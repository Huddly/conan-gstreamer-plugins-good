from conans import ConanFile, Meson, tools
import glob
import shutil
import os

class GStreamerPluginsGoodConan(ConanFile):
    name = "gst-plugins-good"
    version = "1.16.1"
    default_user = "bincrafters"
    generators = "pkg_config"
    default_channel = "stable"
    url = "https://github.com/bincrafters/conan-" + name
    description = "Plug-ins is a set of plugins that we consider to have good quality code and correct functionality"
    license = "https://gitlab.freedesktop.org/gstreamer/gstreamer/raw/master/COPYING"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared":[True,False],
        "autodetect": [True, False],
        "rtp": [True, False],
        "udp": [True, False],
        "png": [True, False],
        "isomp4": [True, False],
        "videofilter": [True, False],
        "multifile": [True, False],
        "with_libalsa": [True, False],
        "with_selinux": [True, False],
        "with_elf": [True, False]
    }
    default_options = (
        "shared=True",
        "autodetect=True",
        "rtp=True",
        "udp=True",
        "png=True",
        "isomp4=True",
        "videofilter=True",
        "multifile=True",
        "with_libalsa=False",
        "with_selinux=False",
        "with_elf=False"
    )
    folder_name = "gst-plugins-good-" + version

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    @property
    def _is_msvc(self):
        return self.settings.compiler == "Visual Studio"

    def requirements(self):
        self.requires("glib/2.64.0@bincrafters/stable")
        self.requires("gstreamer/[>=1.16.0]@bincrafters/stable")
        self.requires("gst-plugins-base/[>=1.16.0]@bincrafters/stable")

    def build_requirements(self):
        self.build_requires("meson/0.54.2")
        if not tools.which("pkg-config"):
            self.build_requires("pkg-config_installer/0.29.2@bincrafters/stable")
        self.build_requires("bison/3.5.3")
        self.build_requires("flex/2.6.4")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
    #    tools.get("https://github.com/GStreamer/gst-plugins-good/archive/%s.tar.gz" % self.version)
        #gst-plugins-base-1.16.1
        os.rename("%s-%s" % (self.name, self.version), self._source_subfolder)

    def _copy_pkg_config(self, name):
        root = self.deps_cpp_info[name].rootpath
        pc_dir = os.path.join(root, 'lib', 'pkgconfig')
        pc_files = glob.glob('%s/*.pc' % pc_dir)
        if not pc_files:  # zlib store .pc in root
            pc_files = glob.glob('%s/*.pc' % root)
        for pc_name in pc_files:
            new_pc = os.path.basename(pc_name)
            self.output.warn('copy .pc file %s' % os.path.basename(pc_name))
            shutil.copy(pc_name, new_pc)
            prefix = tools.unix_path(root) if self.settings.os == 'Windows' else root
            tools.replace_prefix_in_pc_file(new_pc, prefix)

    def configure(self):
        self.options['gst-plugins-base'].with_libalsa = self.options.with_libalsa
        self.options['glib'].with_selinux = self.options.with_selinux
        self.options['glib'].with_elf = self.options.with_elf
        print(100*'-')
        print(f"with_libalsa = {self.options.with_libalsa}\nwith_selinux = {self.options.with_selinux}\nwith_elf = {self.options.with_elf}")
        print(100*'-')


    def _configure_meson(self):
        defs = dict()

        def add_flag(name, value):
            if name in defs:
                defs[name] += " " + value
            else:
                defs[name] = value

        def add_compiler_flag(value):
            add_flag("c_args", value)
            add_flag("cpp_args", value)

        def add_linker_flag(value):
            add_flag("c_link_args", value)
            add_flag("cpp_link_args", value)

        meson = Meson(self)
        if self.settings.compiler == "Visual Studio":
            add_linker_flag("-lws2_32")
            add_compiler_flag("-%s" % self.settings.compiler.runtime)
            if int(str(self.settings.compiler.version)) < 14:
                add_compiler_flag("-Dsnprintf=_snprintf")
        if self.settings.get_safe("compiler.runtime"):
            defs["b_vscrt"] = str(self.settings.compiler.runtime).lower()
        defs["tools"] = "disabled"
        defs["examples"] = "disabled"
        defs["benchmarks"] = "disabled"
        defs["tests"] = "disabled"
        meson.configure(build_folder=self._build_subfolder,
                        source_folder=self._source_subfolder,
                        defs=defs)
        return meson

    def _fix_library_names(self, path):
        # regression in 1.16
        if self.settings.compiler == "Visual Studio":
            with tools.chdir(path):
                for filename_old in glob.glob("*.a"):
                    filename_new = filename_old[3:-2] + ".lib"
                    self.output.info("rename %s into %s" % (filename_old, filename_new))
                    shutil.move(filename_old, filename_new)

    def build(self):
        args = ["--auto-features=disabled"]
        args.append("-Dautodetect=" + ("enabled" if self.options.autodetect else "disabled"))
        args.append("-Drtp=" + ("enabled" if self.options.rtp else "disabled"))
        args.append("-Drtpmanager=" + ("enabled" if self.options.rtp else "disabled"))
        args.append("-Dudp=" + ("enabled" if self.options.udp else "disabled"))
        args.append("-Dpng=" + ("enabled" if self.options.png else "disabled"))
        args.append("-Disomp4=" + ("enabled" if self.options.isomp4 else "disabled"))
        args.append("-Dvideofilter=" + ("enabled" if self.options.videofilter else "disabled"))
        args.append("-Dmultifile=" + ("enabled" if self.options.multifile else "disabled"))
       # meson = Meson(self)
        #¤meson.configure(source_folder=self.folder_name, args=args, pkg_config_paths=os.environ["PKG_CONFIG_PATH"].split(":"))
        #for p in self.conan_data["patches"][self.version]:
        #    tools.patch(**p)
        self._copy_pkg_config("glib")
        self._copy_pkg_config("gstreamer")
        self._copy_pkg_config("gst-plugins-base")
        with tools.environment_append(VisualStudioBuildEnvironment(self).vars) if self._is_msvc else tools.no_op():
            meson = self._configure_meson()
            meson.build()
    #    meson.configure(source_folder=self.folder_name, args=args)
        #meson.build()
        #meson.install()

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        with tools.environment_append(VisualStudioBuildEnvironment(self).vars) if self._is_msvc else tools.no_op():
            meson = self._configure_meson()
            meson.install()

        self._fix_library_names(os.path.join(self.package_folder, "lib"))
        self._fix_library_names(os.path.join(self.package_folder, "lib", "gstreamer-1.0"))
