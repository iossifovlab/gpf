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

        GPF_DOCKER_NETWORK="gpf_base_${env.BRANCH_NAME}_${env.BUILD_NUMBER}"
        GPF_DOCKER_IMAGE="iossifovlab/gpf_base_${env.BRANCH_NAME}:${env.BUILD_NUMBER}"
        GPF_IMPALA_DOCKER_CONTAINER="gpf_impala_${env.BRANCH_NAME}_${env.BUILD_NUMBER}"
        GPF_REMOTE_DOCKER_CONTAINER="gpf_test_remote_${env.BRANCH_NAME}_${env.BUILD_NUMBER}"
        GPF_TEST_REMOTE_HOSTNAME="gpfremote"

        DAE_DB_DIR="${env.WORKSPACE}/data-hg19-startup"

        CLEANUP=1
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
                        -v ${WD}:/code \
                        busybox:latest \
                        /bin/sh -c "rm -rf /code/wdae-*.log && rm -rf /code/wdae_django*.cache"
                    docker run -d --rm \
                        -v ${WD}:/code \
                        busybox:latest \
                        /bin/sh -c "/code/jenkins_git_clean.sh"
                    docker run -d --rm \
                        -v ${WD}:/code \
                        busybox:latest \
                        /bin/sh -c "rm -rf /code/test_results/*"
                '''
            }
        }

        stage('Docker build') {
            steps {
                script {
                    docker.build(
                        "${GPF_DOCKER_IMAGE}", ". -f ${WD}/Dockerfile")
                }
            }
        }

        stage('Create docker network') {
            steps {
                sh '''
                    ${WD}/create_docker_network.sh
                '''
            }
        }

        stage('Start federation remote instance') {
            steps {
                sh '''
                    ${WD}/scripts/setup_remote_gpf_container.sh
                    ${WD}/scripts/run_remote_gpf_container.sh
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
                                -v ${WD}:/code \
                                busybox:latest \
                                /bin/sh -c "sed -i \"s/localhost/impala/\" /code/dae_conftests/dae_conftests/tests/fixtures/DAE.conf"
                '''
            }
        }


        stage('Lint') {
            steps {
                sh '''
                    docker run --rm \
                        -v ${DAE_DB_DIR}:/data \
                        -v ${WD}:/code \
                        ${GPF_DOCKER_IMAGE} /code/jenkins_flake8.sh

                '''
            }
        }

        stage('Type Check') {
            steps {
                sh '''
                    docker run --rm \
                        -v ${DAE_DB_DIR}:/data \
                        -v ${WD}:/code \
                        ${GPF_DOCKER_IMAGE} /code/jenkins_mypy.sh
                '''
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

        }
        success {
	    archiveArtifacts artifacts: 'mypy_report.tar.gz'

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
