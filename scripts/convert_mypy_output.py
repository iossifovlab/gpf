import pathlib
import re
import sys
from dataclasses import dataclass

SEVERITY_MAP_PYLINT = {
    "information": "C",
    "warning": "W",
    "error": "E",
}


@dataclass
class MypyError:
    """Represents a single mypy error."""
    file: str
    line: int
    severity: str
    rule: str
    message: str
    source: str

    def __repr__(self) -> str:
        return (
            f"{self.file}:{self.line}: [{self.severity}{self.rule}] "
            f"{self.message}"
        )


MYPY_PATTERN = re.compile(
    r"^(?P<file>[^:\n]+?):(?P<line>[0-9^:]+): (?P<severity>[^:]+?): "
    r"(?P<message>.+?)(?=(( |\n)\[)|(\n[^:\n]+?:[0-9^:]+?:))"
    r"( |\n)(?P<rule>\[[^\]]+?\])?",
    re.MULTILINE | re.DOTALL)

SEVERITY_MAP_PYLINT = {
    "note": "C",
    "warning": "W",
    "error": "E",
}


def _parse_mypy_output(text: str) -> list[MypyError]:
    severities: set[str] = set()
    result = []
    for data in MYPY_PATTERN.finditer(text):
        groups = data.groupdict()
        file = groups["file"].strip()
        line = int(groups["line"])
        severity = groups["severity"].strip()
        severities.add(groups["severity"].strip())
        sverity = SEVERITY_MAP_PYLINT[severity]
        message = groups["message"].strip()
        message = message.replace("\n", " ")
        rule = groups.get("rule")
        if rule is None:
            rule = "note"
        else:
            rule = rule.strip()
            rule = rule.strip("[]")
        source = text[data.start():data.end()]
        result.append(MypyError(
            file=file,
            line=line,
            severity=sverity,
            rule=rule,
            message=message,
            source=source,
        ))
    print(
        f"Found severities: {', '.join(sorted(severities))}",
        file=sys.stderr)
    return result


def main(filepath: str) -> None:
    """Main function to read mypy output and print it in a PyLint format."""

    if not (content := pathlib.Path(filepath).read_text()):
        return
    for mypy in _parse_mypy_output(content):
        print(
            f"{mypy.file}:{mypy.line}: [{mypy.severity}{mypy.rule}] "
            f"{mypy.message}",
        )


if __name__ == "__main__":
    main(sys.argv[-1])
