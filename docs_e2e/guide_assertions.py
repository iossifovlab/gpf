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
    # /api/v3/datasets/visible returns a JSON list of dataset-id
    # *strings* (e.g. ["denovo_example", "vcf_example"]). Tolerate
    # a list of {"id": ...} dicts too, in case a caller passes a
    # response from a richer datasets endpoint.
    visible_ids = [
        item if isinstance(item, str)
        else item.get("id") if isinstance(item, dict)
        else None
        for item in data
    ]
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


def _parse_tsv_header(response):
    """Return the tab-separated header fields of a download response."""
    text = getattr(response, "text", "") or ""
    lines = text.splitlines()
    if not lines:
        return []
    return lines[0].split("\t")


def assert_download_has_columns(response, columns, *, rst_ref, expectation):
    """Assert the genotype-browser download TSV header contains each
    of ``columns``.

    Backs the annotation guide's claim that the additional attributes
    produced by annotation (``gnomad_v4_genome_ALL_af``, ``CLNSIG``,
    ``CLNDN``) are included in the downloaded variants file. A non-200
    status fails with HTTP-error triage; a missing column fails with a
    hint pointing at the annotation config / re-annotation step.
    """
    if response.status_code != 200:
        raise AssertionError(_http_failure_message(
            response,
            rst_ref=rst_ref,
            expectation=expectation,
            what_was_expected=(
                f"HTTP 200 with a TSV header containing {columns}"
            ),
        ))
    header = _parse_tsv_header(response)
    missing = [c for c in columns if c not in header]
    if not missing:
        return
    message = (
        f'DRIFT at {rst_ref} — "{expectation}"\n'
        f"\n"
        f"  expected columns: {', '.join(columns)}\n"
        f"  missing:          {', '.join(missing)}\n"
        f"  actual header:    {', '.join(header)}\n"
        f"\n"
        f"  Triage hint: The download succeeded but an expected "
        f"annotation column is absent. Most likely either (a) the "
        f"annotation config in gpf_instance.yaml did not take effect "
        f"(re-check that `wgpf run` re-annotated — the wgpf log dump "
        f"in the artefacts shows the configured annotators), or (b) "
        f"the annotator's output attribute was renamed. If the new "
        f"column name is correct, update the guide."
    )
    raise AssertionError(message)


def assert_download_trailing_columns(
        response, columns, *, rst_ref, expectation,
):
    """Assert the final columns of the download TSV header are exactly
    ``columns`` (order-insensitive among themselves).

    Backs the guide's claim that annotation attributes are appended
    "as the last columns in the downloaded file". The inter-order of
    the trailing columns is not asserted — the guide makes no claim
    about it and it is cosmetic.
    """
    if response.status_code != 200:
        raise AssertionError(_http_failure_message(
            response,
            rst_ref=rst_ref,
            expectation=expectation,
            what_was_expected=(
                f"HTTP 200 with {columns} as the trailing TSV columns"
            ),
        ))
    header = _parse_tsv_header(response)
    trailing = header[-len(columns):]
    if set(trailing) == set(columns):
        return
    message = (
        f'DRIFT at {rst_ref} — "{expectation}"\n'
        f"\n"
        f"  expected last {len(columns)} columns: "
        f"{', '.join(sorted(columns))}\n"
        f"  actual last {len(columns)} columns:   "
        f"{', '.join(trailing)}\n"
        f"  full header:    {', '.join(header)}\n"
        f"\n"
        f"  Triage hint: The annotation attributes are not the trailing "
        f"block of the download. Either a column was appended after them "
        f"(layout changed) or one of the expected attributes is missing. "
        f"If the layout legitimately changed, update the guide's claim "
        f"that they are the last columns."
    )
    raise AssertionError(message)


def _score_id(item):
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return item.get("score") or item.get("id") or item.get("name")
    return None


def assert_genomic_score_available(
        response, score_id, *, rst_ref, expectation,
):
    """Assert ``score_id`` appears in the instance's genomic-scores
    registry (``/api/v3/genomic_scores/``).

    Backs the guide's claim that annotation attributes are usable as
    genomic-score query filters. The response is a JSON list of score
    descriptor dicts each carrying a ``score`` field; a list of bare
    id strings is tolerated too.
    """
    if response.status_code != 200:
        raise AssertionError(_http_failure_message(
            response,
            rst_ref=rst_ref,
            expectation=expectation,
            what_was_expected=(
                f"HTTP 200 with '{score_id}' among the genomic scores"
            ),
        ))
    score_ids = [_score_id(item) for item in response.json()]
    if score_id in score_ids:
        return
    available = ", ".join(repr(s) for s in score_ids) or "(none)"
    message = (
        f'DRIFT at {rst_ref} — "{expectation}"\n'
        f"\n"
        f"  expected genomic score: {score_id!r}\n"
        f"  available scores:       [{available}]\n"
        f"\n"
        f"  Triage hint: The score is not registered as a queryable "
        f"genomic score. Most likely the annotation that produces it is "
        f"not configured (re-check the annotation block in "
        f"gpf_instance.yaml and that `wgpf run` re-annotated), or the "
        f"score id in the guide drifted from the annotator's output "
        f"attribute name."
    )
    raise AssertionError(message)


