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
                # --recursive=y is what makes the web_api stage Django
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
        stage('Dispatch release') {
            // A CalVer tag pushed to iossifovlab/gpf lands here as a
            // multibranch tag-build. Fire the gpf-release pipelineJob
            // (DSL at jenkins-jobs/release.groovy) and exit. The
            // multibranch tag-build is intentionally a thin shim so
            // this Jenkinsfile stays focused on per-branch CI;
            // gpf-release owns the actual release flow.
            //
            // wait:false,propagate:false matches the Trigger web_e2e
            // / Trigger ...-integration patterns: the dispatcher's
            // tag-build always exits SUCCESS once gpf-release is
            // queued; the release outcome lives in gpf-release's own
            // build history + Zulip notifications.
            //
            // The CalVer regex here mirrors the one in
            // Jenkinsfile.release for defense in depth (the release
            // pipeline re-validates TAG_NAME on entry). The legacy
            // 3.3.rcN.NNN tag train fails this regex and the stage
            // is a no-op SUCCESS — those tags stay harmless.
            when {
                buildingTag()
                expression {
                    env.TAG_NAME ==~ /^\d{4}\.\d+\.\d+$/
                }
            }
            steps {
                build(
                    job: '/gpf-release',
                    parameters: [
                        string(
                            name: 'TAG_NAME',
                            value: env.TAG_NAME,
                        ),
                    ],
                    wait: false,
                    propagate: false,
                )
            }
        }

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

                stage('Detect change scope') {
                    // Sets env.DOCS_ONLY='true' iff every file in this
                    // build's changeset lives under docs/. Heavy stages
                    // (Sub-projects, Conda, prod images, downstream
                    // triggers) gate on it and skip when only docs
                    // changed. Build docs / Deploy docs keep their
                    // existing `changeset 'docs/**'` clauses.
                    //
                    // Empty changeset (first build, manual rebuild, no
                    // commits since last build) → DOCS_ONLY='false' →
                    // full CI. Conservative default — only short-circuit
                    // when we positively know it's docs-only.
                    steps {
                        script {
                            def changedFiles = []
                            for (changeSet in currentBuild.changeSets) {
                                for (item in changeSet.items) {
                                    changedFiles.addAll(item.affectedPaths)
                                }
                            }
                            boolean isDocsOnly =
                                !changedFiles.isEmpty() &&
                                changedFiles.every { it.startsWith('docs/') }
                            env.DOCS_ONLY = isDocsOnly ? 'true' : 'false'
                            echo "Changeset: ${changedFiles.size()} file(s); " +
                                 "DOCS_ONLY=${env.DOCS_ONLY}"
                        }
                    }
                }

                stage('Apply Job DSL') {
                    // Run jobDsl on master only — this is the
                    // bootstrap that materialises (or updates) the
                    // root-level pipelineJob() declarations under
                    // **/jenkins-jobs/*.groovy. After this runs, the
                    // gpf-federation-integration / gpf-rest-client-
                    // integration jobs exist on the controller and
                    // the Trigger ... integration stages below can
                    // queue them. No separate gpf-seed pipelineJob
                    // is needed — the multibranch project at
                    // iossifovlab/gpf/master auto-runs this Jenkinsfile
                    // on every master push, which is the same trigger
                    // surface a dedicated seed job would have.
                    //
                    // Branch builds skip this stage; their Trigger
                    // stages still wrap build() in catchError, so a
                    // branch that touches the .groovy files before
                    // they reach master just sees UNSTABLE there
                    // until the next master build re-seeds.
                    //
                    // First-run note: on the first master build with
                    // a new jobDsl call, the Jenkins admin may need
                    // to approve the script under
                    // Manage Jenkins → In-process Script Approval.
                    //
                    when { branch 'master' }
                    steps {
                        jobDsl(
                            targets: '**/jenkins-jobs/*.groovy',
                            removedJobAction: 'IGNORE',
                            removedViewAction: 'IGNORE',
                        )
                    }
                }

                stage('Conda builder image') {
                    when { not { environment name: 'DOCS_ONLY', value: 'true' } }
                    steps {
                        sh '''
                            docker build -f conda-builder/Dockerfile \
                                -t gpf-conda-builder-ci:${BUILD_NUMBER} conda-builder
                        '''
                    }
                }

                stage('Fetch gain wheel') {
                    // Pull the gain-core wheel from gain's last
                    // successful master build into dist/gain/.
                    // Consumed by web_api/Dockerfile.production (the
                    // backend prod image's builder stage installs
                    // /wheels/*.whl which now includes gain-core)
                    // and re-archived to dist/gain/*.whl by the
                    // archiveArtifacts at the end so downstream
                    // jobs (gpf-web-e2e) can copy the same wheel
                    // and test against the exact same gain build
                    // this gpf build was assembled with.
                    //
                    // selector: lastSuccessful() pulls the most
                    // recent green gain master. No build-arg
                    // parameter for now — the gain → gpf trigger
                    // (which would pin to a specific gain build
                    // number) is separate work.
                    //
                    // flatten: true drops the dist/core/ prefix
                    // so the wheel lands at dist/gain/gain_core-
                    // <version>-py3-none-any.whl rather than
                    // dist/gain/dist/core/gain_core-...whl.
                    steps {
                        copyArtifacts(
                            filter: 'dist/core/*.whl',
                            fingerprintArtifacts: true,
                            projectName: 'iossifovlab/gain/master',
                            selector: lastSuccessful(),
                            target: 'dist/gain',
                            flatten: true,
                        )
                        sh '''
                            ls -la dist/gain/
                            test -n "$(ls dist/gain/gain_core-*.whl 2>/dev/null)"
                        '''
                    }
                }

                stage('Sub-projects') {
                    when { not { environment name: 'DOCS_ONLY', value: 'true' } }
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
                                        // tb-o19: pass -f docker-compose.yaml
                                        // explicitly so docker compose does
                                        // NOT auto-load
                                        // docker-compose.override.yaml. The
                                        // override file publishes host ports
                                        // 127.0.0.1:29000/29001/28080 for
                                        // local-dev `docker compose up`; in
                                        // CI those host ports are global to
                                        // the agent and any concurrent build
                                        // would race on them. Mirrors gain's
                                        // Jenkinsfile, which has used -f
                                        // since the override file existed.
                                        sh '''
                                            mkdir -p core/tests/.test_grr
                                            docker compose -f docker-compose.yaml \
                                                -p "$COMPOSE_PROJECT" \
                                                up -d --wait apache minio
                                            docker compose -f docker-compose.yaml \
                                                -p "$COMPOSE_PROJECT" \
                                                run --rm minio-client
                                        '''

                                        // tb-eqh: wait-for-minio sidecar.
                                        // `up -d --wait` only verifies minio's
                                        // own healthcheck (curl on localhost
                                        // inside the minio container). That
                                        // does NOT prove a sibling container
                                        // can resolve `minio` via Docker's
                                        // embedded DNS yet. The flake we hit
                                        // is exactly that: test runner starts,
                                        // first boto3 call returns empty
                                        // addr_infos because resolv.conf
                                        // lookup of `minio` returned nothing.
                                        // A throwaway curl container attached
                                        // to $COMPOSE_NETWORK exercises the
                                        // exact same DNS+TCP+HTTP path the
                                        // test runner will, and gates the
                                        // test runner on it succeeding. The
                                        // --retry flags expose any retry rate
                                        // in the console log so we stay
                                        // visible to the underlying race.
                                        sh '''
                                            docker run --rm --network "$COMPOSE_NETWORK" \
                                                curlimages/curl:latest \
                                                --retry 10 --retry-delay 2 --retry-all-errors \
                                                -fsS http://minio:9000/minio/health/live
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
                                        // tb-eqh: on core stage exit (success
                                        // or failure), dump network + minio
                                        // state into reports/core/ so a
                                        // post-mortem of the next flake hit
                                        // has bird's-eye evidence to pair
                                        // with the worm's-eye conftest dump.
                                        // Best-effort — every command guarded
                                        // with `|| true` so a missing
                                        // container or a teardown race never
                                        // overrides the actual test exit
                                        // code. publishReports('core') picks
                                        // these up via the post stage.
                                        sh '''
                                            mkdir -p reports/core
                                            (
                                                echo "=== docker network inspect $COMPOSE_NETWORK ==="
                                                docker network inspect "$COMPOSE_NETWORK" 2>&1 || true
                                                echo
                                                echo "=== docker ps -a (compose project $COMPOSE_PROJECT) ==="
                                                docker ps -a --filter "label=com.docker.compose.project=$COMPOSE_PROJECT" 2>&1 || true
                                                echo
                                                echo "=== docker logs ${COMPOSE_PROJECT}-minio-1 (tail 200) ==="
                                                docker logs "${COMPOSE_PROJECT}-minio-1" --tail 200 2>&1 || true
                                                echo
                                                echo "=== sidecar DNS probe (busybox on $COMPOSE_NETWORK) ==="
                                                docker run --rm --network "$COMPOSE_NETWORK" busybox sh -c '
                                                    echo "--- /etc/resolv.conf ---"
                                                    cat /etc/resolv.conf
                                                    echo "--- nslookup minio ---"
                                                    nslookup minio 2>&1 || true
                                                    echo "--- getent hosts minio ---"
                                                    getent hosts minio 2>&1 || true
                                                    echo "--- ping -c 1 minio ---"
                                                    ping -c 1 minio 2>&1 || true
                                                ' 2>&1 || true
                                            ) > reports/core/network-diagnostic.txt 2>&1 || true

                                            docker compose -f docker-compose.yaml -p "$COMPOSE_PROJECT" down -v --remove-orphans || true
                                        '''
                                    }
                                }
                            }
                            post {
                                always {
                                    script { publishReports('core') }
                                    // tb-eqh: the finally{} block in this
                                    // stage writes a bird's-eye network
                                    // diagnostic (docker network inspect,
                                    // ps -a, minio logs, sibling DNS probe)
                                    // to reports/core/network-diagnostic.txt
                                    // — but publishReports() only handles
                                    // XML reports, so the text file was not
                                    // landing in the archived artifacts.
                                    // Build #63 surfaced this: the
                                    // worm's-eye conftest dump made it via
                                    // JUnit stderr capture, but the
                                    // bird's-eye file was lost. Archive it
                                    // explicitly here. allowEmptyArchive so
                                    // that a teardown race that prevents
                                    // file creation doesn't fail the post
                                    // stage.
                                    archiveArtifacts(
                                        artifacts: 'reports/core/network-diagnostic.txt',
                                        allowEmptyArchive: true,
                                        fingerprint: false,
                                    )
                                }
                            }
                        }

                        stage('web_api') {
                            steps {
                                script {
                                    runProject(
                                        name: 'web_api',
                                        pkg: 'gpf_web',
                                        tests: 'gpf_web/',
                                        // mypy needs `-p <pkg>` for each
                                        // Django app inside web_api/gpf_web/.
                                        // The bare names would be ambiguous
                                        // because /workspace/web_api also has a
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
                                            '--config-file /workspace/web_api/mypy.ini',
                                        pytestArgs: '-n 5',
                                        distPkg: 'gpf-web',
                                        dockerRunExtra:
                                            '-e DJANGO_SETTINGS_MODULE=' +
                                            'gpf_web.test_settings',
                                    )
                                }
                            }
                            post { always { script { publishReports('web_api') } } }
                        }

                        stage('web_ui') {
                            steps {
                                script {
                                    String imageTag =
                                        "gpf-web-ui-ci:${env.BUILD_NUMBER}"
                                    sh label: 'Build web_ui image', script: """
                                        docker build -f web_ui/Dockerfile \
                                            -t ${imageTag} .
                                    """
                                    // ESLint + Stylelint + Jest run inline because
                                    // runProject() is Python-specific (uv build,
                                    // pylint, mypy, pytest). Single sh -c so all
                                    // four reports land in one bind mount.
                                    sh label: 'Run web_ui CI', script: """
                                        mkdir -p reports/web_ui
                                        docker run --rm \\
                                            -v \$PWD/reports/web_ui:/reports \\
                                            ${imageTag} \\
                                            sh -c '
                                                set +e
                                                mkdir -p /reports/coverage
                                                npx eslint "**/*.{html,ts}" \\
                                                    --format checkstyle \\
                                                    > /reports/ts-lint-report.xml
                                                npx stylelint \\
                                                    --custom-formatter \\
                                                    stylelint-checkstyle-formatter \\
                                                    "**/*.css" \\
                                                    > /reports/css-lint-report.xml
                                                JEST_JUNIT_OUTPUT_DIR=/reports \\
                                                JEST_JUNIT_OUTPUT_NAME=jest.xml \\
                                                    npx jest --ci \\
                                                        --collectCoverageFrom=./src/** \\
                                                        --coverageDirectory=/reports/coverage
                                                jest_exit=\$?
                                                # Rewrite container-absolute /app
                                                # paths to web_ui/ so Jenkins coverage
                                                # source mapping resolves files. This
                                                # mirrors the runProject() sed for the
                                                # python projects.
                                                sed -i \\
                                                    "s#<source>/app</source>#<source>web_ui</source>#g" \\
                                                    /reports/coverage/cobertura-coverage.xml \\
                                                    2>/dev/null || true
                                                cp /reports/coverage/cobertura-coverage.xml \\
                                                    /reports/coverage.xml \\
                                                    2>/dev/null || true
                                                chmod -R a+rw /reports
                                                # Propagate jest's exit code so test
                                                # failures fail the build (mirrors the
                                                # python projects' pytest gating).
                                                # eslint / stylelint failures don't
                                                # gate; they surface through their
                                                # report XMLs only.
                                                exit \$jest_exit
                                            '
                                    """
                                }
                            }
                            post {
                                always {
                                    script {
                                        // publishReports() is Python-specific
                                        // (pytest junit + ruff/mypy/pylint
                                        // recordIssues). For web_ui we publish
                                        // jest's junit + the cobertura coverage
                                        // here, and the lint findings via the
                                        // separate recordIssues below.
                                        junit(
                                            allowEmptyResults: true,
                                            testResults: 'reports/web_ui/jest.xml',
                                        )
                                        recordCoverage(
                                            tools: [[
                                                parser: 'COBERTURA',
                                                pattern: 'reports/web_ui/coverage.xml',
                                            ]],
                                            id: 'web_ui-coverage',
                                            name: 'web_ui coverage',
                                            skipPublishingChecks: true,
                                            failOnError: false,
                                        )
                                        recordIssues(
                                            enabledForFailure: true,
                                            aggregatingResults: false,
                                            tools: [
                                                checkStyle(
                                                    pattern: 'reports/web_ui/ts-lint-report.xml',
                                                    reportEncoding: 'UTF-8',
                                                    id: 'web_ui-eslint',
                                                    name: 'web_ui ESLint'),
                                                checkStyle(
                                                    pattern: 'reports/web_ui/css-lint-report.xml',
                                                    reportEncoding: 'UTF-8',
                                                    id: 'web_ui-stylelint',
                                                    name: 'web_ui Stylelint'),
                                            ],
                                            qualityGates: [[threshold: 1, type: 'DELTA', unstable: true]]
                                        )
                                    }
                                }
                            }
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

                stage('Build docs') {
                    when { changeset 'docs/**' }
                    // Migrated from iossifovlab/gpf_documentation
                    // (iossifovlab/gpf#841). The source tree now lives in
                    // docs/. Build runs inside the web_api CI image
                    // (already has gpf + gpf_web installed under
                    // /workspace/.venv); the docs dependency group from
                    // the root pyproject.toml is layered on top at run-
                    // time.
                    //
                    // Only runs when docs/** changed in this build's
                    // commit range; saves ~2 min on code-only changes.
                    // A docstring tweak in core/gpf or web_api/gpf_web
                    // won't refresh the rendered autodoc page until a
                    // docs-side commit lands — accepted trade-off
                    // (iossifovlab/gpf#849 conversation).
                    //
                    // When DOCS_ONLY=true the Sub-projects > web_api
                    // stage is skipped, so we build the web_api CI
                    // image inline here. Idempotent — when Sub-projects
                    // did run, the image already exists and the
                    // docker build is a near-instant cache hit; we
                    // still re-issue it so the stage is self-contained
                    // and runnable in either mode.
                    steps {
                        sh '''
                            docker build -f web_api/Dockerfile \
                                -t gpf-web-api-ci:${BUILD_NUMBER} .
                            mkdir -p dist/docs
                            docker run --rm \
                                -v $PWD:/workspace \
                                -v $PWD/.git:/workspace/.git:ro \
                                -w /workspace \
                                gpf-web-api-ci:${BUILD_NUMBER} \
                                sh -c '
                                    set -eu
                                    # The `docs` group is defined on the
                                    # root virtual workspace, so install
                                    # without --package: this installs
                                    # gpf-core + gpf-web (the root deps)
                                    # plus the sphinx toolchain.
                                    uv sync --group docs \
                                        --upgrade-package gain-core \
                                        --find-links ./dist/gain
                                    bash docs/build_docs.sh
                                '
                            cp docs/gpfdocs-html.tar.gz dist/docs/
                        '''
                    }
                }

                stage('Deploy docs') {
                    when {
                        allOf {
                            branch 'master'
                            changeset 'docs/**'
                        }
                    }
                    // Master-only ansible push to iossifovlab.com, only
                    // when docs/** changed. Skipped on every branch
                    // build and on master builds that don't touch the
                    // docs tree, so the live site keeps serving the
                    // last good build's content untouched.
                    //
                    // Uses the Jenkins-managed `gpf-docs-deploy` SSH
                    // credential (set up 2026-05-11). Independent of
                    // which '!dory' agent picks up the build; the
                    // earlier bind-mount-the-agent's-~/.ssh approach
                    // was agent-roulette and failed when the picked
                    // agent didn't have the deploy key.
                    steps {
                        withCredentials([sshUserPrivateKey(
                            credentialsId: 'gpf-docs-deploy',
                            keyFileVariable: 'SSH_KEY',
                            usernameVariable: 'SSH_USER',
                        )]) {
                            sh '''
                                docker run --rm \
                                    -v $PWD:/workspace \
                                    -v $SSH_KEY:/deploy.key:ro \
                                    -e SSH_USER \
                                    -w /workspace \
                                    gpf-web-api-ci:${BUILD_NUMBER} \
                                    sh -c '
                                        set -eu
                                        apt-get update
                                        apt-get install -y --no-install-recommends \
                                            ansible openssh-client
                                        mkdir -p /root/.ssh
                                        chmod 700 /root/.ssh
                                        ssh-keyscan -H iossifovlab.com \
                                            > /root/.ssh/known_hosts 2>/dev/null
                                        chmod 600 /root/.ssh/known_hosts
                                        ANSIBLE_PRIVATE_KEY_FILE=/deploy.key \
                                            ANSIBLE_REMOTE_USER="$SSH_USER" \
                                            bash docs/deploy/docs_deploy.sh
                                    '
                            '''
                        }
                    }
                }

                stage('Conda packages') {
                    when { not { environment name: 'DOCS_ONLY', value: 'true' } }
                    steps {
                        sh '''
                            # Derive the hatch-vcs PEP 440 version from any wheel name;
                            # pass it to rattler-build via env so the conda package
                            # version matches the wheel's.
                            VCS_VERSION=$(ls dist/core/*.whl | head -1 \
                                | sed 's#.*gpf_core-##' \
                                | sed 's#-py3-none-any.whl$##')
                            echo "VCS_VERSION=$VCS_VERSION"

                            mkdir -p dist/conda
                            # Run the conda-builder container as the Jenkins user
                            # (instead of the image's default `mambauser`, UID
                            # 57439). rattler-build creates its output `.conda`
                            # via a 0600-mode tempfile, so files produced by
                            # mambauser end up unreadable to Jenkins on the host;
                            # matching UIDs sidesteps that entirely. HOME is
                            # redirected to /tmp because /home/mambauser is not
                            # writable by an arbitrary UID.
                            DOCKER_USER="$(id -u):$(id -g)"
                            for proj in core web_api federation rest_client; do
                                mkdir -p conda/$proj
                                docker run --rm \
                                    --user "$DOCKER_USER" \
                                    -e HOME=/tmp \
                                    -v $PWD:/workspace \
                                    -w /workspace \
                                    -e VCS_VERSION="$VCS_VERSION" \
                                    gpf-conda-builder-ci:${BUILD_NUMBER} \
                                    rattler-build build \
                                        --recipe $proj/conda-recipe/recipe.yaml \
                                        --output-dir conda/$proj
                                # Promote the final .conda artefact(s) out of
                                # rattler-build's working tree. conda/$proj/bld/
                                # holds 1000+ symlinks into build-env prefixes;
                                # archiveArtifacts walking that tree has raced
                                # with it. dist/conda/ stays clean and holds
                                # only the published packages.
                                cp conda/$proj/noarch/*.conda dist/conda/
                            done
                        '''
                    }
                }

                stage('Build & push prod images') {
                    when { not { environment name: 'DOCS_ONLY', value: 'true' } }
                    // Builds the wheel-based backend + Apache-based
                    // frontend prod images here in the root build, tags
                    // them for registry.seqpipe.org, and pushes on
                    // master. Branch builds build-but-don't-push
                    // (validates the Dockerfiles + that the wheels
                    // install). Tags pushed on master:
                    //   :${BUILD_NUMBER}  — Jenkins build identity
                    //   :${GIT_SHORT}     — immutable git-anchored handle
                    //   :latest           — moving pointer for prod
                    environment {
                        REGISTRY      = 'registry.seqpipe.org'
                        BACKEND_REPO  = "${env.REGISTRY}/gpf-web-api"
                        FRONTEND_REPO = "${env.REGISTRY}/gpf-web-ui"
                        BUNDLE_REPO   = "${env.REGISTRY}/gpf-web"
                        GIT_SHORT     = "${env.GIT_COMMIT.take(8)}"
                        // Two secret-text credentials, set up in Jenkins.
                        // Bound here for the whole stage but only used by
                        // the master-only push path below.
                        REGISTRY_USER = credentials('user.registry.seqpipe.org')
                        REGISTRY_PASS = credentials('passwd.registry.seqpipe.org')
                    }
                    steps {
                        sh '''
                            # Pull base images up front so `docker image
                            # inspect` further down can read a populated
                            # RepoDigests. BuildKit-driven `docker build`
                            # pulls images into BuildKit's content store
                            # but doesn't always register them at the
                            # daemon level with a <repo>:<tag> +
                            # RepoDigests entry, which leaves NODE_IMAGE
                            # / HTTPD_IMAGE empty in dist/base-images.lock.
                            docker pull python:3.12-slim
                            docker pull node:22.14.0-alpine
                            docker pull httpd:2.4-alpine

                            # Build backend; tag with build number first
                            # so the frontend's --build-arg can reference
                            # it. PYTHON_IMAGE is passed explicitly so the
                            # Dockerfile is consistent across master (this
                            # path, floating tag) and any future digest-
                            # pinned release stage.
                            docker build \
                                -f web_api/Dockerfile.production \
                                --build-arg PYTHON_IMAGE=python:3.12-slim \
                                -t "$BACKEND_REPO:$BUILD_NUMBER" .
                            docker tag "$BACKEND_REPO:$BUILD_NUMBER" \
                                       "$BACKEND_REPO:$GIT_SHORT"

                            # Build frontend; multi-stages collectstatic
                            # from the backend image we just built.
                            docker build \
                                -f web_ui/Dockerfile.production \
                                --build-arg NODE_IMAGE=node:22.14.0-alpine \
                                --build-arg HTTPD_IMAGE=httpd:2.4-alpine \
                                --build-arg BACKEND_IMAGE="$BACKEND_REPO:$BUILD_NUMBER" \
                                -t "$FRONTEND_REPO:$BUILD_NUMBER" .
                            docker tag "$FRONTEND_REPO:$BUILD_NUMBER" \
                                       "$FRONTEND_REPO:$GIT_SHORT"

                            # Build the combined bundle image: thin
                            # assembly layer that copies the venv from
                            # the backend image and the SPA + Django
                            # static from the frontend image, plus
                            # apache2 + supervisord. Single-container
                            # deploy artifact (gunicorn on loopback
                            # :9001, apache on :80).
                            docker build \
                                -f Dockerfile.production \
                                --build-arg PYTHON_IMAGE=python:3.12-slim \
                                --build-arg BACKEND_IMAGE="$BACKEND_REPO:$BUILD_NUMBER" \
                                --build-arg FRONTEND_IMAGE="$FRONTEND_REPO:$BUILD_NUMBER" \
                                -t "$BUNDLE_REPO:$BUILD_NUMBER" .
                            docker tag "$BUNDLE_REPO:$BUILD_NUMBER" \
                                       "$BUNDLE_REPO:$GIT_SHORT"

                            # Resolve and record the base-image digests
                            # this build used, so a future release
                            # pipeline can rebuild from a tagged commit
                            # against the same base layers. Archived
                            # below in post.always with fingerprint:true
                            # so the file survives even if the build
                            # record rotates out.
                            mkdir -p dist
                            {
                                echo "PYTHON_IMAGE=$(docker image inspect python:3.12-slim \
                                    --format '{{index .RepoDigests 0}}')"
                                echo "NODE_IMAGE=$(docker image inspect node:22.14.0-alpine \
                                    --format '{{index .RepoDigests 0}}')"
                                echo "HTTPD_IMAGE=$(docker image inspect httpd:2.4-alpine \
                                    --format '{{index .RepoDigests 0}}')"
                            } > dist/base-images.lock
                            cat dist/base-images.lock

                            # Fail loud if RepoDigests came back empty.
                            # The release pipeline silently consumes
                            # whatever this file contains and an empty
                            # value only surfaces several stages later
                            # as an opaque `docker build` failure.
                            if grep -E '^[A-Z_]+=$' dist/base-images.lock; then
                                echo "ERROR: empty digest(s) in" \
                                     "dist/base-images.lock — see" \
                                     "lines above. Refusing to" \
                                     "publish a poisoned lockfile." >&2
                                exit 1
                            fi
                        '''
                        script {
                            if (env.BRANCH_NAME == 'master') {
                                // `--password-stdin` keeps the secret out
                                // of the process list / shell trace. Use
                                // `printf '%s'` (not `echo`) so the
                                // password is sent byte-for-byte: echo
                                // appends a trailing newline and POSIX
                                // /bin/sh's echo also interprets backslash
                                // escapes — both can silently mangle a
                                // valid password into a 401. The trap
                                // ensures docker logout runs even if a
                                // push fails — agents are shared, don't
                                // leave registry auth lying around.
                                sh '''
                                    # #855: docker login/logout mutate a
                                    # shared per-user ~/.docker/config.json.
                                    # On a shared agent a concurrent job's
                                    # `docker logout` EXIT trap (e.g. the
                                    # release-pipeline registry preflight)
                                    # wipes our auth between two pushes —
                                    # master #5742: push :$BUILD_NUMBER OK,
                                    # push :$GIT_SHORT -> "no basic auth
                                    # credentials". Auth instance of the
                                    # tb-w8d race documented below. A
                                    # per-build DOCKER_CONFIG makes
                                    # login/logout build-local; scoped to
                                    # this sh (not the stage env) so the
                                    # base-image pulls above keep using the
                                    # default config.
                                    export DOCKER_CONFIG="$WORKSPACE/.docker-cfg-$BUILD_NUMBER"
                                    mkdir -p "$DOCKER_CONFIG"
                                    echo "REGISTRY_USER bytes: $(printf '%s' "$REGISTRY_USER" | wc -c)"
                                    echo "REGISTRY_PASS bytes: $(printf '%s' "$REGISTRY_PASS" | wc -c)"
                                    printf '%s' "$REGISTRY_PASS" | docker login \
                                        -u "$REGISTRY_USER" \
                                        --password-stdin "$REGISTRY"
                                    trap 'docker logout "$REGISTRY" || true; rm -rf "$DOCKER_CONFIG"' EXIT
                                    # tb-w8d: tag :latest INSIDE the loop,
                                    # immediately before pushing it. gain
                                    # build #137 hit a race where a bulk
                                    # docker tag :latest at the top of the
                                    # push block was followed ~30s later
                                    # by docker push :latest failing with
                                    # "tag does not exist", because a
                                    # concurrent process on the shared
                                    # Docker daemon had untagged :latest
                                    # in between. gpf has the same shape
                                    # with one extra repo (BUNDLE) — fix
                                    # preemptively.
                                    for repo in "$BACKEND_REPO" "$FRONTEND_REPO" "$BUNDLE_REPO"; do
                                        docker push "$repo:$BUILD_NUMBER"
                                        docker push "$repo:$GIT_SHORT"
                                        docker tag "$repo:$BUILD_NUMBER" "$repo:latest"
                                        docker push "$repo:latest"
                                    done
                                '''
                            } else {
                                echo "Skipping registry push: " +
                                     "branch is ${env.BRANCH_NAME}, not master"
                            }
                        }
                    }
                }

                // The integration suites run as separate downstream
                // jobs (gpf-federation-integration / gpf-rest-client-
                // integration) so the heavy backend stack is wired up
                // there, not in the per-project parallel stages.
                // Declarative-pipeline default behaviour skips these
                // triggers when a previous stage failed — so they only
                // fire when core + web_api pytest came out clean (UNSTABLE
                // from lint findings does NOT skip them, which is what
                // we want).
                //
                // The downstream jobs are materialised by the
                // `gpf-seed` pipeline (jenkins-jobs/Jenkinsfile.seed,
                // tracks master). `wait: false, propagate: false`
                // means an integration regression doesn't FAIL the
                // parent — but `build()` still throws synchronously if
                // the named job doesn't exist on the controller (e.g.
                // before seed has run for the first time, or on a
                // branch where the seed hasn't been re-run since
                // those .groovy files were added). `catchError` keeps
                // those bootstrap failures non-fatal: the parent build
                // logs the error and stays UNSTABLE.

                stage('Trigger web_e2e') {
                    when { not { environment name: 'DOCS_ONLY', value: 'true' } }
                    // Downstream gate for the gpf-web-e2e job (DSL at
                    // web_e2e/jenkins-jobs/e2e.groovy). Runs on every
                    // branch — the e2e job clones the same branch /
                    // commit and either pulls the prod images this
                    // pipeline just pushed (master only) or copies
                    // the wheel artefacts archived above
                    // (`dist/core/*.whl` + `dist/web_api/*.whl`) and
                    // builds the prod images locally.
                    steps {
                        catchError(
                            buildResult: 'UNSTABLE',
                            stageResult: 'UNSTABLE',
                            message:
                                'Could not trigger ' +
                                'gpf-web-e2e; has gpf-seed ' +
                                'materialised it yet?',
                        ) {
                            build(
                                job: '/gpf-web-e2e',
                                parameters: [
                                    string(
                                        name: 'BRANCH_NAME',
                                        value: env.BRANCH_NAME,
                                    ),
                                    string(
                                        name: 'COMMIT_SHA',
                                        value: env.GIT_COMMIT ?: '',
                                    ),
                                    string(
                                        name: 'UPSTREAM_PROJECT',
                                        value: env.JOB_NAME,
                                    ),
                                    string(
                                        name: 'UPSTREAM_BUILD',
                                        value: env.BUILD_NUMBER,
                                    ),
                                ],
                                wait: false,
                                propagate: false,
                            )
                        }
                    }
                }

                stage('Trigger federation integration') {
                    when { not { environment name: 'DOCS_ONLY', value: 'true' } }
                    steps {
                        catchError(
                            buildResult: 'UNSTABLE',
                            stageResult: 'UNSTABLE',
                            message:
                                'Could not trigger ' +
                                'gpf-federation-integration; has ' +
                                'gpf-seed materialised it yet?',
                        ) {
                            build(
                                job: '/gpf-federation-integration',
                                parameters: [
                                    string(
                                        name: 'BRANCH_NAME',
                                        value: env.BRANCH_NAME,
                                    ),
                                    string(
                                        name: 'COMMIT_SHA',
                                        value: env.GIT_COMMIT ?: '',
                                    ),
                                    string(
                                        name: 'UPSTREAM_PROJECT',
                                        value: env.JOB_NAME,
                                    ),
                                    string(
                                        name: 'UPSTREAM_BUILD',
                                        value: env.BUILD_NUMBER,
                                    ),
                                ],
                                wait: false,
                                propagate: false,
                            )
                        }
                    }
                }

                stage('Trigger rest_client integration') {
                    when { not { environment name: 'DOCS_ONLY', value: 'true' } }
                    steps {
                        catchError(
                            buildResult: 'UNSTABLE',
                            stageResult: 'UNSTABLE',
                            message:
                                'Could not trigger ' +
                                'gpf-rest-client-integration; has ' +
                                'gpf-seed materialised it yet?',
                        ) {
                            build(
                                job: '/gpf-rest-client-integration',
                                parameters: [
                                    string(
                                        name: 'BRANCH_NAME',
                                        value: env.BRANCH_NAME,
                                    ),
                                    string(
                                        name: 'COMMIT_SHA',
                                        value: env.GIT_COMMIT ?: '',
                                    ),
                                    string(
                                        name: 'UPSTREAM_PROJECT',
                                        value: env.JOB_NAME,
                                    ),
                                    string(
                                        name: 'UPSTREAM_BUILD',
                                        value: env.BUILD_NUMBER,
                                    ),
                                ],
                                wait: false,
                                propagate: false,
                            )
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
                        artifacts: 'dist/**/*.whl, dist/**/*.tar.gz, dist/conda/*.conda, dist/base-images.lock',
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
                for img in gpf-core-ci gpf-web-api-ci gpf-web-ui-ci gpf-federation-ci gpf-rest-client-ci gpf-conda-builder-ci; do
                    docker rmi "$img:${BUILD_NUMBER}" 2>/dev/null || true
                done
                # Registry-prefixed prod images. `:latest` only exists on
                # master but the rmi is harmless on branches. GIT_SHORT
                # may be unset if the build failed before that stage —
                # the rmi just no-ops then.
                for repo in registry.seqpipe.org/gpf-web-api \
                            registry.seqpipe.org/gpf-web-ui \
                            registry.seqpipe.org/gpf-web; do
                    for tag in "$BUILD_NUMBER" "${GIT_COMMIT:0:8}" latest; do
                        docker rmi "$repo:$tag" 2>/dev/null || true
                    done
                done
            '''
        }
    }
}
