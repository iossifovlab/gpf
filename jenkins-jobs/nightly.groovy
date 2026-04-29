// Jenkins Job DSL definition for the gpf-nightly orchestrator.
// Materialised by the inline `Apply Job DSL` stage in the root
// Jenkinsfile (master branch); the script path below loads this
// repo's `Jenkinsfile.nightly`.
//
// The job is cron-triggered (~02:00 UTC) and rebuilds master plus
// the integration suites (gpf-federation-integration +
// gpf-rest-client-integration) unconditionally. The cron schedule
// + Zulip-on-failure live in Jenkinsfile.nightly, not here.

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
