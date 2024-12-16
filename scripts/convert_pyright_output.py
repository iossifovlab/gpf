import json
import os
import pathlib
import sys

SEVERITY_MAP_PYLINT = {
    "information": "C",
    "warning": "W",
    "error": "E",
}


def _convert_to_pylint(diag: dict) -> str:
    path = pathlib.Path(diag["file"]).relative_to(os.getcwd())
    severity = SEVERITY_MAP_PYLINT[diag["severity"]]
    ttype = diag["rule"]
    line = diag["range"]["start"]["line"]
    text = diag["message"]
    return f"{path}:{line}: [{severity}{ttype}] {text}".replace("\n", "")


def main(filepath: str):
    report = json.loads(pathlib.Path(filepath).read_text())
    for part in report["generalDiagnostics"]:
        print(_convert_to_pylint(part))


if __name__ == "__main__":
    main(sys.argv[-1])
