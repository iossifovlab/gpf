"""Assertion helpers for docs-e2e guide-claim tests.

Each helper takes an ``rst_ref`` (file:line in the Getting Started
RST source) and a paraphrased ``expectation``. On failure, raises
AssertionError with a uniform message that includes the rst ref,
the expectation, the actual response, and a triage hint that helps
disambiguate guide drift from a real code regression.

Pure Python. No httpx, no gpf, no pytest imports. HTTP responses
are duck-typed (anything with ``.status_code`` and ``.json()``);
subprocess results are duck-typed (anything with ``.returncode``,
``.args``, ``.stdout``, ``.stderr``).
"""

import shlex
from pathlib import Path


_TAIL_LINES = 20


def _format_args(args):
    if isinstance(args, str):
        return args
    return shlex.join(str(a) for a in args)


def _tail(text, n=_TAIL_LINES):
    if text is None:
        return ""
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")
    lines = text.splitlines()
    return "\n".join("    " + line for line in lines[-n:])


def assert_command_succeeds(result, *, rst_ref, expectation):
    """Assert that ``result`` is a successful subprocess completion.

    On failure, the AssertionError carries the rst ref, paraphrased
    expectation, the failing command line, exit code, tails of
    stdout/stderr, and a triage hint pointing at the most likely
    failure mode (guide drift vs. code regression).
    """
    if result.returncode == 0:
        return
    message = (
        f'DRIFT at {rst_ref} — "{expectation}"\n'
        f"\n"
        f"  command:  {_format_args(result.args)}\n"
        f"  expected: exit code 0\n"
        f"  actual:   exit code {result.returncode}\n"
        f"\n"
        f"  stdout (last {_TAIL_LINES} lines):\n{_tail(result.stdout)}\n"
        f"\n"
        f"  stderr (last {_TAIL_LINES} lines):\n{_tail(result.stderr)}\n"
        f"\n"
        f"  Triage hint: Command exited non-zero. Most likely guide "
        f"drift — check if a CLI flag changed, a prerequisite step "
        f"is missing, or the binary was removed/renamed. Less likely "
        f"a regression in the binary itself."
    )
    raise AssertionError(message)


def _http_failure_message(
        response, *, rst_ref, expectation, what_was_expected,
):
    body_tail = _tail(getattr(response, "text", "") or "")
    return (
        f'DRIFT at {rst_ref} — "{expectation}"\n'
        f"\n"
        f"  expected: {what_was_expected}\n"
        f"  actual:   HTTP {response.status_code} from the backend\n"
        f"\n"
        f"  response body (last {_TAIL_LINES} lines):\n{body_tail}\n"
        f"\n"
        f"  Triage hint: The backend returned an error response. "
        f"Most likely a server-side regression (5xx) or a missing "
        f"endpoint / changed URL (404). The guide claim cannot be "
        f"evaluated until the server responds successfully. Check "
        f"the wgpf log dump in the artefacts for the underlying "
        f"exception."
    )


def assert_dataset_visible(response, dataset_id, *, rst_ref, expectation):
    """Assert ``dataset_id`` appears in ``/api/v3/datasets/visible``.

    The response is expected to be a JSON list of objects each
    carrying an ``id`` field. A non-200 status, a non-JSON body, or
    an id missing from the list each raise AssertionError with a
    triage-aware diagnostic.
    """
    if response.status_code != 200:
        raise AssertionError(_http_failure_message(
            response,
            rst_ref=rst_ref,
            expectation=expectation,
            what_was_expected=(
                f"HTTP 200 with dataset '{dataset_id}' in the visible list"
            ),
        ))
    data = response.json()
    visible_ids = [item.get("id") for item in data if isinstance(item, dict)]
    if dataset_id in visible_ids:
        return
    visible_list = ", ".join(repr(i) for i in visible_ids) or "(none)"
    message = (
        f'DRIFT at {rst_ref} — "{expectation}"\n'
        f"\n"
        f"  expected: dataset id {dataset_id!r} in the visible list\n"
        f"  actual:   visible ids = [{visible_list}]\n"
        f"\n"
        f"  Triage hint: The backend responded but {dataset_id!r} is "
        f"not in its visible-dataset list. Likely either (a) the "
        f"prior import step did not register the dataset (re-check "
        f"its exit code + stdout), or (b) the dataset id in the "
        f"guide drifted away from what the import config produces. "
        f"If the import succeeded and the new id is in the visible "
        f"list, update the guide to match."
    )
    raise AssertionError(message)


def assert_query_returned_variants(
        response, *, min_count=1, rst_ref, expectation,
):
    """Assert a genotype-browser query returned at least ``min_count``
    variants.

    The response body is expected to decode as a JSON list of
    variant records. A non-200 status fails with HTTP-error
    triage; fewer than ``min_count`` variants fails with a hint
    pointing at the prior import step or the query filter.
    """
    if response.status_code != 200:
        raise AssertionError(_http_failure_message(
            response,
            rst_ref=rst_ref,
            expectation=expectation,
            what_was_expected=(
                f"HTTP 200 with at least {min_count} variant(s)"
            ),
        ))
    variants = response.json()
    count = len(variants)
    if count >= min_count:
        return
    message = (
        f'DRIFT at {rst_ref} — "{expectation}"\n'
        f"\n"
        f"  expected: at least {min_count} variant(s) returned\n"
        f"  actual:   {count} variant(s)\n"
        f"\n"
        f"  Triage hint: The backend responded but the variant "
        f"count is below expectation. Most likely either (a) the "
        f"upstream import step did not load the variants the guide "
        f"claims it would (re-check its exit code and the resulting "
        f"study layout under internal_storage/), or (b) the query "
        f"filter in the test does not match what the guide screenshot "
        f"used. If the new count is correct, update the guide."
    )
    raise AssertionError(message)


def assert_file_created(path, *, rst_ref, expectation, after_command=None):
    """Assert that ``path`` exists on disk.

    ``after_command`` is the subprocess.CompletedProcess of the
    step the guide says creates this file. When supplied, its
    success/failure shapes the triage hint:

    * If the prior command failed, the file absence is downstream
      — the hint redirects to fixing the prior failure first, and
      surfaces the prior step's stderr.
    * If the prior command succeeded (or is omitted), the absence
      is the actual signal: code/import-behavior drift, the file
      may have been renamed or moved, or the guide may name a
      stale path.
    """
    path = Path(path)
    if path.exists():
        return

    prior_failed = (
        after_command is not None and after_command.returncode != 0
    )

    if prior_failed:
        triage = (
            f"Triage hint: Prior command failed (exit code "
            f"{after_command.returncode}). Fix that first — the "
            f"missing file is downstream of that failure."
        )
        prior_block = (
            f"\n  prior command: {_format_args(after_command.args)}\n"
            f"  prior exit:    exit code {after_command.returncode}\n"
            f"\n  prior stderr (last {_TAIL_LINES} lines):\n"
            f"{_tail(after_command.stderr)}\n"
        )
    else:
        triage = (
            "Triage hint: Prior step succeeded but the expected file "
            "is absent. Most likely a code regression or import-"
            "behavior change — the file may have been renamed, moved, "
            "or the output layout changed. If the guide names a stale "
            "path, update the guide."
        )
        prior_block = ""

    message = (
        f'DRIFT at {rst_ref} — "{expectation}"\n'
        f"\n"
        f"  expected file: {path}\n"
        f"  actual:        does not exist"
        f"{prior_block}"
        f"\n"
        f"  {triage}"
    )
    raise AssertionError(message)
