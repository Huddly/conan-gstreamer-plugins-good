#!groovy
@Library('huddlygo_shared_libraries@master') _

Map stage_node_info = [:]
String slack_channel = BRANCH_NAME == "master" ? "#builds-falcon" : ""
String cron_string = BRANCH_NAME == "master" ? "H H 1 * *" : "" // Run once a month (1st day of the month)

pipeline {
  agent { docker huddlydocker([configKey: "falcon_build"]) }
  environment {
    CONAN_USER_HOME = "${env.WORKSPACE}"
    LOCAL_REMOTE='conan-ext_deps-local'
    VIRTUAL_REMOTE='conan'
    SRC='.'
    MODULE='gst-plugins-good'
    USER= 'huddly'
    CHAN_LATEST='latest'
    CHAN_STABLE='stable'
    CONAN_PROFILE='aarch64-buildroot-musl-gcc9'
    CONAN_PROFILE_X86='x86_64-linux-gcc-7'
    ARTIFACTORY_ACCESS_TOKEN=credentials('artifactory-access-token')
    ARTIFACTORY_USER="jenkins"
  }
  triggers { cron(cron_string) }
  stages {
    stage('setup') {
      steps {
        echo "Running on $NODE_NAME"
        conan_config()
      }
      post {
        always {
          script { stage_node_info["$STAGE_NAME"] = "$NODE_NAME"}
        }
      }
    }
    stage ('build') {
      steps {
        echo "Running on $NODE_NAME"
        script {
          def REF = "$MODULE/$VERSION@$USER/$CHAN_LATEST"
          conan.export path: "$SRC", reference: "$REF"

          // Build for aarch64-buildroot-musl-gcc9
          sh script: """
          conan install $REF \
          -r $VIRTUAL_REMOTE \
          -pr:b x86_64-linux-gcc-7 -pr:h aarch64-buildroot-musl-gcc9 \
          --build $MODULE""", label: "Build $MODULE for profile aarch64-buildroot-musl-gcc9"

          // Build for x86_64-linux-gcc-7
          conan.install([
            reference: "$REF",
            profile: "$CONAN_PROFILE_X86",
            remote: "$VIRTUAL_REMOTE",
            extraArgs: "--build $MODULE",
            cmdLabel: "Build $MODULE for profile x86_64-linux-gcc-7"
          ])
        }
      }
      post {
        always {
          script { stage_node_info["$STAGE_NAME"] = "$NODE_NAME"}
        }
      }
    }

    stage ('upload') {
      when {
        anyOf {
          branch 'master'
          buildingTag()
        }
      }
      parallel {
        stage ("Latest release") {
          when { branch 'master' }
          steps {
            script {
              conan.upload reference: "$MODULE/$VERSION@$USER/$CHAN_LATEST", remote: "$LOCAL_REMOTE", extraArgs: "--all"
            }
          }
          post {
            always {
              script { stage_node_info["$STAGE_NAME"] = "$NODE_NAME"}
            }
          }
        }
        stage ("Stable release") {
          when { buildingTag() }
          steps {
            echo "Running on $NODE_NAME"
            script {
              conan.copy reference: "$MODULE/$VERSION@$USER/$CHAN_LATEST", userChannel: "$USER/$CHAN_STABLE", extraArgs: "--all"
              conan.upload reference: "$MODULE/$VERSION@$USER/$CHAN_STABLE", remote: "$LOCAL_REMOTE", extraArgs: "--all"
            }
          }
          post {
            always {
              script { stage_node_info["$STAGE_NAME"] = "$NODE_NAME"}
            }
          }
        }
      }
    }
  }
  post {
    failure {
      send_slack_Failure(BRANCH_NAME, slack_channel, stage_node_info)
      setBuildDescription(stage_node_info)
    }
    aborted {
      setBuildDescription(stage_node_info)
    }
  }
}

def conan_config() {
  script {
    sh script: 'git clean -x -f', label: 'Cleanup old generated files'
    falcon_pylib.install_libraries()
    conan.configure user: "$ARTIFACTORY_USER", password: "$ARTIFACTORY_ACCESS_TOKEN"
    VERSION = conan.inspect path: "$SRC", attribute: "version"
    print("VERSION: $VERSION")
  }
}
