import asyncio
from backend import _run_scan, ScanRequest, SCANS

SCANS["test_id"] = {
    "status": "pending",
    "events": [],
    "phase": "idle",
    "progress": {"discovery": 0, "interaction": 0, "observability": 0}
}
# Using an invalid URL that will definitely fail navigate_to_page
req = ScanRequest(url="https://www.cpchem.com", framework="CCPA", crawl_depth=1, use_llm=False)
_run_scan("test_id", req)

for ev in SCANS["test_id"]["events"]:
    print(ev)
