"""Render ruff's JSON report as flake8-syntax lines for Warnings NG.

Why this exists
---------------
Warnings NG ships no ``ruff`` parser on our Jenkins, so the ``Jenkinsfile``
feeds ruff's report to its ``flake8()`` parser instead. That parser wants a
flake8 code token::

    path/to/file.py:12:5: E501 Line too long (206 > 80)

Up to ruff 0.15 the ``concise`` output was close enough to satisfy it. Ruff
0.16 deprecated rule *codes* in favour of rule *names* and dropped codes
from **every** text format::

    path/to/file.py:12:5: line-too-long: Line too long (206 > 80)   # concise
    path/to/file.py:12: [line-too-long] Line too long (206 > 80)    # pylint

Neither carries an ``E501``-shaped token, so the flake8 parser matches
nothing — and it fails *silently*: the ruff Issues tab would simply go
empty and the quality gate would stop firing, which looks exactly like a
clean run.

The JSON output is the one format that still carries ``code``, so CI emits
that and this script renders the flake8 line. It also keeps the rule name,
appended to the message, so a finding remains greppable by the spelling
ruff itself now prints.

Usage::

    python3 scripts/convert_ruff_output.py <ruff.json> [<out.txt>]

Writes to stdout when no output path is given.
"""
import json
import pathlib
import sys


def render(entry: dict) -> str:
    """One flake8-syntax line for one ruff diagnostic."""
    location = entry.get("location") or {}
    row = location.get("row", 1)
    column = location.get("column", 1)
    # `code` is null for syntax errors, which have no rule behind them.
    code = entry.get("code") or "RUFF"
    message = entry.get("message", "")
    name = (entry.get("url") or "").rsplit("/", 1)[-1]
    if name:
        message = f"{message} ({name})"
    return f"{entry['filename']}:{row}:{column}: {code} {message}"


def main(argv: list[str]) -> int:
    if not 2 <= len(argv) <= 3:
        print(__doc__, file=sys.stderr)
        return 2

    source = pathlib.Path(argv[1])
    # A clean run still has to produce the report file: Warnings NG treats a
    # missing pattern as a build problem, not as zero findings.
    entries = json.loads(source.read_text()) if source.stat().st_size else []
    text = "".join(f"{render(entry)}\n" for entry in entries)

    if len(argv) == 3:
        pathlib.Path(argv[2]).write_text(text)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
