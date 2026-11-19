// Jenkins Job DSL definition for the gpf-python-matrix job.
// Materialised by the inline `Apply Job DSL` stage in the root
// Jenkinsfile (master branch); the script path below loads this
// repo's matrix pipeline. Modelled on gain's
// jenkins-jobs/python_matrix.groovy.
//
// The matrix re-runs the pytest suites of gpf-core and gpf-web
// under Python 3.12, 3.13 and 3.14 to catch forward-compatibility
// breakage on newer interpreters before migration time.
// Triggered nightly from the gpf-nightly orchestrator with
// BRANCH_NAME master; can also be run on demand against a branch.
// The job tests the head of BRANCH_NAME, not a pinned commit.
//
// gpf-nightly calls this job beside the dory deploy, with
// `propagate: false` (iossifovlab/gain#2385, decision 5): a red
// matrix does not block the nightly deploy on dory. The job
// therefore sends its own Zulip alert on a failed, unstable or
// aborted run (topic: nightly), the same topic as the
// orchestrator. The job aborts a run after 2 hours.
//
// First-run note: after `Apply Job DSL` applies this file, a
// Jenkins admin may need to approve the script under
// Manage Jenkins → In-process Script Approval.

// Declared at the Jenkins root (not under `iossifovlab/`): that
// path is a GitHub Organization Folder and rejects Job-DSL-managed
// children. Sibling of `gpf-nightly`, `gpf-federation-integration`
// and `gpf-rest-client-integration`.
pipelineJob('gpf-python-matrix') {
    description(
        'Pytest matrix across Python 3.12/3.13/3.14 for gpf-core ' +
        'and gpf-web. Forward-compatibility canary for the ' +
        'dependency closure. Triggered nightly via gpf-nightly ' +
        'beside the dory deploy, so its result never gates that ' +
        'deploy. Aborts a run after 2 hours. Sends a Zulip alert ' +
        'on a failed, unstable or aborted run (topic: nightly).')

    logRotator {
        numToKeep(40)
    }

    parameters {
        stringParam(
            'BRANCH_NAME',
            'master',
            'Branch to load the matrix pipeline from and test. ' +
            'Default master is what the gpf-nightly trigger runs.',
        )
    }

    definition {
        cpsScm {
            scm {
                git {
                    remote {
                        url('https://github.com/iossifovlab/gpf.git')
                    }
                    // Single-quoted Groovy string so `${BRANCH_NAME}` is
                    // stored literally in the SCM config XML; Jenkins's git
                    // plugin expands it at checkout time from the
                    // BRANCH_NAME build parameter declared above. A manual
                    // run against a branch therefore loads the pipeline
                    // script from that branch and tests that branch.
                    branch('${BRANCH_NAME}')
                }
            }
            scriptPath('Jenkinsfile.python-matrix')
            lightweight()
        }
    }
}
