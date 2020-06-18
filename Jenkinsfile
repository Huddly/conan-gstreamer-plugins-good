#!groovy
@Library('huddlygo_shared_libraries@master') _

Map stage_node_info = [:]
String slack_channel = BRANCH_NAME == "master" ? "#builds-falcon" : ""
String cron_string = BRANCH_NAME == "master" ? "H H 1 * *" : "" // Run once a month (1st day of the month)

def PROFILES=['x86_64-linux-gcc-7']
def PACKAGE=[
    'name' : 'gst-plugins-good',
    'channel_latest': 'latest',
    'channel_stable': 'stable',
    'user': 'huddly',
    'version': '',
    'options' : [	
	    'with_libalsa' : 'False'
	    ],
]

def profileMap = PROFILES.collectEntries {
   ["${it}" : generatePackageStages(PACKAGE, "${it}")]
}

def generatePackageStages(pkg, profile)
{
  return {
    def options=""
    if (pkg.options != null)
    {
       pkg.options.each { option ,value ->
          options="${options} -o ${pkg.name}:${option}=${value}"
       }
    }
	 
    stage("build ${pkg.name}") {
      script {
        conan.install([
          reference: "${pkg.name}/$VERSION@${pkg.user}/${pkg.channel_latest}",
          profile: "$profile",
          remote: "$VIRTUAL_REMOTE",
          extraArgs: "--build ${pkg.name} $options",
          cmdLabel: "building ${pkg.name} for profile $profile"
        ])
      }
    }
  }
}

pipeline {
  agent { docker huddlydocker([configKey: "falcon_build"]) }
  environment {
    CONAN_USER_HOME = "${env.WORKSPACE}"
    LOCAL_REMOTE='conan-ext_deps-local'
    VIRTUAL_REMOTE='conan'
    SRC="."
    ARTIFACTORY_ACCESS_TOKEN=credentials('artifactory-access-token')
    ARTIFACTORY_USER="jenkins"
  }
  triggers { cron(cron_string) }
  stages {
    stage ('setup') {
      steps {
        echo "Running on $NODE_NAME"
        script {
          conan.configure user: "$ARTIFACTORY_USER", password: "$ARTIFACTORY_ACCESS_TOKEN"
          VERSION = conan.inspect path: "$SRC", attribute: "version"
          PACKAGE.version = VERSION
        }
        echo "VERSION is ${VERSION}"
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
          conan.export path: "$SRC", reference: "${PACKAGE.name}/$VERSION@$PACKAGE.user/$PACKAGE.channel_latest"
          parallel profileMap
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
            echo "Running on $NODE_NAME"
            script {
              conan.upload reference: "${PACKAGE.name}/${PACKAGE.version}@${PACKAGE.user}/${PACKAGE.channel_latest}", remote: "$LOCAL_REMOTE", extraArgs: "--all"
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
              STABLE_USERCHAN = "${PACKAGE.user}/${PACKAGE.channel_stable}"
              conan.copy reference: "${PACKAGE.name}/$VERSION@${PACKAGE.user}/${PACKAGE.channel_latest}", userChannel: "$STABLE_USERCHAN", extraArgs: "--all"
              conan.upload reference: "${PACKAGE.name}/${PACKAGE.version}@$STABLE_USERCHAN", remote: "$LOCAL_REMOTE", extraArgs: "--all"
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

