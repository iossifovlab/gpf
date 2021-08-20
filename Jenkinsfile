pipeline {
  agent { label 'piglet || pooh || dory' }
  options {
    copyArtifactPermission('/iossifovlab/*,/seqpipe/*');
  }
  environment {
    BUILD_SCRIPTS_BUILD_DOCKER_REGISTRY_USERNAME = credentials('jenkins-registry.seqpipe.org.user')
    BUILD_SCRIPTS_BUILD_DOCKER_REGISTRY_PASSWORD_FILE = credentials('jenkins-registry.seqpipe.org.passwd')
    TRIGGERS='[cron("0 2 * * *")]'
  }

  stages {
    stage('Start') {
      steps {
        zulipSend(
          message: "Started build #${env.BUILD_NUMBER} of project ${env.JOB_NAME} (${env.BUILD_URL})",
          topic: "${env.JOB_NAME}")
      }
    }
    stage('Generate stages') {
      steps {
        sh "./build.sh preset:slow build_no:${env.BUILD_NUMBER} generate_jenkins_init:yes"
        script {
          load('Jenkinsfile.generated-stages')
        }
      }
    }
    stage('SonarQube') {
      steps {
        script {
          def scannerHome = tool 'SonarScanner';
          withSonarQubeEnv() {
            sh "${scannerHome}/bin/sonar-scanner"
          }
        }
      }
    }
  }
  post {
    always {
      junit 'test-results/wdae-junit.xml, test-results/dae-junit.xml'

      cobertura coberturaReportFile: 'test-results/dae-coverage.xml', enableNewApi: true
      cobertura coberturaReportFile: 'test-results/wdae-coverage.xml', enableNewApi: true

      recordIssues(
        enabledForFailure: true, aggregatingResults: false,
        tools: [
          flake8(pattern: 'test-results/flake8_report', reportEncoding: 'UTF-8'),
          myPy(pattern: 'test-results/mypy_dae_report', reportEncoding: 'UTF-8', id: 'mypy-dae', name: 'MyPy - dae'),
          myPy(pattern: 'test-results/mypy_wdae_report', reportEncoding: 'UTF-8', id: 'mypy-wdae', name: 'MyPy - wdae')
        ]
      )

      zulipNotification(
        topic: "${env.JOB_NAME}"
      )
    }
  }
}
