pipeline {
    agent {
        label 'dory'
    }
    options { 
        disableConcurrentBuilds()
    }
    triggers {
        pollSCM('* * * * *')
        cron('H 2 * * *')
    }
    parameters {
        string(
            name: 'DATA_HG19_BUILD', defaultValue: '0', 
            description: 'data-hg19-startup build number to use for testing')
    }    

    environment {
        WD="${env.WORKSPACE}"

        DOCKER_IMAGE="iossifovlab/gpf-base:${env.BRANCH_NAME}"

        SOURCE_DIR="${env.WORKSPACE}"
        DAE_DB_DIR="${env.WORKSPACE}/data-hg19-startup"
        DAE_GENOMIC_SCORES_HG19="/data01/lubo/data/seq-pipeline/genomic-scores-hg19"
        DAE_GENOMIC_SCORES_HG38="/data01/lubo/data/seq-pipeline/genomic-scores-hg19"

        DOCKER_SOURCE_DIR="/code"
        DOCKER_DAE_DB_DIR="/data"
        DOCKER_DAE_GENOMIC_SCORES_HG19="/genomic-scores-hg19"
        DOCKER_DAE_GENOMIC_SCORES_HG38="/genomic-scores-hg38"
    }
    stages {
        stage ('Start') {
            steps {
                slackSend (
                color: '#FFFF00',
                message: "STARTED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' ${env.BUILD_URL}"
                )
            }
        }

        stage('Data') {
            steps {
                sh '''
                    rm -f builds/*
                '''
                script {
                    println "DATA_HG19_BUILD=" + DATA_HG19_BUILD
                    if (DATA_HG19_BUILD == '0') {
                        copyArtifacts(
                            projectName: 'seqpipe/build-data-hg19-startup/master',
                            selector: lastSuccessful()
                        );
                    } else {
                        copyArtifacts(
                            projectName: 'seqpipe/build-data-hg19-startup/master',
                            selector: specific(DATA_HG19_BUILD));
                    }
                }
                sh '''
                    tar zxf builds/data-hg19-startup-*.tar.gz -C $WD
                '''
            }
        }

        stage('Setup') {
            steps {
                script {
                    docker.build(
                        "${DOCKER_IMAGE}", ". -f ${SOURCE_DIR}/Dockerfile")
                }
                sh '''
                    export PATH=$HOME/anaconda3/envs/gpf3/bin:$PATH

                    docker-compose -f docker-compose.yml up -d
                '''
            }
        }

        stage('Git Clean') {
          steps {
            sh '''
                docker-compose -f docker-compose.yml exec -T tests cd /code && \
                    git clean -xdf \
                        -e data-hg19-startup*.tar.gz \
                        -e data-hg19-startup || true
            '''
          }
        }

        stage('Lint') {
            steps {
                sh '''
                export PATH=$HOME/anaconda3/envs/gpf3/bin:$PATH

                docker-compose -f docker-compose.yml exec -T tests /code/jenkins_flake8.sh
                '''
            }
        }

        stage('Test') {
            steps {
                sh """
                export PATH=$HOME/anaconda3/envs/gpf3/bin:$PATH

                docker-compose -f docker-compose.yml exec -T tests /code/scripts/wait-for-it.sh impala:21050 --timeout=240
                docker-compose -f docker-compose.yml exec -T tests /code/jenkins_test.sh
                """
            }
        }
    }
    post {
        always {
            junit 'coverage/wdae-junit.xml, coverage/dae-junit.xml'
            step([
                $class: 'CoberturaPublisher', 
                coberturaReportFile: 'coverage/coverage.xml'])
            warnings(
                parserConfigurations: [[parserName: 'PyLint', pattern: 'pyflakes.report']],
                excludePattern: '.*site-packages.*',
                usePreviousBuildAsReference: true,
            )
            sh '''
                export PATH=$HOME/anaconda3/envs/gpf3/bin:$PATH

                ./jenkins_clean.sh
            '''

        }
        success {
            slackSend (
                color: '#00FF00',
                message: "SUCCESSFUL: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' ${env.BUILD_URL}"
            )
        }
        failure {
            slackSend (
                color: '#FF0000',
                message: "FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' ${env.BUILD_URL}"
            )
        }
    }
}
