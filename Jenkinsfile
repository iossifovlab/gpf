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

        DOCKER_IMAGE="iossifovlab/gpf-base_${env.BRANCH_NAME}:${env.BUILD_NUMBER}"
        DOCKER_NETWORK="gpf_base_${env.BRANCH_NAME}_${env.BUILD_NUMBER}"

        DOCKER_CONTAINER_IMPALA="gpf_impala_${env.BRANCH_NAME}_${env.BUILD_NUMBER}"

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

        stage('Clean up') {
            steps {
                sh '''
                    docker run -d --rm \
                        -v ${SOURCE_DIR}:/code \
                        busybox:latest \
                        /bin/sh -c "rm -rf /code/wdae-*.log && rm -rf /code/wdae_django*.cache"
                    docker run -d --rm \
                        -v ${SOURCE_DIR}:/code \
                        busybox:latest \
                        /bin/sh -c "/code/jenkins_git_clean.sh"
                '''
            }
        }

        stage('Docker build') {
            steps {
                script {
                    docker.build(
                        "${DOCKER_IMAGE}", ". -f ${SOURCE_DIR}/Dockerfile")
                }
            }
        }

        stage('Start gpf impala') {
            steps {
                sh '''
                    ${WD}/scripts/docker_run_gpf_impala.sh
                '''
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

                    sed -i "s/localhost/impala/" $WD/data-hg19-startup/DAE.conf
                            docker run -d --rm \
                                -v ${SOURCE_DIR}:/code \
                                busybox:latest \
                                /bin/sh -c "sed -i \"s/localhost/impala/\" /code/dae_conftests/dae_conftests/tests/fixtures/DAE.conf"
                '''
            }
        }


        stage('Lint') {
            steps {
                sh '''
                    docker run --rm \
                        --network ${DOCKER_NETWORK} \
                        --link ${DOCKER_CONTAINER_IMPALA}:impala \
                        -v ${DATA}:/data \
                        -v ${SOURCE_DIR}:/code \
                        ${DOCKER_IMAGE} /code/jenkins_flake8.sh

                '''
            }
        }

        stage('Test') {
            steps {
                sh """
                    docker run --rm \
                        --network ${DOCKER_NETWORK} \
                        --link ${DOCKER_CONTAINER_IMPALA}:impala \
                        -v ${DATA}:/data \
                        -v ${SOURCE_DIR}:/code \
                        ${DOCKER_IMAGE} /code/scripts/wait-for-it.sh impala:21050 --timeout=240

                """

                sh """
                    docker run --rm \
                        --network ${DOCKER_NETWORK} \
                        --link ${DOCKER_CONTAINER_IMPALA}:impala \
                        -v ${DATA}:/data \
                        -v ${SOURCE_DIR}:/code \
                        ${DOCKER_IMAGE} /code/jenkins_test.sh

                """

            }
        }
    }
    post {
        always {
            junit 'test_results/wdae-junit.xml, test_results/dae-junit.xml'
            step([
                $class: 'CoberturaPublisher',
                coberturaReportFile: 'test_results/coverage.xml'])

            warnings(
                parserConfigurations: [[parserName: 'PyLint', pattern: 'test_results/pyflakes.report']],
                excludePattern: '.*site-packages.*',
                usePreviousBuildAsReference: true,
            )
            sh '''
                    docker stop ${DOCKER_CONTAINER_IMPALA}
                    docker rm ${DOCKER_CONTAINER_IMPALA}
                    docker network prune --force
                    docker images rm ${DOCKER_IMAGE}
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
