pipeline {
  agent {
    label 'dory'
  }
  environment {
    WD = pwd()
    DAE_SOURCE_DIR = "$WD/gpf/DAE"
    DAE_DB_DIR="$HOME/data/data-work/"
    
    PATH = "$DAE_SOURCE_DIR/tools:$DAE_SOURCE_DIR/tests:$DAE_SOURCE_DIR/pheno/prepare:$HOME/anaconda2/bin:$PATH"
    PYTHONPATH = "$DAE_SOURCE_DIR:$DAE_SOURCE_DIR/tools:$PYTHONPATH"
  }
  options { 
    disableConcurrentBuilds() 
  }
  triggers {
    cron('@weekly')
  }
  stages {
    stage ('Start') {
      steps {
        echo "PATH is: $PATH"
        echo "WD is: $WD"
        
        slackSend (
          color: '#FFFF00',
          message: "STARTED: Job '${env.JOB_NAME} " +
            "[${env.BUILD_NUMBER}]' (${env.BUILD_URL})"
        )
      }
    }
    stage('Prepare') {
      steps {
        echo "PATH is: $PATH"
        echo "WD is: $WD"
      }
    }
    stage('Build') {
        steps {
            checkout([
                $class: 'GitSCM', 
                branches: [[name: '*/master']], 
                doGenerateSubmoduleConfigurations: false, 
                extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'gpf']], 
                submoduleCfg: [], 
                userRemoteConfigs: [[
                    credentialsId: 'dea7a214-d183-4735-a7d5-ed8076dd0e0d', 
                    url: 'git@github.com:seqpipe/gpf.git'
                ]]
            ])
            sh '''
              echo $HOME
              echo $WORKSPACE
              pwd

              ./doc_build.sh
            '''
            
            sh '''

            '''
        }
    }

  }
  post {
    success {
        slackSend (
          color: '#00FF00',
          message: "SUCCESSFUL: Job '${env.JOB_NAME} " +
                   "[${env.BUILD_NUMBER}]' (${env.BUILD_URL})"
        )
        fingerprint 'gpf-html.tar.gz'
        archive 'gpf-html.tar.gz'
    }
    failure {
      slackSend (
        color: '#FF0000',
        message: "FAILED: Job '${env.JOB_NAME} " +
                 "[${env.BUILD_NUMBER}]' (${env.BUILD_URL})"
      )
    }
  }
}
