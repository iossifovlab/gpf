pipeline {
  agent {
    label 'dory'
  }
  options { 
    disableConcurrentBuilds()
  }
  triggers {
    cron('@weekly')
    upstream(upstreamProjects: 'iossifovlab/gpf/master', threshold: hudson.model.Result.SUCCESS)
  }
  environment {
    DOCUMENTATION_DOCKER_IMAGE="seqpipe/gpf-documentation:${env.BRANCH_NAME}"
    GPF_DOCKER_IMAGE="iossifovlab/gpf-base:documentation_${env.BRANCH_NAME}"

    WD="${env.WORKSPACE}"
    SOURCE_DIR="${env.WORKSPACE}/userdocs/gpf"
    DAE_DB_DIR="${env.WORKSPACE}/data-hg19-startup"
    DAE_GENOMIC_SCORES_HG19="/data01/lubo/data/seq-pipeline/genomic-scores-hg19"
    DAE_GENOMIC_SCORES_HG38="/data01/lubo/data/seq-pipeline/genomic-scores-hg19"


    DOCKER_PARAMETERS="""
      -v ${WD}:/documentation \
      -v ${DAE_DB_DIR}:/data \
      -v ${SOURCE_DIR}:/documentation/userdocs/gpf \
      -v ${DAE_GENOMIC_SCORES_HG19}:/genomic-scores-hg19 \
      -v ${DAE_GENOMIC_SCORES_HG38}:/genomic-scores-hg38
    """
  }
  stages {
    stage ('Start') {
      steps {
        slackSend (
          color: '#FFFF00',
          message: "STARTED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})"
        )
      }
    }

    stage('Source') {
      steps {
        checkout([
          $class: 'GitSCM', 
          branches: [[name: '*/master']],
          doGenerateSubmoduleConfigurations: false,
          extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'userdocs/gpf']],
          submoduleCfg: [], 
          userRemoteConfigs: [[
            credentialsId: 'dea7a214-d183-4735-a7d5-ed8076dd0e0d', 
            url: 'git@github.com:iossifovlab/gpf.git'
          ]]
        ])
      }
    }

    stage('Data') {
        steps {
            sh '''
                rm -f builds/*
            '''
            script {
                copyArtifacts(
                    projectName: 'seqpipe/data-hg19-startup/master',
                    selector: lastSuccessful()
                );
            }
            sh '''
                tar zxf builds/data-hg19-startup-*.tar.gz -C $WD
                
                mkdir -p $WD/data-hg19-startup/wdae

                sed -i "s/localhost/impala/" $WD/data-hg19-startup/DAE.conf
            '''
        }
    }

    stage('Docker Setup') {
      steps {
        script {
          sh '''
            make gpf_image
            make documentation_image
          '''
          // docker.build(
          //   "${GPF_DOCKER_IMAGE}",
          //   ". -f ${SOURCE_DIR}/Dockerfile --build-arg SOURCE_DIR=./\$(basename ${SOURCE_DIR})"
          // )
          // docker.build(
          //   "${DOCUMENTATION_DOCKER_IMAGE}",
          //   ". -f ${WD}/Dockerfile --build-arg GPF_DOCKER_IMAGE=${GPF_DOCKER_IMAGE}"
          // )
        }
      }
    }

    stage('Build') {
      steps {
        sh '''
          docker run --rm ${DOCKER_PARAMETERS} ${DOCUMENTATION_DOCKER_IMAGE} /documentation/scripts/jenkins_build.sh
        '''
      }
    }

    // stage('Test') {
    //   steps {
    //     sh '''
    //       docker run --rm ${DOCKER_PARAMETERS} ${DOCUMENTATION_DOCKER_IMAGE} /documentation/scripts/jenkins_test.sh
    //     '''
    //   }
    // }

    stage('Publish') {
      steps {
        timeout(time: 5, unit: 'MINUTES') {
          sh '''
            echo $HOME
            echo $WORKSPACE
            pwd
            hostname
            ansible-playbook -i doc_inventory doc_publish.yml
          '''
        }
      }
    }

  }
  post {
    // always {
    //   junit 'coverage/doc-junit.xml'
    // }
    success {
      slackSend (
        color: '#00FF00',
        message: "SUCCESSFUL: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})"
      )

      archive 'gpf-html.tar.gz'
      fingerprint 'gpf-html.tar.gz'
      archive 'gpf-wdae-html.tar.gz'
      fingerprint 'gpf-wdae-html.tar.gz'
      archive 'gpf-user-html.tar.gz'
      fingerprint 'gpf-user-html.tar.gz'

    }
    failure {
      slackSend (
        color: '#FF0000',
        message: "FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})"
      )
    }
  }
}
