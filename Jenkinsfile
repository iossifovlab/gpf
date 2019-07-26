pipeline {
  agent any
  stages {

    stage('Data') {
      steps {
        sh '''
            ./jenkins_data.sh
        '''
      }
    }

    stage('Setup') {
      steps {
        sh """
            ./jenkins_build_container.sh
        """
      }
    }

    stage('Prepare') {
      steps {
        sh '''
          export PATH=$HOME/anaconda3/envs/gpf3/bin:$PATH

          docker-compose -f docker-compose.yml up -d

        '''
      }
    }

    stage('Lint') {
      steps {
        sh '''
          export PATH=$HOME/anaconda3/envs/gpf3/bin:$PATH

          docker-compose -f docker-compose.yml exec -T tests /code/scripts/wait-for-it.sh impala:21050 --timeout=240
          docker-compose -f docker-compose.yml exec -T tests flake8 --format=pylint --exclude "--exclude "*old*,*tmp*,*temp*,data-hg19*,gpf*"" /code > ./pyflakes.report || echo "pylint exited with $?"
        '''
      }
    }

    stage('Test') {
      steps {
        sh """
          export PATH=$HOME/anaconda3/envs/gpf3/bin:$PATH

          docker-compose -f docker-compose.yml exec -T tests /code/scripts/wait-for-it.sh impala:21050 --timeout=240
          docker-compose -f docker-compose.yml exec -T tests /code/jenkins_test.sh

          docker-compose -f docker-compose.yml down

        """
      }
    }
  }
  post {
    always {
      junit 'coverage/wdae-junit.xml, coverage/dae-junit.xml'
      step([$class: 'CoberturaPublisher',
           coberturaReportFile: 'coverage/coverage.xml'])
      warnings(
        parserConfigurations: [[parserName: 'PyLint', pattern: 'pyflakes.report']],
        excludePattern: '.*site-packages.*',
        usePreviousBuildAsReference: true,
      )
    }
    success {
      slackSend (
        color: '#00FF00',
        message: "SUCCESSFUL: Job '${env.JOB_NAME} " +
                 "[${env.BUILD_NUMBER}]' ${env.BUILD_URL} (${params.PythonVersion})"
      )
    }
    failure {
      slackSend (
        color: '#FF0000',
        message: "FAILED: Job '${env.JOB_NAME} " +
                 "[${env.BUILD_NUMBER}]' ${env.BUILD_URL} (${params.PythonVersion})"
      )
    }
  }
}
