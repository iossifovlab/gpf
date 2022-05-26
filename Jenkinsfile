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
  }
  post {
    always {
      script {
        try {
          junit 'test-results/wdae-junit.xml, test-results/dae-junit.xml'

          cobertura coberturaReportFile: 'test-results/coverage.xml',
            enableNewApi: false, onlyStable: false, sourceEncoding: 'ASCII'

          recordIssues(
            enabledForFailure: true, aggregatingResults: false,
            tools: [
              flake8(pattern: 'test-results/flake8_report', reportEncoding: 'UTF-8'),
              myPy(pattern: 'test-results/mypy_dae_report', reportEncoding: 'UTF-8', id: 'mypy-dae', name: 'MyPy - dae'),
              myPy(pattern: 'test-results/mypy_wdae_report', reportEncoding: 'UTF-8', id: 'mypy-wdae', name: 'MyPy - wdae'),
              pyLint(pattern: 'test-results/pylint_gpf_report', reportEncoding: 'UTF-8')
            ],
            qualityGates: [[threshold: 1, type: 'NEW']]

          )

          publishHTML (target : [allowMissing: true,
            alwaysLinkToLastBuild: true,
            keepAll: true,
            reportDir: 'test-results/coverage-html',
            reportFiles: 'index.html',
            reportName: 'gpf-coverage-report',
            reportTitles: 'gpf-coverage-report'])

          // publishHTML (target : [allowMissing: false,
          //   alwaysLinkToLastBuild: true,
          //   keepAll: true,
          //   reportDir: 'test-results/mypy_dae_html_report',
          //   reportFiles: 'index.html',
          //   reportName: 'dae-mypy-report',
          //   reportTitles: 'dae-mypy-report'])

          // publishHTML (target : [allowMissing: false,
          //   alwaysLinkToLastBuild: true,
          //   keepAll: true,
          //   reportDir: 'test-results/mypy_wdae_html_report',
          //   reportFiles: 'index.html',
          //   reportName: 'wdae-mypy-report',
          //   reportTitles: 'wdae-mypy-report'])

          publishHTML (target : [allowMissing: true,
            alwaysLinkToLastBuild: true,
            keepAll: true,
            reportDir: 'test-results/',
            reportFiles: 'bandit_*dae_report.html',
            reportName: 'bandit-dae-report',
            reportTitles: 'bandit-dae-report'])

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
        LinkedHashSet < String > authors = []
        currentBuild.changeSets.items.each {
          itemSet ->
            itemSet.each {
              changeSet ->
                if (changeSet instanceof hudson.plugins.git.GitChangeSet) {
                  authors.add(changeSet.author.displayName)
                }
            }
        }
        zulipSend(
          stream: "hristo-jenkins-test-stream",
          topic: "${env.JOB_NAME}",
          message: "@**${authors.last()}** \n" + "**Project: **[${env.JOB_BASE_NAME}](${env.JOB_URL}) : **Build: **[#${env.BUILD_NUMBER}](${env.BUILD_URL}): **${currentBuild.result}** :${currentBuild.result == 'UNSTABLE' ? 'warning' : 'cross_mark'}:"
        )
      }
    }
    failure {
      script {
        LinkedHashSet < String > authors = []
        currentBuild.changeSets.items.each {
          itemSet ->
            itemSet.each {
              changeSet ->
                if (changeSet instanceof hudson.plugins.git.GitChangeSet) {
                  authors.add(changeSet.author.displayName)
                }
            }
        }
        zulipSend(
          stream: "hristo-jenkins-test-stream",
          topic: "${env.JOB_NAME}",
          message: "@**${authors.last()}** \n" + "**Project: **[${env.JOB_BASE_NAME}](${env.JOB_URL}) : **Build: **[#${env.BUILD_NUMBER}](${env.BUILD_URL}): **${currentBuild.result}** :${currentBuild.result == 'UNSTABLE' ? 'warning' : 'cross_mark'}:"
        )
      }
    }
  }
}