#        if self.channel == "testing":
 #           self.copy("*.c", "src")
  #          self.copy("*.h", "src")

    def package_info(self):
        gst_plugin_path = os.path.join(self.package_folder, "lib", "gstreamer-1.0")
        if self.options.shared:
            self.output.info("Appending GST_PLUGIN_PATH env var : %s" % gst_plugin_path)
            self.env_info.GST_PLUGIN_PATH.append(gst_plugin_path)
        else:
            self.cpp_info.defines.append("GST_PLUGINS_BASE_STATIC")
            self.cpp_info.libdirs.append(gst_plugin_path)
            #self.cpp_info.libs = tools.collect_libs(self)
            self.cpp_info.libs.extend(["libgstalaw",
        "libgstcutter",
        "libgstgoom",
        "libgstmonoscope",
        "libgstrtpmanager",
        "libgstvideofilter",
        "libgstalphacolor",
        "libgstdebug",
        "libgsticydemux",
        "libgstmulaw",
        "libgstrtp",
        "libgstvideomixer",
        "libgstalpha",
        "libgstdeinterlace",
        "libgstid3demux",
        "libgstmultifile",
        "libgstrtsp",
        "libgstwavenc",
        "libgstapetag",
        "libgstdtmf",
        "libgstimagefreeze",
        "libgstmultipart",
        "libgstshapewipe",
        "libgstwavparse",
        "libgstaudiofx",
        "libgsteffectv",
        "libgstinterleave",
        "libgstnavigationtest",
        "libgstsmpte",
        "libgstximagesrc",
        "libgstaudioparsers",
        "libgstequalizer",
        "libgst",
        "mp4",
        "libgstoss4",
        "libgstspectrum",
        "libgsty4menc",
        "libgstauparse",
        "libgstflv",
        "libgstjpeg",
        "libgstossaudio",
        "libgstudp",
        "libgstautodetect",
        "libgstflxdec",
        "libgstlame",
        "libgstpng",
        "libgstvideo4linux2",
        "libgstavi",
        "libgstgdkpixbuf",
        "libgstlevel",
        "libgstpulseaudio",
        "libgstvideobox",
        "libgstcairo",
        "libgstgoom2k1",
        "libgstmatroska",
        "libgstreplaygain",
        "libgstvideocrop",
        ])


        #self.cpp_info.srcdirs.append("src")
        #self.env_info.GST_PLUGIN_PATH.append(os.path.join(self.package_folder, "lib", "gstreamer-1.0"))
        #self.env_info.PKG_CONFIG_PATH.append(os.path.join(self.package_folder, "lib", "pkgconfig"))
        #self.env_info.SOURCE_PATH.append(os.path.join(self.package_folder, "src"))
