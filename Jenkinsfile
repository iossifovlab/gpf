// Jenkins pipeline for the GPF monorepo.
//
// Runs per-sub-project CI in parallel. Each project:
//   1. Builds its Dockerfile image from the repo root build context.
//   2. Inside the container, runs ruff, mypy, pylint, and pytest with JUnit
//      output, plus Cobertura coverage for pytest.
//   3. Publishes JUnit + coverage reports to Jenkins.
//
// Lint / type-check tools (ruff, mypy, pylint) only report via their JUnit
// XML and don't gate the build. Pytest, however, propagates its exit code
// so test failures fail the build (the post.always hook still publishes
// the JUnit + coverage reports either way).

def runProject(Map args) {
    String name           = args.name                          // dir name, e.g. "core"
    String pkg            = args.pkg                           // importable Python package, e.g. "gpf"
    String tests          = args.tests                         // pytest target relative to project dir
    String mypyTarget     = args.mypyTarget ?: pkg
    String mypyExtra      = args.mypyExtra ?: ''               // e.g. "--config-file /workspace/mypy.ini"
    String pytestArgs     = args.pytestArgs ?: ''              // e.g. "-n auto"
    String dockerRunExtra = args.dockerRunExtra ?: ''          // extra flags for `docker run` (network, -v, -e, ...)
    String distName       = name.replace('_', '-')
    String distPkg        = args.distPkg ?: "gpf-${distName}"  // PyPI-style name, e.g. "gpf-rest-client"
    String imageTag       = "gpf-${distName}-ci:${env.BUILD_NUMBER}"

    sh label: "Build ${name} image", script: """
        docker build -f ${name}/Dockerfile -t ${imageTag} .
    """

    // Mount .git read-only so hatch-vcs can derive the version during
    // `uv build`. .git is excluded from the Docker build context via
    // .dockerignore, which keeps the test image small and cacheable;
    // it's only needed at distribution-build time.
    sh label: "Run ${name} CI", script: """
        mkdir -p reports/${name} dist/${name}
        docker run --rm \\
            -v \$PWD/reports/${name}:/reports \\
            -v \$PWD/dist/${name}:/dist \\
            -v \$PWD/.git:/workspace/.git:ro \\
            ${dockerRunExtra} \\
            ${imageTag} \\
            sh -c '
                set +e
                ruff check --output-format=junit --output-file=/reports/ruff.xml .
                mypy ${mypyExtra} ${mypyTarget} --junit-xml=/reports/mypy.xml
                pylint_rcfile=/workspace/${name}/pylintrc
                if [ ! -f "\$pylint_rcfile" ]; then
                    pylint_rcfile=/workspace/pylintrc
                fi
                pylint --rcfile="\$pylint_rcfile" \\
                       --load-plugins=pylint_junit \\
                       --output-format=pylint_junit.JUnitReporter \\
                       --exit-zero ${pkg} > /reports/pylint.xml
                pytest ${pytestArgs} \\
                    --junitxml=/reports/pytest.xml \\
                    --cov=${pkg} --cov-branch \\
                    --cov-report=xml:/reports/coverage.xml \\
                    ${tests}
                pytest_exit=\$?
                # Rewrite container-absolute <source>/workspace/...</source> to a
                # path relative to the Jenkins workspace so recordCoverage can
                # resolve source files.
                sed -i "s#<source>/workspace/\\([^<]*\\)</source>#<source>\\1</source>#g" \\
                    /reports/coverage.xml 2>/dev/null || true
                # Build wheel + sdist for this project. hatch-vcs reads the
                # mounted .git to produce a proper PEP 440 version.
                uv build --package ${distPkg} --out-dir /dist
                chmod -R a+rw /reports /dist
                # Propagate pytest's exit code so test failures fail the
                # build (FAILURE) instead of just being logged via JUnit
                # (UNSTABLE). The post.always publishReports hook still
                # uploads the XML reports either way. Lint / type-check
                # failures from the steps above don't gate here — they
                # surface via their JUnit XMLs only.
                exit \$pytest_exit
            '
    """
}

def publishReports(String name) {
    junit allowEmptyResults: true, testResults: "reports/${name}/*.xml"
    recordCoverage(
        tools: [[parser: 'COBERTURA', pattern: "reports/${name}/coverage.xml"]],
        id: "${name}-coverage",
        name: "${name} coverage",
        skipPublishingChecks: true,
        failOnError: false,
    )
}

