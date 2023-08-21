pipeline {
  agent { label 'piglet' }
  options {
    copyArtifactPermission('/iossifovlab/*,/seqpipe/*');
    disableConcurrentBuilds()
  }
  environment {
    BUILD_SCRIPTS_BUILD_DOCKER_REGISTRY_USERNAME = credentials('jenkins-registry.seqpipe.org.user')
    BUILD_SCRIPTS_BUILD_DOCKER_REGISTRY_PASSWORD_FILE = credentials('jenkins-registry.seqpipe.org.passwd')
    SONARQUBE_DEFAULT_TOKEN=credentials('sonarqube-default')
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
/*
    stage('SonarQube') {
      steps {
        script {
          def scannerHome = tool 'sonarqube-scanner-default';
          withSonarQubeEnv() {
            sh "${scannerHome}/bin/sonar-scanner"
          }
        }
      }
    }
*/
  }
  post {
    always {
      script {
        try {
          resultBeforeTests = currentBuild.currentResult
          junit 'test-results/wdae-junit.xml, test-results/dae-junit.xml'
          sh "test ${resultBeforeTests} == ${currentBuild.currentResult}"

          cobertura coberturaReportFile: 'test-results/coverage.xml', enableNewApi: true, onlyStable: false, sourceEncoding: 'ASCII'

          recordIssues(
            enabledForFailure: true, aggregatingResults: false,
            tools: [
              flake8(pattern: 'test-results/flake8_report', reportEncoding: 'UTF-8'),
              myPy(pattern: 'test-results/mypy_dae_report', reportEncoding: 'UTF-8', id: 'mypy-dae', name: 'MyPy - dae'),
              myPy(pattern: 'test-results/mypy_wdae_report', reportEncoding: 'UTF-8', id: 'mypy-wdae', name: 'MyPy - wdae')
            ]
          )

          publishHTML (target : [allowMissing: false,
            alwaysLinkToLastBuild: true,
            keepAll: true,
            reportDir: 'test-results/coverage-html',
            reportFiles: 'index.html',
            reportName: 'GPF Coverage Report',
            reportTitles: 'GPF Coverage Report'])
          
        } finally {
          zulipNotification(
            topic: "${env.JOB_NAME}"
          )
        }
      }
    }
  }
}
