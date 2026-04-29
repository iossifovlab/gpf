// Jenkins Job DSL definition for the gpf-federation-integration
// pipeline. Consumed by a seed job on the Jenkins controller; the
// script path below loads this repo's
// `federation/Jenkinsfile.integration` and runs it against the branch
// / commit passed as build parameters.
//
// The job is kicked off downstream from
// `iossifovlab/gpf/<branch>`'s `Trigger federation integration`
// stage on every branch where the upstream `Sub-projects` parallel
// stage finished successfully (i.e. core + web tests passed). It can
// also be triggered manually from the Jenkins UI (defaults: master).

pipelineJob('gpf-federation-integration') {
    description(
        'Integration tests for gpf-federation against a live ' +
        'gpf-web backend. Brings up a backend container with a ' +
        'seeded t4c8 GPF instance and runs the federation pytest ' +
        'suite against it. Triggered downstream of ' +
        'iossifovlab/gpf/<branch> after Sub-projects; safe to ' +
        'run manually.')

    logRotator {
        numToKeep(20)
    }

    parameters {
        stringParam(
            'BRANCH_NAME',
            'master',
            'Branch the upstream gpf build was triggered from. ' +
            'The pipeline checks out this branch unless ' +
            'COMMIT_SHA is set.',
        )
        stringParam(
            'COMMIT_SHA',
            '',
            'Specific commit SHA to test (takes precedence over ' +
            'BRANCH_NAME). Empty = use BRANCH_NAME HEAD.',
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
                    // (defaults to `master` per the parameters{}
                    // block above). A branch trigger therefore loads
                    // Jenkinsfile.integration from the same branch
                    // it tests, not from master — important when the
                    // pipeline definition lives on a non-master
                    // branch.
                    branch('${BRANCH_NAME}')
                }
            }
            scriptPath('federation/Jenkinsfile.integration')
            lightweight()
        }
    }
}
