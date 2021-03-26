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
    environment {
        WD="${env.WORKSPACE}"
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
                    echo "removing GPF data..."
                    docker run -d --rm \
                        -v ${WD}:/wd \
                        busybox:latest \
                        /bin/sh -c "rm -rf /wd/data/*"

                    echo "removing GPF import..."
                    docker run -d --rm \
                        -v ${WD}:/wd \
                        busybox:latest \
                        /bin/sh -c "rm -rf /wd/import/*"

                    echo "removing downloaded data..."
                    docker run -d --rm \
                        -v ${WD}:/wd \
                        busybox:latest \
                        /bin/sh -c "rm -rf /wd/downloads/*"
                    
                    echo "removing results..."
                    docker run -d --rm \
                        -v ${WD}:/wd \
                        busybox:latest \
                        /bin/sh -c "rm -rf /wd/results/*"

                    mkdir -p ${WD}/data
                    mkdir -p ${WD}/import
                    mkdir -p ${WD}/downloads
                    mkdir -p ${WD}/results
                '''
            }
        }

        stage('Docker build') {
            steps {
                sh '''
                . ${WD}/scripts/version.sh

                cd ${WD}
                docker build . -f ${WD}/Dockerfile -t ${IMAGE_GPF_DEV}

                '''
            }
        }


        stage('Data Download') {
            steps {
                script {
                    copyArtifacts(
                        projectName: 'seqpipe/data-hg19-startup/master',
                        selector: lastSuccessful(),
                        target: "${env.WORKSPACE}" + "/downloads"
                    );
                }
            }
        }

        stage('Prepare GPF Data') {
            steps {
                sh '''
                . ${WD}/scripts/version.sh
                ${SCRIPTS}/prepare_gpf_data.sh
                '''
            }
        }

        stage('Prepare Remote GPF Data') {
            steps {
                sh '''
                . ${WD}/scripts/version.sh
                ${SCRIPTS}/prepare_gpf_remote.sh
                '''
            }
        }

        stage('Start Remote GPF') {
            steps {
                sh '''
                . ${WD}/scripts/version.sh
                ${SCRIPTS}/run_gpf_remote.sh
                '''
            }
        }

        stage('Test Data Import') {
            steps {
                sh '''
                . ${WD}/scripts/version.sh
                ${SCRIPTS}/run_gpf_dev.sh internal_run_test_data_import.sh
                '''
            }
        }

        // stage('Lint') {
        //     steps {
        //         sh '''
        //             docker run --rm \
        //                 -v ${DAE_DB_DIR}:/data \
        //                 -v ${WD}:/code \
        //                 ${GPF_DOCKER_IMAGE} /code/jenkins_flake8.sh

        //         '''
        //     }
        // }

        // stage('Type Check') {
        //     steps {
        //         sh '''
        //             docker run --rm \
        //                 -v ${DAE_DB_DIR}:/data \
        //                 -v ${WD}:/code \
        //                 ${GPF_DOCKER_IMAGE} /code/jenkins_mypy.sh
        //         '''
        //     }
        // }

        stage('Test') {
            steps {
                sh '''
                    ${WD}/tests_run.sh
                '''
            }
        }
    }
    post {
        always {
            sh '''
                ${WORKSPACE}/tests_cleanup.sh
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
            sh '''
                ${WORKSPACE}/scripts/package.sh
            '''

    	    // archiveArtifacts artifacts: 'mypy_report.tar.gz'
            
            archiveArtifacts artifacts: 'builds/*.tar.gz'
            archiveArtifacts artifacts: 'builds/*.yml'

            // script {
            //     def job_result = build job: 'seqpipe/seqpipe-gpf-containers/master', propagate: true, wait: false, parameters: [
            //         string(name: 'GPF_BRANCH', value: "master"),
            //         string(name: 'GPF_BUILD', value: "$env.BUILD_NUMBER"),
            //         booleanParam(name: "PUBLISH", value: false)
            //     ]
            // }
        }
    }
}
