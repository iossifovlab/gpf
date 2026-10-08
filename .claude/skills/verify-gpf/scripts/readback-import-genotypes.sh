#!/usr/bin/env bash
# readback-import-genotypes.sh <variants.tsv>
#
# Check a dump of the imported study (written by dump_study.py) against the
# exact values the drive's input gives:
#   families f1, f2
#   f1 chrA:11 A>C   f1 chrA:23 A>G   f2 chrA:37 A>T
#   each with best state "2 2 1/0 0 1" (mom, dad, proband)
# Exits 0 on an exact match, 1 otherwise. A dump with a lost, extra or
# changed variant, or another family set, fails.

set -euo pipefail

dump="${1:-}"
[[ -n "$dump" ]] || { echo "readback: missing <variants.tsv> argument" >&2; exit 1; }
[[ -f "$dump" ]] || { echo "readback: FAIL: $dump does not exist" >&2; exit 1; }

expected=$'#families\tf1,f2
family\tchrom\tpos\tref\talt\tbest_state
f1\tchrA\t11\tA\tC\t2 2 1/0 0 1
f1\tchrA\t23\tA\tG\t2 2 1/0 0 1
f2\tchrA\t37\tA\tT\t2 2 1/0 0 1'
actual="$(cat "$dump")"

if [[ "$actual" != "$expected" ]]; then
    echo "readback: FAIL: the study in $dump does not match"
    echo "--- expected"
    printf '%s\n' "$expected"
    echo "--- actual"
    printf '%s\n' "$actual"
    exit 1
fi
echo "readback: PASS: families f1, f2; f1 chrA:11 A>C, f1 chrA:23 A>G, f2 chrA:37 A>T in $dump"
