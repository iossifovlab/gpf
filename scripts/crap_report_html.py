"""Render the text CRAP table of crapper as an HTML page.

Usage: ``python crap_report_html.py <crap.txt> <crap.html> [<churn log>
<source root>]``

The core stage of the root ``Jenkinsfile`` writes ``crap.txt`` with
``crapper`` and publishes the page that this script writes with
``publishHTML``. Jenkins serves that page under a Content-Security-Policy
that blocks inline styles and scripts, so the page is plain HTML: a
summary list and one table, worst score first, as crapper sorts it.

A row of the table has five fields: function, namespace, cyclomatic
complexity, coverage (``97.4%``) and CRAP. Lines before the dashed rule
under the column header are the report header. An input without that
rule, or with no rows, gives a page that says so.

The optional churn log is the ``git log -M --name-status`` text that the
"Prepare workspace" stage writes. With it, a second table ranks the
functions by hotspot score: CRAP times the number of commits in the log
that changed the file of the function. The source root maps each
namespace to its file. Without the log, or with a missing or empty log,
one sentence takes the place of the hotspot table.
"""
import html
import pathlib
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class CrapRow:
    """One function of the CRAP table."""
    function: str
    namespace: str
    complexity: int
    coverage: float
    crap: float


def parse_crap_table(text: str) -> list[CrapRow]:
    """Return the rows of a crapper text table, in table order."""
    lines = text.splitlines()
    start = next(
        (i + 1 for i, line in enumerate(lines)
         if line.startswith("---")),
        None)
    if start is None:
        return []
    rows = []
    for line in lines[start:]:
        fields = line.split()
        if len(fields) != 5:
            continue
        function, namespace, complexity, coverage, crap = fields
        rows.append(CrapRow(
            function, namespace, int(complexity),
            float(coverage.rstrip("%")), float(crap)))
    return rows


COMMIT_MARKER = "@@commit:"
# A commit that changes this many files or more is a split, a package
# rename or a tool bump: it adds no churn, but its renames still count.
BIG_COMMIT = 100


def _commits(text: str) -> list[list[list[str]]]:
    """Split ``--name-status`` text into commits of tab-split lines."""
    commits: list[list[list[str]]] = []
    for line in text.splitlines():
        if line.startswith(COMMIT_MARKER):
            commits.append([])
        elif line.strip() and commits:
            commits[-1].append(line.split("\t"))
    return commits


def parse_churn_log(text: str) -> dict[str, int]:
    """Return the commit count of each file, keyed by its current path.

    The text is ``git log -M --name-status`` output, newest commit first,
    with ``COMMIT_MARKER`` as the format of each commit line. A map from
    each old path to the current path follows the renames. A pure rename
    (``R100``) adds no churn. A commit adds at most one to each file.
    """
    current: dict[str, str] = {}
    churn: dict[str, int] = {}
    for commit in _commits(text):
        renames: dict[str, str] = {}
        changed: set[str] = set()
        for fields in commit:
            status, path = fields[0], fields[-1]
            path = current.get(path, path)
            if status.startswith("R"):
                renames[fields[1]] = path
            if status != "R100":
                changed.add(path)
        if len(commit) < BIG_COMMIT:
            for path in changed:
                churn[path] = churn.get(path, 0) + 1
        current.update(renames)
    return churn


def namespace_file(namespace: str, root: pathlib.Path) -> str | None:
    """Return the repo-relative file of a namespace, or None.

    The file is that of the longest dotted prefix that is a module
    (``<prefix>.py``) or a package (``<prefix>/__init__.py``) under the
    source root. The rest of the namespace is a class name. The key starts
    with the name of the root, as ``core/`` in the form that ``git log``
    prints.
    """
    parts = namespace.split(".")
    for end in range(len(parts), 0, -1):
        prefix = "/".join(parts[:end])
        for candidate in (f"{prefix}.py", f"{prefix}/__init__.py"):
            if (root / candidate).is_file():
                return f"{root.name}/{candidate}"
    return None


@dataclass(frozen=True)
class Hotspot:
    """One function of the hotspot table."""
    row: CrapRow
    commits: int

    @property
    def score(self) -> float:
        """The hotspot score: CRAP times the commits in the window."""
        return self.row.crap * self.commits


HOTSPOT_ROWS = 50