def assert_pheno_instruments_available(
        response, instruments, *, rst_ref, expectation,
):
    """Assert each of ``instruments`` is listed by the Phenotype Browser
    instruments endpoint (``/api/v3/pheno_browser/instruments``).

    Backs the phenotype guide's claim that, after ``import_phenotypes``,
    the Phenotype Browser tab shows the imported instruments. The
    response is a JSON object ``{"instruments": [...], "default": ...}``
    whose ``instruments`` value is a list of instrument-name strings. A
    non-200 status fails with HTTP-error triage; a missing instrument
    fails with a hint pointing at the import step.
    """
    if response.status_code != 200:
        raise AssertionError(_http_failure_message(
            response,
            rst_ref=rst_ref,
            expectation=expectation,
            what_was_expected=(
                f"HTTP 200 with instruments {instruments} listed"
            ),
        ))
    listed = response.json().get("instruments", [])
    missing = [i for i in instruments if i not in listed]
    if not missing:
        return
    available = ", ".join(repr(i) for i in listed) or "(none)"
    message = (
        f'DRIFT at {rst_ref} — "{expectation}"\n'
        f"\n"
        f"  expected instruments: {', '.join(instruments)}\n"
        f"  missing:              {', '.join(missing)}\n"
        f"  available:            [{available}]\n"
        f"\n"
        f"  Triage hint: The Phenotype Browser responded but an expected "
        f"instrument is absent. Most likely either (a) the "
        f"import_phenotypes step did not import the instrument (re-check "
        f"its exit code + that import_project.yaml lists the instrument "
        f"file), or (b) the instrument name in the guide drifted from "
        f"what the import produces. If the new name is correct, update "
        f"the guide."
    )
    raise AssertionError(message)


def _navigate(obj, dotted_path):
    """Walk a dotted key path into nested dicts.

    Returns ``(found, value)``: ``found`` is False if any segment is
    missing (or a non-dict is hit mid-path), in which case ``value`` is
    None. Distinguishes a genuinely-absent key from a key present with a
    falsy value, so the failure message can say "absent" vs. the value.
    """
    current = obj
    for key in dotted_path.split("."):
        if not isinstance(current, dict) or key not in current:
            return False, None
        current = current[key]
    return True, current


def assert_dataset_description_flag(
        response, flag_path, *, rst_ref, expectation,
):
    """Assert a (possibly nested) flag in a dataset description is truthy.

    Backs the phenotype guide's claims that attaching a phenotype db to
    ``example_dataset`` enables the Phenotype Browser + Phenotype Tool
    tabs and the genotype-browser Pheno Measures filters. The response
    is the single-dataset description endpoint (``/api/v3/datasets/<id>``),
    shaped ``{"data": {...}}``. ``flag_path`` is a dotted path into that
    inner object, e.g. ``"phenotype_tool"`` or
    ``"genotype_browser_config.has_person_pheno_filters"``.
    """
    if response.status_code != 200:
        raise AssertionError(_http_failure_message(
            response,
            rst_ref=rst_ref,
            expectation=expectation,
            what_was_expected=(
                f"HTTP 200 with a truthy '{flag_path}' in the "
                f"dataset description"
            ),
        ))
    data = response.json().get("data", {})
    found, value = _navigate(data, flag_path)
    if found and value:
        return
    actual = "absent" if not found else f"{value!r}"
    message = (
        f'DRIFT at {rst_ref} — "{expectation}"\n'
        f"\n"
        f"  expected: dataset description flag '{flag_path}' truthy\n"
        f"  actual:   {actual}\n"
        f"  description keys: {', '.join(sorted(data)) or '(none)'}\n"
        f"\n"
        f"  Triage hint: The dataset description was returned but the "
        f"phenotype flag is not set. Most likely either (a) the "
        f"`phenotype_data: mini_pheno` line was not added to the "
        f"example_dataset config (or the pheno study failed to import, so "
        f"the attachment resolves to nothing), or (b) the description "
        f"field that signals this tab was renamed. If the field moved, "
        f"update the test's flag path; if the guide's claim no longer "
        f"holds, update the guide."
    )
    raise AssertionError(message)
