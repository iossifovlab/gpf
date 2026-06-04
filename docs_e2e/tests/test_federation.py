"""Guide-claim tests for getting_started_with_federation.rst.

Federation needs a SECOND, remote GPF instance. The guide points the local
instance's ``remotes:`` block at the external SFARI instance; docs-e2e can't
depend on that, so the fixtures (conftest.py) stand up a hermetic LOCAL
stand-in remote and federate local clients with it over HTTP.

Authentication is the point of this suite. The remote runs as ``wdaemanage
runserver`` (NOT ``wgpf run`` — wgpf forces ``DISABLE_PERMISSIONS=True`` and
bypasses all auth), so it ENFORCES dataset permissions like SFARI. It serves
two demo studies — ``denovo_example`` made **public** (``any_user``) and
``vcf_example`` left **protected** (default ``any_dataset``) — plus a
client-credentials OAuth app standing in for a SFARI federation token. Two
clients federate with it:

* a **token-free** client (``remotes:`` without credentials) → the guide's
  public-access path: sees the public study, NOT the protected one;
* a **token** client (``remotes:`` with ``client_id``/``client_secret``) →
  the guide's Federation-tokens path: also sees the protected study.

Together the five tests prove our authentication works *as expected*: access
is granted with a token, denied without one, and public resources are
reachable token-free. (The old ``wgpf run`` remote silently faked all this by
disabling permissions.)

Carve-outs (documented in conftest): the ``remotes.url`` is local (vs SFARI),
and the federation token is created via ``wdaemanage createapplication``
rather than the SFARI UI — both invisible infrastructure we substitute. Out
of scope (non-hermetic, like the screenshots): the literal token-panel UI
steps. The remote-prefixing convention exposes a remote study on a client as
``<remote_config_id>_<study_id>`` (the remote config id is ``fed_remote``).

Each test maps to one discrete prose claim. ``rst_ref`` points at the line in
the guide source so a failure localizes the drift.
"""

from docs_e2e.guide_assertions import (
    assert_command_succeeds,
    assert_dataset_not_visible,
    assert_dataset_visible,
    assert_remote_dataset_resolves,
)

RST = "getting_started_with_federation.rst"

# Remote-prefixed study ids the clients expose (<remote_id>_<study>): the
# remote serves denovo_example (public) + vcf_example (protected).
_PUBLIC_REMOTE_STUDY = "fed_remote_denovo_example"
_PROTECTED_REMOTE_STUDY = "fed_remote_vcf_example"

# Cold budget: the client's first federated request resolves reference genome
# / gene models from the warm GRR cache and makes a hop (token clients also do
# the OAuth handshake) to the stand-in remote.
_COLD_PULL_TIMEOUT = 300


class TestFederationInstall:
    """RST lines 15-28: install the separate ``gpf-federation`` conda
    package into the local conda environment."""

    def test_gpf_federation_installs(self, federation_install):
        # RST lines 18-28: `mamba install ... gpf-federation` installs the
        # federation package the local (client) instance needs.
        assert_command_succeeds(
            federation_install.install,
            rst_ref=f"{RST}:19",
            expectation=(
                "installing the gpf-federation conda package succeeds"
            ),
        )


class TestPublicAccess:
    """RST lines 67-76: a token-free local instance accesses ONLY the publicly
    available resources of the remote."""

    def test_public_study_visible_without_token(
        self, federation_anon_client_server,
    ):
        # RST lines 72-76: the token-free configuration lets the local
        # instance access the remote's publicly available resources. The
        # public study (granted any_user on the remote) appears in the
        # token-free client's visible datasets.
        resp = federation_anon_client_server.client.get(
            "/api/v3/datasets/visible",
            timeout=_COLD_PULL_TIMEOUT,
        )
        assert_dataset_visible(
            resp, _PUBLIC_REMOTE_STUDY,
            rst_ref=f"{RST}:74",
            expectation=(
                "a token-free local instance can access the remote's publicly "
                "available study"
            ),
        )

    def test_protected_study_hidden_without_token(
        self, federation_anon_client_server,
    ):
        # RST lines 72-76 ("ONLY the publicly available resources"): a
        # protected remote study must NOT appear to a token-free client. This
        # is the negative that makes the auth test meaningful — an
        # auth-bypassing remote (wgpf run) would leak it.
        resp = federation_anon_client_server.client.get(
            "/api/v3/datasets/visible",
            timeout=_COLD_PULL_TIMEOUT,
        )
        assert_dataset_not_visible(
            resp, _PROTECTED_REMOTE_STUDY,
            rst_ref=f"{RST}:74",
            expectation=(
                "a token-free local instance accesses ONLY public resources — "
                "the remote's protected study stays hidden (auth enforced)"
            ),
        )


class TestTokenAccess:
    """RST lines 134-178: with a federation token (client_id/secret) the local
    instance accesses the resources it has access to on the remote."""

    def test_protected_study_visible_with_token(
        self, federation_auth_client_server,
    ):
        # RST lines 155-171: adding the federation client_id/client_secret to
        # the remotes block grants access to the resources the account can see
        # — including the protected study the token-free client could not.
        resp = federation_auth_client_server.client.get(
            "/api/v3/datasets/visible",
            timeout=_COLD_PULL_TIMEOUT,
        )
        assert_dataset_visible(
            resp, _PROTECTED_REMOTE_STUDY,
            rst_ref=f"{RST}:170",
            expectation=(
                "a client configured with a federation token can access the "
                "remote's protected study"
            ),
        )

    def test_protected_study_resolves_with_token(
        self, federation_auth_client_server,
    ):
        # RST lines 103-108 + 170: the authenticated client can actually use
        # the remote study — resolving its details through the client proves
        # the federation link works end-to-end (authenticated REST to the
        # remote), not just that the id was listed.
        resp = federation_auth_client_server.client.get(
            f"/api/v3/datasets/{_PROTECTED_REMOTE_STUDY}",
            timeout=_COLD_PULL_TIMEOUT,
        )
        assert_remote_dataset_resolves(
            resp, _PROTECTED_REMOTE_STUDY,
            rst_ref=f"{RST}:170",
            expectation=(
                "the protected remote study resolves through the token client"
            ),
        )
