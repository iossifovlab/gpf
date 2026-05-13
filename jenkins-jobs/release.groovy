// Jenkins Job DSL definition for the gpf-release pipeline.
// Materialised by the inline `Apply Job DSL` stage in the root
// Jenkinsfile (master branch); the script path below loads this
// repo's `Jenkinsfile.release` and runs it against the tag passed
// as the TAG_NAME parameter.
//
// The job is kicked off downstream from the root multibranch's
// `Dispatch release` stage when a CalVer tag (^\d{4}\.\d+\.\d+$)
// lands. It can also be triggered manually from the Jenkins UI
// (e.g. to retry a release after a transient publish failure).

// Declared at the Jenkins root (not under `iossifovlab/`): that
// path is a GitHub Organization Folder and rejects Job-DSL-managed
// children. Sibling of `gpf-nightly`, `gpf-federation-integration`,
// `gpf-rest-client-integration`, `gpf-web-e2e`, and
// `gpf-deploy-dory`.
pipelineJob('gpf-release') {
    description(
        'Tag-driven release pipeline for the gpf monorepo. ' +
        'Builds wheels, sdists, conda packages, and digest-pinned ' +
        'production Docker images (backend + frontend + bundle) ' +
        'for a CalVer tag, then publishes to wheels.seqpipe.org, ' +
        'anaconda.org/iossifovlab, and registry.seqpipe.org. ' +
        'Triggered downstream of iossifovlab/gpf/<tag> after the ' +
        'dispatcher fires; safe to run manually with TAG_NAME set ' +
        'to the tag to release.')

    logRotator {
        numToKeep(40)
    }

    parameters {
        stringParam(
            'TAG_NAME',
            '',
            'CalVer tag to release (e.g. 2026.5.13). Must match ' +
            '^\\d{4}\\.\\d+\\.\\d+$. Pre-release suffixes are ' +
            'deferred to V2.',
        )
        stringParam(
            'UPSTREAM_PROJECT',
            'iossifovlab/gpf/master',
            'Multibranch path used to locate the master CI build ' +
            'whose GIT_COMMIT matches the tagged commit. Override ' +
            'only if the multibranch folder layout has changed.',
        )
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
            // Jenkinsfile.release is loaded from master tip so
            // pipeline fixes (typos, credential renames, etc.) can
            // ship without retagging. The pipeline itself does an
            // explicit `checkout refs/tags/${TAG_NAME}` for the
            // workspace so hatch-vcs / Dockerfiles / recipes match
            // the tagged commit.
            scriptPath('Jenkinsfile.release')
            lightweight()
        }
    }
}
