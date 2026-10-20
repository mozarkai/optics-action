"""Print a Markdown summary of an Optics JUnit report; exit 1 if any test failed.

Error screens found at the end of a run are added to the report as failing test
cases without changing the exit code of `optics execute`, so this step is what
fails the build on them.
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

path = Path(sys.argv[1])
if not path.is_file():
    print(f"### Optics\n\nNo JUnit report at `{path}`: the run did not get far enough to write one.")
    sys.exit(0)

root = ET.parse(path).getroot()
suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
cases = [c for s in suites for c in s.iter("testcase")]
total = sum(int(s.get("tests", 0)) for s in suites)
failed = sum(int(s.get("failures", 0)) + int(s.get("errors", 0)) for s in suites)
skipped = sum(int(s.get("skipped", 0)) for s in suites)

print("### Optics results\n")
print(f"**{total - failed - skipped} passed, {failed} failed, {skipped} skipped** of {total} test cases.\n")
print("| Test case | Status | Time (s) | Message |")
print("|---|---|---|---|")
for c in cases:
    problem = c.find("failure") if c.find("failure") is not None else c.find("error")
    status = c.get("status") or ("FAIL" if problem is not None else "PASS")
    message = (problem.get("message", "") if problem is not None else "").replace("|", "\\|").replace("\n", " ")
    print(f"| {c.get('name', '')} | {status} | {c.get('time', '')} | {message[:300]} |")

sys.exit(1 if failed else 0)