pipeline {
    agent { label '!dory' }

    options {
        timeout(time: 1, unit: 'HOURS')
        buildDiscarder(logRotator(numToKeepStr: '100'))
    }

    stages {
        stage('CI') {
            when { not { buildingTag() } }
            stages {
                stage('Start') {
                    steps {
                        script {
                            properties([
                                copyArtifactPermission('*'),
                            ])
                        }
                        zulipSend(
                            message: "Started build #${env.BUILD_NUMBER} of project ${env.JOB_NAME} (${env.BUILD_URL})",
                            topic: "${env.JOB_NAME}",
                        )
                    }
                }

                stage('Prepare workspace') {
                    steps {
                        sh 'rm -rf reports dist && mkdir -p reports dist'
                    }
                }

                stage('Sub-projects') {
                    parallel {
                        stage('core') {
                            environment {
                                COMPOSE_PROJECT = "gpf-ci-${env.BUILD_NUMBER}"
                                COMPOSE_NETWORK = "gpf-ci-${env.BUILD_NUMBER}_default"
                            }
                            steps {
                                script {
                                    try {
                                        // Bring up apache (HTTP fixture on :80
                                        // inside the network) and minio (S3
                                        // fixture on :9000). Core tests reach
                                        // them by service name via the compose
                                        // network. minio-client is a one-shot
                                        // bucket setup job — run it inline
                                        // instead of via `up --wait`, which
                                        // races with short-lived services.
                                        sh '''
                                            mkdir -p core/tests/.test_grr
                                            docker compose -p "$COMPOSE_PROJECT" \
                                                up -d --wait apache minio
                                            docker compose -p "$COMPOSE_PROJECT" \
                                                run --rm minio-client
                                        '''

                                        runProject(
                                            name: 'core',
                                            pkg: 'gpf',
                                            tests: 'tests/small',
                                            mypyTarget: 'gpf',
                                            mypyExtra: '--config-file /workspace/mypy.ini',
                                            pytestArgs: '-n 5 --enable-http-testing --enable-s3-testing',
                                            dockerRunExtra:
                                                '--network "$COMPOSE_NETWORK" ' +
                                                '-e HTTP_HOST=apache:80 ' +
                                                '-e MINIO_HOST=minio ' +
                                                '-v $PWD/core/tests/.test_grr:/workspace/core/tests/.test_grr',
                                        )
                                    } finally {
                                        sh '''
                                            docker compose -p "$COMPOSE_PROJECT" down -v --remove-orphans || true
                                        '''
                                    }
                                }
                            }
                            post { always { script { publishReports('core') } } }
                        }

                        stage('web') {
                            steps {
                                script {
                                    runProject(
                                        name: 'web',
                                        pkg: 'gpf_web',
                                        tests: 'gpf_web/',
                                        mypyTarget: 'gpf_web',
                                        mypyExtra: '--config-file /workspace/web/mypy.ini',
                                        pytestArgs: '-n 5',
                                        distPkg: 'gpf-web',
                                        dockerRunExtra:
                                            '-e DJANGO_SETTINGS_MODULE=' +
                                            'gpf_web.test_settings',
                                    )
                                }
                            }
                            post { always { script { publishReports('web') } } }
                        }

                        stage('federation') {
                            environment {
                                COMPOSE_PROJECT = "gpf-ci-federation-${env.BUILD_NUMBER}"
                                COMPOSE_NETWORK = "gpf-ci-federation-${env.BUILD_NUMBER}_default"
                            }
                            steps {
                                script {
                                    try {
                                        // MailHog catches outgoing mail so
                                        // user-flow tests can assert against it.
                                        sh '''
                                            docker compose -p "$COMPOSE_PROJECT" \
                                                up -d --wait mail
                                        '''

                                        runProject(
                                            name: 'federation',
                                            pkg: 'federation',
                                            tests: 'tests/',
                                            mypyTarget: 'federation',
                                            mypyExtra: '--config-file /workspace/federation/mypy.ini',
                                            pytestArgs: '',
                                            distPkg: 'gpf-federation',
                                            dockerRunExtra:
                                                '--network "$COMPOSE_NETWORK" ' +
                                                '-e WDAE_EMAIL_HOST=mail ' +
                                                '-e DJANGO_SETTINGS_MODULE=' +
                                                'gpf_web.test_settings',
                                        )
                                    } finally {
                                        sh '''
                                            docker compose -p "$COMPOSE_PROJECT" down -v --remove-orphans || true
                                        '''
                                    }
                                }
                            }
                            post { always { script { publishReports('federation') } } }
                        }

                        stage('rest_client') {
                            environment {
                                COMPOSE_PROJECT = "gpf-ci-rest-client-${env.BUILD_NUMBER}"
                                COMPOSE_NETWORK = "gpf-ci-rest-client-${env.BUILD_NUMBER}_default"
                            }
                            steps {
                                script {
                                    try {
                                        sh '''
                                            docker compose -p "$COMPOSE_PROJECT" \
                                                up -d --wait mail
                                        '''

                                        runProject(
                                            name: 'rest_client',
                                            pkg: 'rest_client',
                                            tests: 'tests/',
                                            pytestArgs: '',
                                            distPkg: 'gpf-rest-client',
                                            dockerRunExtra:
                                                '--network "$COMPOSE_NETWORK" ' +
                                                '-e WDAE_EMAIL_HOST=mail ' +
                                                '-e DJANGO_SETTINGS_MODULE=' +
                                                'gpf_web.test_settings',
                                        )
                                    } finally {
                                        sh '''
                                            docker compose -p "$COMPOSE_PROJECT" down -v --remove-orphans || true
                                        '''
                                    }
                                }
                            }
                            post { always { script { publishReports('rest_client') } } }
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                try {
                    archiveArtifacts(
                        artifacts: 'reports/**/*.xml',
                        allowEmptyArchive: true,
                        fingerprint: false,
                    )
                    archiveArtifacts(
                        artifacts: 'dist/**/*.whl, dist/**/*.tar.gz',
                        allowEmptyArchive: true,
                        fingerprint: true,
                    )
                } finally {
                    zulipNotification(topic: "${env.JOB_NAME}")
                }
            }
        }
        cleanup {
            sh '''
                for img in gpf-core-ci gpf-web-ci gpf-federation-ci gpf-rest-client-ci; do
                    docker rmi "$img:${BUILD_NUMBER}" 2>/dev/null || true
                done
            '''
        }
    }
}
