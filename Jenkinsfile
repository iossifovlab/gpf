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
            name: 'DATA_HG19_BUILD', defaultValue: '158',
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

        // CLEANUP=1
    }
    stages {
        stage ('Start') {
            steps {
                zulipSend(
                    message: "Started build #${env.BUILD_NUMBER} of project ${env.JOB_NAME} (${env.BUILD_URL})",
                    topic: "${env.JOB_NAME}")
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
                    docker run -d --rm \
                        -v ${WD}:/code \
                        busybox:latest \
                        /bin/sh -c "rm -rf /code/gpf_remote"
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

        stage('Data') {
            steps {
                sh '''
                    rm -f builds/*
                '''
                script {
                    println "DATA_HG19_BRANCH=" + DATA_HG19_BRANCH

                    copyArtifacts(
                        projectName: 'seqpipe/data-hg19-startup/' + DATA_HG19_BRANCH,
                        selector: lastSuccessful()
                    );
                }
                sh '''
                    tar zxf builds/data-hg19-startup-*.tar.gz -C $WD
                    
                    mkdir -p $WD/data-hg19-startup/wdae

                    sed -i "s/localhost/impala/" $WD/data-hg19-startup/DAE.conf
                            docker run -d --rm \
                                -v ${WD}:/code \
                                busybox:latest \
                                /bin/sh -c "sed -i \"s/localhost/impala/\" /code/dae_conftests/dae_conftests/tests/fixtures/DAE.conf"
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

        stage('Test') {
            steps {
                sh '''
                    ${WD}/run_tests.sh
                '''
            }
        }
    }
    post {
        always {
            sh '''
                ${WORKSPACE}/scripts/clean_up_docker.sh
            '''

            junit 'test_results/wdae-junit.xml, test_results/dae-junit.xml'

            step([
                $class: 'CoberturaPublisher',
                coberturaReportFile: 'test_results/coverage.xml'])

            zulipNotification(
                topic: "${env.JOB_NAME}"
            )      

        }
        success {
    	    archiveArtifacts artifacts: 'mypy_report.tar.gz'

        }
    }
}
