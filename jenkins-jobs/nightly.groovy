// Jenkins Job DSL definition for the gpf-nightly orchestrator.
// Materialised by the inline `Apply Job DSL` stage in the root
// Jenkinsfile (master branch); the script path below loads this
// repo's `Jenkinsfile.nightly`.
//
// The job is cron-triggered (~02:00 UTC) and rebuilds master plus
// the integration suites (gpf-federation-integration +
// gpf-rest-client-integration) unconditionally.
//
// tb-7e7: cron MUST live in this DSL, not in Jenkinsfile.nightly.
// The seed re-applies the DSL on every master push (gpf-seed runs
// often) and that overwrites the job config — wiping any cron
// trigger that the Jenkinsfile registered on its previous run.
// Result was 1 manual build and zero cron-fired builds for
// gpf-nightly. Putting the cron here means each seed re-applies
// it explicitly. Zulip-on-failure stays in the Jenkinsfile (it's
// pipeline logic, not job config).

// Declared at the Jenkins root (not under `iossifovlab/`): that
// path is a GitHub Organization Folder and rejects Job-DSL-managed
// children. Sibling of `gpf-federation-integration` and
// `gpf-rest-client-integration`.
pipelineJob('gpf-nightly') {
    description(
        'Cron-scheduled orchestrator that rebuilds master from ' +
        'scratch and re-runs gpf-federation-integration + ' +
        'gpf-rest-client-integration unconditionally. Catches ' +
        'dependency drift / silently-stale caches on quiet days. ' +
        'Sends a Zulip alert on failure (topic: nightly).')

    logRotator {
        numToKeep(40)
    }

    triggers {
        // H hashes on the job name so the minute is stable per job
        // but spread across other nightlies on the controller.
        cron('H 2 * * *')
    }

    definition {
        cpsScm {
            scm {
                git {
                    remote {
                        url('https://github.com/iossifovlab/gpf.git')
                    }
                    branch('master')
                }
            }
            scriptPath('Jenkinsfile.nightly')
            lightweight()
        }
    }
}
