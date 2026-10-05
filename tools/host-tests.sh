#!/bin/sh
# C0 host proof: run the stdlib tests the reduced configuration must pass
# against build/host/python.exe (pthread stubs, static modules, no
# mimalloc), one test module per process, each verdict recorded as it
# finishes in build/host/tests.tsv (module, verdict, counts). Resumable:
# modules already recorded are skipped.
#   tools/host-tests.sh               the C0 set, those not yet recorded
#   tools/host-tests.sh name...       just these (re-run, re-recorded)
#   tools/host-tests.sh --failed      re-run the recorded failures
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
HB=$ROOT/build/host
PY=$HB/python.exe
LOG=$HB/tests.tsv
OUT=$HB/tests-out
EXPECTED=$ROOT/tests/c0-expected.tsv
C0="test_json test_re test_posixpath test_genericpath test_io test_struct
test_math test_time test_select test_subprocess
tests/test_c0_config.py tests/test_c2_import_case.py
tests/test_w35_exec_bare_name.py tests/test_w35_abspath.py"
mkdir -p "$OUT"
touch "$LOG"

if [ $# -gt 0 ] && [ "$1" = "--failed" ]; then
	set -- $(awk -F'\t' '$2 !~ /^pass/ {print $1}' "$LOG")
fi
if [ $# -gt 0 ]; then
	list="$*"
	for t in $list; do
		grep -v "^$t	" "$LOG" > "$LOG.tmp"; mv "$LOG.tmp" "$LOG"
	done
else
	list=$C0
fi

for t in $list; do
	grep -q "^$t	" "$LOG" && continue
	o=$OUT/$(echo "$t" | tr / _).txt
	if [ "${t%.py}" != "$t" ]; then
		# this repo's own tests of the configuration (tests/*.py)
		(cd "$ROOT" && "$PY" -m unittest -v "$t") > "$o" 2>&1
	else
		# -u all minus network/gui; one worker, this machine runs hot
		"$PY" -m test -u all,-network,-gui,-cpu,-largefile "$t" -v > "$o" 2>&1
	fi
	rc=$?
	sum=$(grep -E "^(Total tests|Ran [0-9]+ test)" "$o" | tail -1)
	if [ $rc -eq 0 ]; then v=pass
	else
		# pass* = every reported failure is a by-design one (tests/c0-expected.tsv)
		unexpected=$(grep -E "^(FAIL|ERROR):" "$o" | sed -E 's/^(FAIL|ERROR): //' |
			sort -u | while IFS= read -r id; do
				cut -f1 "$EXPECTED" | grep -qxF "$id" || echo "$id"; done)
		nexp=$(grep -cE "^(FAIL|ERROR):" "$o")
		if [ $rc -ne 0 ] && [ "$nexp" -gt 0 ] && [ -z "$unexpected" ]; then v="pass*"
		else v="fail($rc)"; fi
	fi
	printf '%s\t%s\t%s\n' "$t" "$v" "$sum" >> "$LOG"
	printf '%s\t%s\t%s\n' "$t" "$v" "$sum"
done
awk -F'\t' '{n++; if ($2=="pass") p++; if ($2=="pass*") e++} END {printf "%d of %d pass (%d of them pass* = only by-design failures, tests/c0-expected.tsv)\n", p+e, n, e}' "$LOG"
