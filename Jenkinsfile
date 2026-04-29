// Jenkins pipeline for the GPF monorepo.
//
// Runs per-sub-project CI in parallel. Each project:
//   1. Builds its Dockerfile image from the repo root build context.
//   2. Inside the container, runs ruff, mypy, pylint, and pytest. ruff /
//      mypy / pylint write text reports to /reports; pytest writes JUnit
//      XML + Cobertura coverage.
//   3. Publishes pytest's JUnit + coverage via `junit` and `recordCoverage`,
//      and the lint reports via `recordIssues` (Warnings Next Generation
//      plugin) with a `TOTAL > 0 → unstable` quality gate.
//
// Result mapping:
//   - pytest test failure  → stage exits non-zero  → build FAILURE
//   - mypy / ruff / pylint findings  → recordIssues quality gate  → build
//     UNSTABLE (the stage's exit code is unaffected)
//
// `recordIssues` keeps the lint findings in their own "Issues" tab in
// Jenkins, separate from the "Tests" tab, which makes the FAILURE-vs-
// UNSTABLE distinction visible at a glance.

def runProject(Map args) {
    String name           = args.name                          // dir name, e.g. "core"
    String pkg            = args.pkg                           // importable Python package, e.g. "gpf"
    String tests          = args.tests                         // pytest target relative to project dir
    String mypyTarget     = args.mypyTarget ?: pkg
    String mypyExtra      = args.mypyExtra ?: ''               // e.g. "--config-file /workspace/mypy.ini"
    String pytestArgs     = args.pytestArgs ?: ''              // e.g. "-n auto"
    boolean skipPytest    = args.skipPytest ?: false           // true → only lint, no pytest
    String dockerRunExtra = args.dockerRunExtra ?: ''          // extra flags for `docker run` (network, -v, -e, ...)
    String distName       = name.replace('_', '-')
    String distPkg        = args.distPkg ?: "gpf-${distName}"  // PyPI-style name, e.g. "gpf-rest-client"
    String imageTag       = "gpf-${distName}-ci:${env.BUILD_NUMBER}"

    String pytestBlock = skipPytest ? '''
                # pytest is skipped for this stage — see runProject() call
                # for context.
                pytest_exit=0
''' : """
                # pytest IS gating: its exit code is the only thing that
                # propagates out of this script and decides FAILURE vs
                # SUCCESS for the stage.
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
"""

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
                # ruff / mypy / pylint are non-gating: --exit-zero or `|| true`
                # ensures their non-zero exit codes never propagate. Their
                # findings end up in /reports as text and are picked up by
                # `recordIssues` in the post hook → UNSTABLE quality gate.
                ruff check --exit-zero --output-format=concise . \\
                    > /reports/ruff.txt
                mypy ${mypyExtra} ${mypyTarget} \\
                    > /reports/mypy.txt 2>&1 || true
                pylint_rcfile=/workspace/${name}/pylintrc
                if [ ! -f "\$pylint_rcfile" ]; then
                    pylint_rcfile=/workspace/pylintrc
                fi
                # --recursive=y is what makes the web stage Django
                # layout (a gpf_web/ directory containing multiple
                # Django apps as peer packages) lintable end-to-end; for
                # the other stages it is a no-op.
                pylint --rcfile="\$pylint_rcfile" \\
                       --output-format=parseable \\
                       --recursive=y \\
                       --exit-zero ${pkg} > /reports/pylint.txt
${pytestBlock}
                # Build wheel + sdist for this project. hatch-vcs reads the
                # mounted .git to produce a proper PEP 440 version.
                uv build --package ${distPkg} --out-dir /dist
                chmod -R a+rw /reports /dist
                exit \$pytest_exit
            '
    """
}

def publishReports(String name) {
    // pytest results — `junit` marks UNSTABLE on test failures, but the
    // stage already exited with the pytest exit code so a failure here
    // surfaces as FAILURE.
    junit allowEmptyResults: true, testResults: "reports/${name}/pytest.xml"

    recordCoverage(
        tools: [[parser: 'COBERTURA', pattern: "reports/${name}/coverage.xml"]],
        id: "${name}-coverage",
        name: "${name} coverage",
        skipPublishingChecks: true,
        failOnError: false,
    )

    // Static-analysis findings (ruff / mypy / pylint) — separate per-tool
    // record so each gets its own "Issues" tab and trend chart. Quality
    // gate marks the build UNSTABLE if any new finding appears; FAILURE
    // is reserved for pytest test failures (and stage script errors).
    recordIssues(
        enabledForFailure: true,
        aggregatingResults: false,
        tools: [
            // Warnings NG doesn't ship a `ruff` parser on this Jenkins
            // instance, but ruff's `--output-format=concise` emits flake8
            // syntax (`file:line:col: code message`) which `flake8()`
            // parses correctly.
            flake8(
                pattern: "reports/${name}/ruff.txt",
                id: "${name}-ruff",
                name: "${name} ruff",
            ),
            myPy(
                pattern: "reports/${name}/mypy.txt",
                id: "${name}-mypy",
                name: "${name} mypy",
            ),
            pyLint(
                pattern: "reports/${name}/pylint.txt",
                id: "${name}-pylint",
                name: "${name} pylint",
            ),
        ],
        qualityGates: [[threshold: 1, type: 'TOTAL', unstable: true]],
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
                                        // mypy needs `-p <pkg>` for each
                                        // Django app inside web/gpf_web/.
                                        // The bare names would be ambiguous
                                        // because /workspace/web also has a
                                        // `gpf_web/` Django project layout
                                        // dir without an __init__.py.
                                        mypyTarget:
                                            '-p gpf_web ' +
                                            '-p common_reports_api ' +
                                            '-p datasets_api ' +
                                            '-p enrichment_api ' +
                                            '-p family_api ' +
                                            '-p gene_profiles_api ' +
                                            '-p gene_scores ' +
                                            '-p gene_sets ' +
                                            '-p gene_view ' +
                                            '-p genomes_api ' +
                                            '-p genomic_scores_api ' +
                                            '-p genotype_browser ' +
                                            '-p gpf_instance ' +
                                            '-p gpfjs ' +
                                            '-p groups_api ' +
                                            '-p measures_api ' +
                                            '-p person_sets_api ' +
                                            '-p pheno_browser_api ' +
                                            '-p pheno_tool_api ' +
                                            '-p query_base ' +
                                            '-p query_state_save ' +
                                            '-p sentry ' +
                                            '-p studies ' +
                                            '-p user_queries ' +
                                            '-p users_api ' +
                                            '-p utils',
                                        mypyExtra:
                                            '--config-file /workspace/web/mypy.ini',
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

                        // federation and rest_client tests are integration
                        // tests that need a running gpf-web backend on
                        // localhost:21010 / localhost:21011 (the old
                        // docker-compose-jenkins.yaml in each subdir set
                        // this up). The new Jenkinsfile does not yet bring
                        // up that backend stack, so for now both stages
                        // run linters only (`skipPytest: true`). When the
                        // backend stack is wired back in, drop skipPytest
                        // and add the `--url` / `TEST_REMOTE_HOST` env
                        // wiring back into dockerRunExtra.

                        stage('federation') {
                            steps {
                                script {
                                    runProject(
                                        name: 'federation',
                                        pkg: 'federation',
                                        tests: 'tests/',
                                        mypyTarget: 'federation',
                                        mypyExtra: '--config-file /workspace/federation/mypy.ini',
                                        skipPytest: true,
                                        distPkg: 'gpf-federation',
                                    )
                                }
                            }
                            post { always { script { publishReports('federation') } } }
                        }

                        stage('rest_client') {
                            steps {
                                script {
                                    runProject(
                                        name: 'rest_client',
                                        pkg: 'rest_client',
                                        tests: 'tests/',
                                        skipPytest: true,
                                        distPkg: 'gpf-rest-client',
                                    )
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
