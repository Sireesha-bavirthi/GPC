import asyncio
from backend import app, _run_scan, ScanRequest, SCANS

SCANS["test_id"] = {
    "status": "pending",
    "events": [],
    "phase": "idle",
    "progress": {"discovery": 0, "interaction": 0, "observability": 0}
}
req = ScanRequest(url="https://www.cpchem.com", framework="CCPA", crawl_depth=1, use_llm=False)

# Let's run it directly
_run_scan("test_id", req)

for ev in SCANS["test_id"]["events"]:
    print(ev)
