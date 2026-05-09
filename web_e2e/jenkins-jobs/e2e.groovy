// Jenkins Job DSL definition for the gpf-web-e2e (Playwright)
// pipeline. Consumed by a seed job on the Jenkins controller;
// the script path below loads this repo's
// `web_e2e/Jenkinsfile.e2e` and runs it against the branch /
// commit passed as build parameters.
//
// The job is kicked off downstream from
// `iossifovlab/gpf/<branch>`'s `Trigger web_e2e` stage on
// every branch, after the parent build's `Build & push prod
// images` stage finishes. It can also be triggered manually
// from the Jenkins UI (defaults: gpf-gain-split, copy wheels
// from the last successful build of that branch).

// Declared at the Jenkins root (not under `iossifovlab/`):
// that path is a GitHub Organization Folder and rejects
// Job-DSL-managed children. Sibling of the `gpf-seed` seed
// job and of `gain-web-e2e`.
pipelineJob('gpf-web-e2e') {
    description(
        'End-to-end Playwright test suite for the gpf web ' +
        'stack. Builds the wheel-based backend production ' +
        'image (gpf-core + gpf-web) and the Apache-based ' +
        'frontend production image, brings up the full e2e ' +
        'compose stack (db + mail + backend-e2e + ' +
        'frontend-e2e), and runs `npx playwright test` ' +
        'against it. Triggered downstream of ' +
        'iossifovlab/gpf/<branch> after Build & push prod ' +
        'images; safe to run manually.')

    logRotator {
        numToKeep(20)
    }

    parameters {
        stringParam(
            'BRANCH_NAME',
            'gpf-gain-split',
            'Branch the upstream gpf build was triggered ' +
            'from. The pipeline checks out this branch ' +
            'unless COMMIT_SHA is set.',
        )
        stringParam(
            'COMMIT_SHA',
            '',
            'Specific commit SHA to test (takes precedence ' +
            'over BRANCH_NAME). Empty = use BRANCH_NAME HEAD.',
        )
        stringParam(
            'UPSTREAM_PROJECT',
            '',
            'Upstream Jenkins project name ' +
            '(e.g. iossifovlab/gpf/gpf-gain-split) the wheel ' +
            'artefacts are copied from. Empty = build the ' +
            'wheels from source instead.',
        )
        stringParam(
            'UPSTREAM_BUILD',
            '',
            'Upstream build number to copy wheel artefacts ' +
            'from. Empty = use the last successful build of ' +
            'UPSTREAM_PROJECT.',
        )
    }

    definition {
        cpsScm {
            scm {
                git {
                    remote {
                        url('https://github.com/iossifovlab/gpf.git')
                    }
                    // Single-quoted Groovy string so `${BRANCH_NAME}`
                    // is stored literally in the SCM config XML;
                    // Jenkins's git plugin expands it at checkout
                    // time using the BRANCH_NAME build parameter
                    // declared in the parameters{} block above. A
                    // branch trigger therefore loads Jenkinsfile.e2e
                    // from the same branch it tests, not from
                    // master — important when the pipeline
                    // definition lives on a non-master branch.
                    branch('${BRANCH_NAME}')
                }
            }
            scriptPath('web_e2e/Jenkinsfile.e2e')
            lightweight()
        }
    }
}
