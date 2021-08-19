pipeline {
  agent { label 'piglet || pooh || dory' }
  options {
    copyArtifactPermission('/iossifovlab/*,/seqpipe/*');
  }
  environment {
    BUILD_SCRIPTS_BUILD_DOCKER_REGISTRY_USERNAME = credentials('jenkins-registry.seqpipe.org.user')
    BUILD_SCRIPTS_BUILD_DOCKER_REGISTRY_PASSWORD_FILE = credentials('jenkins-registry.seqpipe.org.passwd')
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
  }
  post {
    always {
      junit 'test-results/wdae-junit.xml, test-results/dae-junit.xml'
      recordIssues(
        enabledForFailure: true, aggregatingResults: false,
        tools: [
          flake8(pattern: 'test-results/flake8_report', reportEncoding: 'UTF-8'),
          junitParser(pattern: 'test-results/dae-junit.xml', reportEncoding: 'UTF-8', id: 'junit-dae', name: 'JUnit - dae'),
          junitParser(pattern: 'test-results/wdae-junit.xml', reportEncoding: 'UTF-8', id: 'junit-wdae', name: 'JUnit - wdae'),
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
