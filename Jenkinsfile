pipeline {
  agent { label 'pooh' }
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
  }
  post {
    always {
      script {
        try {
          discoverGitReferenceBuild(latestBuildIfNotFound: true, maxCommits: 400, skipUnknownCommits: true)

          def resultBeforeTests = currentBuild.currentResult
          junit 'test-results/wdae-junit.xml, test-results/dae-junit.xml, test-results/dae-tests-junit.xml, test-results/wdae-tests-junit.xml'
          sh "test ${resultBeforeTests} == ${currentBuild.currentResult}"

          recordCoverage sourceCodeEncoding: 'UTF-8', enabledForFailure: true, sourceCodeRetention: 'LAST_BUILD', tools: [
            [parser: 'COBERTURA', pattern: 'test-results/coverage.xml']
          ]

          recordIssues(
            enabledForFailure: true, aggregatingResults: false,
            tools: [
                flake8(pattern: 'test-results/ruff_report', reportEncoding: 'UTF-8', id: 'ruff', name: 'Ruff'),
                myPy(pattern: 'test-results/mypy_dae_report', reportEncoding: 'UTF-8', id: 'mypy-dae', name: 'MyPy - dae'),
                myPy(pattern: 'test-results/mypy_wdae_report', reportEncoding: 'UTF-8', id: 'mypy-wdae', name: 'MyPy - wdae'),

                pyLint(pattern: 'test-results/mypy_dae_pylint_report', reportEncoding: 'UTF-8', id: 'mypy-dae-pylint', name: 'MyPy - dae (converted to PyLint)'),
                pyLint(pattern: 'test-results/mypy_wdae_pylint_report', reportEncoding: 'UTF-8', id: 'mypy-wdae-pylint', name: 'MyPy - wdae (converted to PyLint)'),

                pyLint(pattern: 'test-results/pylint_report', id: 'pylint-id', reportEncoding: 'UTF-8')
            ],
            qualityGates: [[threshold: 1, type: 'DELTA', unstable: true]]
          )

          publishHTML (target : [allowMissing: true,
            alwaysLinkToLastBuild: true,
            keepAll: true,
            reportDir: 'test-results/coverage-html',
            reportFiles: 'index.html',
            reportName: 'gpf-coverage-report',
            reportTitles: 'gpf-coverage-report'])

          publishHTML (target : [allowMissing: true,
            alwaysLinkToLastBuild: true,
            keepAll: true,
            reportDir: 'test-results/',
            reportFiles: 'bandit_wdae_report.html',
            reportName: 'bandit-wdae-report',
            reportTitles: 'bandit-wdae-report'])

        } finally {
          zulipNotification(
            topic: "${env.JOB_NAME}"
          )
        }
      }
    }
    unstable {
        script {
            load('build-scripts/libjenkinsfile/zulip-tagged-notification.groovy').zulipTaggedNotification()
        }
    }
    failure {
      script {
        load('build-scripts/libjenkinsfile/zulip-tagged-notification.groovy').zulipTaggedNotification()
      }
    }
  }
}
