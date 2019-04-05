from conans import ConanFile, Meson, tools

import os

class GStreamerPluginsGoodConan(ConanFile):
    name = "gstreamer-plugins-good"
    version = "1.15.1"
    default_user = "bincrafters"
    default_channel = "stable"
    url = "https://github.com/bincrafters/conan-" + name
    description = "Plug-ins is a set of plugins that we consider to have good quality code and correct functionality"
    license = "https://gitlab.freedesktop.org/gstreamer/gstreamer/raw/master/COPYING"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "autodetect": [True, False],
        "rtp": [True, False],
        "udp": [True, False],
        "png": [True, False],
        "isomp4": [True, False],
        "videofilter": [True, False],
        "multifile": [True, False],
    }
    default_options = (
        "autodetect=True",
        "rtp=True",
        "udp=True",
        "png=True",
        "isomp4=True",
        "videofilter=True",
        "multifile=True",
    )
    folder_name = "gst-plugins-good-" + version

    def requirements(self):
        self.requires("glib/2.58.1@%s/%s" % (self.user, self.channel))
        self.requires("gstreamer/%s@%s/%s" % (self.version, self.user, self.channel))
        self.requires("gstreamer-plugins-base/%s@%s/%s" % (self.version, self.user, self.channel))

    def source(self):
        tools.get("https://github.com/GStreamer/gst-plugins-good/archive/%s.tar.gz" % self.version)

    def build(self):
        args = ["--auto-features=disabled"]
        args.append("-Dautodetect=" + ("enabled" if self.options.autodetect else "disabled"))
        args.append("-Drtp=" + ("enabled" if self.options.rtp else "disabled"))
        args.append("-Drtpmanager=" + ("enabled" if self.options.rtp else "disabled"))
        args.append("-Dudp=" + ("enabled" if self.options.udp else "disabled"))
        args.append("-Dpng=" + ("enabled" if self.options.png else "disabled"))
        args.append("-Disomp4=" + ("enabled" if self.options.isomp4 else "disabled"))
        args.append("-Dvideofilter=" + ("enabled" if self.options.videofilter else "disabled"))
        args.append("-Dmultifile=" + ("enabled" if self.options.videofilter else "disabled"))
        meson = Meson(self)
        meson.configure(source_folder=self.folder_name, args=args, pkg_config_paths=os.environ["PKG_CONFIG_PATH"].split(":"))
        meson.build()
        meson.install()

    def package(self):
        if self.channel == "testing":
            self.copy("*.c", "src")
            self.copy("*.h", "src")

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        self.cpp_info.srcdirs.append("src")
        self.env_info.GST_PLUGIN_PATH.append(os.path.join(self.package_folder, "lib", "gstreamer-1.0"))
        self.env_info.PKG_CONFIG_PATH.append(os.path.join(self.package_folder, "lib", "pkgconfig"))
        self.env_info.SOURCE_PATH.append(os.path.join(self.package_folder, "src"))