def rank_hotspots(
    rows: list[CrapRow], churn: dict[str, int], root: pathlib.Path,
    limit: int = HOTSPOT_ROWS,
) -> list[Hotspot]:
    """Return the rows with the highest hotspot score, highest first.

    A namespace that maps to no file, or a file with no entry in the
    churn map, has 0 commits.
    """
    files = {
        namespace: namespace_file(namespace, root)
        for namespace in {row.namespace for row in rows}}
    hotspots = []
    for row in rows:
        path = files[row.namespace]
        hotspots.append(Hotspot(row, churn.get(path, 0) if path else 0))
    hotspots.sort(key=lambda hotspot: hotspot.score, reverse=True)
    return hotspots[:limit]


def _hotspot_section(hotspots: list[Hotspot] | None) -> list[str]:
    """Return the HTML of the hotspot table, or of the missing sentence."""
    parts = ["<h2>Hotspots</h2>"]
    if hotspots is None:
        parts.append(
            "<p>The churn count is missing, so the page has no hotspot "
            "table.</p>")
        return parts
    parts.extend((
        (f"<p>The top {HOTSPOT_ROWS} functions by CRAP times the commits "
         "in the last 12 months that changed the file of the function.</p>"),
        ('<table border="1" cellpadding="3">'
         "<thead><tr><th>Function</th><th>Namespace</th><th>CRAP</th>"
         "<th>Commits in 12 months</th><th>Hotspot score</th></tr></thead>"
         "<tbody>"),
    ))
    parts.extend(
        f"<tr><td>{html.escape(hotspot.row.function)}</td>"
        f"<td>{html.escape(hotspot.row.namespace)}</td>"
        f'<td align="right">{hotspot.row.crap:.1f}</td>'
        f'<td align="right">{hotspot.commits}</td>'
        f'<td align="right">{hotspot.score:.1f}</td></tr>'
        for hotspot in hotspots)
    parts.append("</tbody></table>")
    return parts


def render_html(
    rows: list[CrapRow], hotspots: list[Hotspot] | None = None,
) -> str:
    """Return the HTML page for the given rows.

    The hotspot table follows the CRAP table. Without hotspots, one
    sentence says that the churn count is missing.
    """
    title = "CRAP report of gpf"
    parts = [
        "<!DOCTYPE html>",
        (f'<html><head><meta charset="utf-8"><title>{title}</title>'
         "</head><body>"),
        f"<h1>{title}</h1>",
    ]
    if not rows:
        parts.append("<p>crapper wrote no rows.</p></body></html>")
        return "\n".join(parts)
    parts.append("<ul>")
    parts.extend(
        f"<li>{label}: {count}</li>" for label, count in (
            ("Functions", len(rows)),
            ("CRAP &gt;= 30", sum(row.crap >= 30 for row in rows)),
            ("CRAP &gt;= 10", sum(row.crap >= 10 for row in rows)),
            ("Coverage 0%", sum(row.coverage == 0 for row in rows)),
        ))
    parts.extend((
        "</ul>",
        ('<table border="1" cellpadding="3">'
         "<thead><tr><th>Function</th><th>Namespace</th><th>CC</th>"
         "<th>Cov%</th><th>CRAP</th></tr></thead><tbody>"),
    ))
    parts.extend(
        f"<tr><td>{html.escape(row.function)}</td>"
        f"<td>{html.escape(row.namespace)}</td>"
        f'<td align="right">{row.complexity}</td>'
        f'<td align="right">{row.coverage:.1f}%</td>'
        f'<td align="right">{row.crap:.1f}</td></tr>'
        for row in rows)
    parts.append("</tbody></table>")
    parts.extend(_hotspot_section(hotspots))
    parts.append("</body></html>")
    return "\n".join(parts)


def read_hotspots(
    rows: list[CrapRow], log: pathlib.Path, root: pathlib.Path,
) -> list[Hotspot] | None:
    """Rank the rows by the churn log, or None for a missing log."""
    text = log.read_text() if log.is_file() else ""
    if not text.strip():
        return None
    return rank_hotspots(rows, parse_churn_log(text), root)


def main(argv: list[str]) -> int:
    """Read the text table at argv[1] and write the page to argv[2].

    The optional argv[3] and argv[4] are the churn log and the source
    root of the hotspot table.
    """
    if len(argv) not in (3, 5):
        print(__doc__, file=sys.stderr)
        return 2
    source, target = pathlib.Path(argv[1]), pathlib.Path(argv[2])
    text = source.read_text() if source.exists() else ""
    rows = parse_crap_table(text)
    hotspots = None
    if len(argv) == 5:
        hotspots = read_hotspots(
            rows, pathlib.Path(argv[3]), pathlib.Path(argv[4]))
    target.write_text(render_html(rows, hotspots))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
