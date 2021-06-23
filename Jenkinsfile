pipeline {
    agent {
        label 'dory || piglet || pooh'
    }
    options { 
        copyArtifactPermission('/iossifovlab/gpf/*,/iossifovlab/gpfjs/*,/iossifovlab/gpf/master,/seqpipe/gpf_documentation/*');
    }
    triggers {
        pollSCM('* * * * *')
        cron('H * * * *')
    }
    environment {
        BUILD_SCRIPTS_BUILD_DOCKER_REGISTRY_USERNAME = credentials('jenkins-registry.seqpipe.org.user')
        BUILD_SCRIPTS_BUILD_DOCKER_REGISTRY_PASSWORD_FILE = credentials('jenkins-registry.seqpipe.org.passwd')
    }
    stages {
        stage ('Start') {
            steps {
                zulipSend(
                    message: "Started build #${env.BUILD_NUMBER} of project ${env.JOB_NAME} (${env.BUILD_URL})",
                    topic: "${env.JOB_NAME}")
            }
        }

        stage('Copy artifacts') {
            steps {
                copyArtifacts( filter: 'build-env/seqpipe-containers.build-env.sh', fingerprintArtifacts: true, projectName: 'seqpipe/seqpipe-containers/build-scripts')
                copyArtifacts( filter: 'build-env/data-hg19-startup.build-env.sh', fingerprintArtifacts: true, projectName: 'seqpipe/data-hg19-startup/build-scripts')
            }
        }

        stage('Generate stages') {
            steps {
                sh './build.sh Jenkinsfile.generated-stages'
                script {
                    load('Jenkinsfile.generated-stages')
                }
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: 'build-env/gpf.build-env.sh', fingerprint: true

            junit 'test-results/wdae-junit.xml, test-results/dae-junit.xml'

            zulipNotification(
                topic: "${env.JOB_NAME}"
            )      
        }
    }
}
