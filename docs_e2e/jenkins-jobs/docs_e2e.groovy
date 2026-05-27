// pipelineJob DSL for gpf-docs-e2e. Seeded by the main gpf
// Jenkinsfile's `Apply Job DSL` stage (which targets
// **/jenkins-jobs/*.groovy on master). Matches the shape of
// web_e2e/jenkins-jobs/e2e.groovy so anyone who can read one
// can read the other.

pipelineJob('gpf-docs-e2e') {
    description(
        'docs-e2e — guide-accuracy regression for the GPF Getting ' +
        'Started Guide. See docs_e2e/README.md and ' +
        'iossifovlab/gpf#871 for the full design.',
    )

    parameters {
        stringParam(
            'BRANCH_NAME', 'master',
            'Branch the upstream gpf build was triggered from. ' +
            'The pipeline checks out this branch unless ' +
            'COMMIT_SHA is set.',
        )
        stringParam(
            'COMMIT_SHA', '',
            'Specific commit SHA to test (takes precedence over ' +
            'BRANCH_NAME). Empty = use BRANCH_NAME HEAD.',
        )
        stringParam(
            'UPSTREAM_PROJECT', '',
            'Upstream Jenkins project (e.g. iossifovlab/gpf/master) ' +
            'the conda artefacts are copied from. Empty = fall ' +
            'back to iossifovlab/gpf/master lastSuccessful().',
        )
        stringParam(
            'UPSTREAM_BUILD', '',
            'Upstream build number to copy conda artefacts from. ' +
            'Empty = use lastSuccessful() of UPSTREAM_PROJECT.',
        )
        stringParam(
            'STAGE_FILTER', '',
            'Optional pytest -k expression to narrow which test ' +
            'files run. Empty = run all stages.',
        )
    }

    properties {
        // Branch builds may queue while master is mid-run. Build
        // discarder is set in the Jenkinsfile (numToKeepStr: 20).
        disableConcurrentBuilds(abortPrevious: false)
    }

    definition {
        cpsScm {
            scm {
                git {
                    remote {
                        url('https://github.com/iossifovlab/gpf.git')
                    }
                    // The Jenkinsfile's Checkout stage re-checks out
                    // the requested BRANCH_NAME/COMMIT_SHA — this
                    // initial checkout just gets the Jenkinsfile
                    // itself.
                    branch('master')
                    extensions {
                        cloneOptions {
                            shallow(true)
                            noTags(true)
                            depth(1)
                        }
                    }
                }
            }
            scriptPath('docs_e2e/Jenkinsfile.docs-e2e')
            lightweight(true)
        }
    }
}
