"""Create (or update) a GitHub Release for a gpf CalVer tag.

Invoked by the `Publish GitHub release` stage of `Jenkinsfile.release`
after all artifacts (wheels, conda, registry + Docker Hub images) have
been published. The release is a human-facing landing page, NOT an
artifact store: the body links to the existing distribution channels
rather than re-uploading anything.

Behaviour:
  - Extracts the release notes for ``--tag`` from the version-keyed
    ``changes.rst`` (the ``* <version>`` block) and renders them as
    markdown.
  - Appends an Install section (public Docker image, wheels index,
    anaconda) plus the bundled gain version.
  - Upserts via the REST API: GET the release by tag, PATCH if it
    already exists, otherwise POST. This mirrors the idempotent
    re-push semantics of the rest of the release pipeline, so a manual
    re-run of gpf-release is safe.
  - Falls back to a minimal body if changes.rst has no section for the
    tag (does not fail — a missing changelog entry should not block).

Auth: the token is read from the ``GH_TOKEN`` environment variable
(never passed on argv, which is visible in the process list). It needs
``Contents: write`` on the target repo — that permission scope covers
Releases.

Stdlib only (urllib/json/re) so it runs in the conda-builder container
without extra deps. Use ``--dry-run`` to print the rendered body and
the action it would take without calling the API (and without a token).
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

API_VERSION = "2022-11-28"


def extract_notes(changes_text: str, version: str) -> str:
    """Return the markdown notes for ``version`` from changes.rst.

    changes.rst is a flat bullet list keyed by ``* <version>`` headers
    (no leading indent), with 4-space-indented ``* `` bullets beneath
    each and 6-space (or deeper) continuation lines wrapping long
    bullets. Nested bullets are indented a further 4 spaces.

    Returns an empty string if the version has no section.
    """
    block: list[str] = []
    capturing = False
    for line in changes_text.splitlines():
        header = re.match(r"^\* (\S+)\s*$", line)
        if header:
            if capturing:
                break  # reached the next version → done
            capturing = header.group(1) == version
            continue
        if capturing:
            block.append(line)

    # Trim leading/trailing blank lines.
    while block and not block[0].strip():
        block.pop(0)
    while block and not block[-1].strip():
        block.pop()

    # Normalise indentation to the shallowest bullet so top-level
    # changelog bullets render as markdown level 0 (`- `) rather than
    # an over-indented nested list. changes.rst puts top-level bullets
    # at 4 spaces; deeper bullets (e.g. the 2026.4.1 renames) sit 4
    # spaces further in per level.
    indents = [
        len(m.group(1))
        for line in block
        if (m := re.match(r"^( *)\* ", line))
    ]
    base = min(indents) if indents else 0

    md: list[str] = []
    for line in block:
        bullet = re.match(r"^( *)\* (.*)$", line)
        if bullet:
            level = (len(bullet.group(1)) - base) // 4
            md.append("  " * level + "- " + bullet.group(2).strip())
        elif line.strip():
            # Continuation of the previous bullet's wrapped text.
            if md:
                md[-1] += " " + line.strip()
            else:
                md.append(line.strip())
    return "\n".join(md).strip()


def build_body(notes: str, opts: argparse.Namespace) -> str:
    """Assemble the release body: notes + an Install section."""
    parts = [notes] if notes else [f"Release {opts.tag}."]
    install = [
        "",
        "## Install",
        "",
        "Public Docker image (runs GPF standalone):",
        "",
        "```",
        f"docker pull {opts.dockerhub_image}:{opts.tag}",
        "```",
        "",
        f"- Wheels: {opts.wheels_url}",
        f"- Conda: {opts.anaconda}",
    ]
    if opts.gain_version:
        install.append(f"- Bundled gain: `{opts.gain_version}`")
    parts.append("\n".join(install))
    return "\n".join(parts).strip() + "\n"


def _api(
    method: str,
    url: str,
    token: str,
    payload: dict | None = None,
) -> tuple[int, dict]:
    # URL is always a hardcoded https://api.github.com/... base built
    # below, never user-controlled, so the scheme audit is moot here.
    req = urllib.request.Request(url, method=method)  # noqa: S310
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", API_VERSION)
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data) as resp:  # noqa: S310
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as err:
        try:
            body = json.load(err)
        except (ValueError, OSError):
            body = {"message": err.reason}
        return err.code, body


def upsert_release(opts: argparse.Namespace, body: str, token: str) -> str:
    """Create or update the release; return its html_url."""
    base = f"https://api.github.com/repos/{opts.repo}/releases"
    payload = {
        "tag_name": opts.tag,
        "name": opts.tag,
        "body": body,
        "draft": False,
        "prerelease": False,
        "make_latest": "true",
    }

    status, existing = _api("GET", f"{base}/tags/{opts.tag}", token)
    if status == 200:
        rid = existing["id"]
        st, result = _api("PATCH", f"{base}/{rid}", token, payload)
        action = "updated"
    elif status == 404:
        st, result = _api("POST", base, token, payload)
        action = "created"
    else:
        raise SystemExit(
            f"GitHub API error probing release {opts.tag}: "
            f"HTTP {status} — {existing.get('message')}",
        )

    if st not in (200, 201):
        raise SystemExit(
            f"GitHub API error ({action}) for {opts.tag}: "
            f"HTTP {st} — {result.get('message')}",
        )
    print(f"GitHub release {action}: {result['html_url']}")
    return result["html_url"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tag", required=True, help="CalVer tag, e.g. 2026.6.0",
    )
    parser.add_argument("--repo", default="iossifovlab/gpf")
    parser.add_argument(
        "--changes",
        default="docs/source/development/changes.rst",
        help="Path to the version-keyed changes.rst",
    )
    parser.add_argument("--gain-version", default="")
    parser.add_argument("--dockerhub-image", default="iossifovlab/gpf-web")
    parser.add_argument(
        "--wheels-url", default="https://wheels.seqpipe.org/gpf/",
    )
    parser.add_argument(
        "--anaconda", default="https://anaconda.org/iossifovlab",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the rendered body + intended action; no API call.",
    )
    opts = parser.parse_args(argv)

    try:
        changes_text = pathlib.Path(opts.changes).read_text(encoding="utf-8")
    except OSError as err:
        print(
            f"WARNING: could not read {opts.changes}: {err}",
            file=sys.stderr,
        )
        changes_text = ""

    notes = extract_notes(changes_text, opts.tag)
    if not notes:
        print(
            f"WARNING: no changes.rst section for {opts.tag}; "
            "using a minimal body.",
            file=sys.stderr,
        )
    body = build_body(notes, opts)

    if opts.dry_run:
        print(f"--- DRY RUN: would upsert {opts.tag} on {opts.repo} ---")
        print(body)
        return 0

    token = os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("GH_TOKEN environment variable is required.")
    upsert_release(opts, body, token)
    return 0


if __name__ == "__main__":
    sys.exit(main())
