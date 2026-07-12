// pipelineJob DSL for gpf-docs-e2e-prewarm. Seeded by the main gpf
// Jenkinsfile's `Apply Job DSL` stage (which targets
// **/jenkins-jobs/*.groovy on master). Sibling of docs_e2e.groovy.
//
// NOTE: the filename uses underscores (docs_e2e_prewarm.groovy), not
// dashes — Apply Job DSL requires script filenames to be valid Groovy
// identifiers (^[A-Za-z_][A-Za-z0-9_]*\.groovy$); a dash silently
// breaks the seed job.
//
// This job pre-caches the ~15 GB of GRR instance resources onto a
// chosen agent's node-local gpf-grr-cache volume, so the
// gpf-docs-e2e build's in-suite grr_cache_repo step runs warm. Run
// it once per agent that will run gpf-docs-e2e — see
// docs_e2e/README.md § Onboarding an agent and iossifovlab/gpf#876.

pipelineJob('gpf-docs-e2e-prewarm') {
    description(
        'One-time per-agent seeding of the gpf-grr-cache volume for ' +
        'docs-e2e (grr_cache_repo bulk-pulls ~15 GB). Run once per ' +
        'agent. See docs_e2e/README.md § Onboarding an agent and ' +
        'iossifovlab/gpf#876.',
    )

    parameters {
        stringParam(
            'AGENT_LABEL', 'pooh',
            'The specific agent to seed. Must match the agent ' +
            'gpf-docs-e2e runs on (its AGENT_LABEL default is also ' +
            '"pooh") — the gpf-grr-cache volume is node-local. ' +
            'Set a different concrete name to seed another agent.',
        )
        stringParam(
            'GETTING_STARTED_REF', 'master',
            'Branch/tag of iossifovlab/gpf-getting-started to ' +
            'derive the instance config (resource set) from.',
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
                    extensions {
                        cloneOptions {
                            shallow(true)
                            noTags(true)
                            depth(1)
                        }
                    }
                }
            }
            scriptPath('docs_e2e/Jenkinsfile.docs-e2e-prewarm')
            lightweight(true)
        }
    }
}
