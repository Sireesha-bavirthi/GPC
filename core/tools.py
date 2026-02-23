"""
APO v2 — Core Browser Tools (10 tools)
All Playwright-based tools used by every agent tier.
"""

import re
import time
import json
from pathlib import Path
from playwright.async_api import Page

from core.config import (
    ACTION_DELAY_MS, PAGE_LOAD_TIMEOUT,
    SCROLL_STEPS, GPC_HEADER_KEY, GPC_HEADER_VALUE,
    GPC_JS_SCRIPT, KNOWN_TRACKERS, PII_PATTERNS,
    TEMPORAL_LEAK_MS
)

# ═══════════════════════════════════════════════════════════════
# TOOL 1: navigate_to_page
# ═══════════════════════════════════════════════════════════════
async def navigate_to_page(page: Page, url: str) -> dict:
    try:
        response = await page.goto(url, wait_until="domcontentloaded",
                                   timeout=PAGE_LOAD_TIMEOUT)
        await page.wait_for_load_state("networkidle", timeout=PAGE_LOAD_TIMEOUT)
        return {
            "status": "ok",
            "url": page.url,
            "title": await page.title(),
            "http_status": response.status if response else None,
        }
    except Exception as e:
        return {"status": "error", "msg": str(e)}


# ═══════════════════════════════════════════════════════════════
# TOOL 2: click_element
# ═══════════════════════════════════════════════════════════════
async def dismiss_modal(page: Page) -> None:
    for sel in ["[aria-label='Close']", "button.close", ".modal-close",
                ".cookie-accept", "button#accept-all", "[data-dismiss='modal']"]:
        try:
            el = await page.query_selector(sel)
            if el and await el.is_visible():
                await el.click()
                await page.wait_for_timeout(400)
                return
        except Exception:
            pass
    try:
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(200)
    except Exception:
        pass


async def click_element(page: Page, selector: str) -> dict:
    await dismiss_modal(page)
    try:
        await page.wait_for_selector(selector, timeout=5000)
        await page.evaluate(f"document.querySelector('{selector}')?.click()")
        await page.wait_for_timeout(ACTION_DELAY_MS)
        return {"status": "ok", "clicked": selector}
    except Exception as e:
        return {"status": "error", "msg": str(e)}


# ═══════════════════════════════════════════════════════════════
# TOOL 3: fill_form_field
# ═══════════════════════════════════════════════════════════════
async def fill_form_field(page: Page, selector: str, value: str,
                          submit: bool = False) -> dict:
    await dismiss_modal(page)
    fallbacks = [selector, "input[type=text]", "input[type=email]", "textarea"]
    for sel in fallbacks:
        try:
            el = await page.query_selector(sel)
            if el:
                await el.fill(value)
                if submit:
                    await el.press("Enter")
                await page.wait_for_timeout(ACTION_DELAY_MS)
                return {"status": "ok", "filled": sel, "value": value}
        except Exception:
            continue
    return {"status": "error", "msg": "No fillable field found"}


# ═══════════════════════════════════════════════════════════════
# TOOL 4: inject_gpc_signal
# ═══════════════════════════════════════════════════════════════
async def inject_gpc_signal(page: Page) -> dict:
    try:
        await page.add_init_script(GPC_JS_SCRIPT)
        gpc_value = await page.evaluate("() => navigator.globalPrivacyControl")
        return {"status": "ok", "gpc_active": bool(gpc_value)}
    except Exception as e:
        return {"status": "error", "msg": str(e)}


# ═══════════════════════════════════════════════════════════════
# TOOL 5: scroll_page
# ═══════════════════════════════════════════════════════════════
async def scroll_page(page: Page, steps: int = SCROLL_STEPS) -> dict:
    try:
        for i in range(steps):
            await page.evaluate(f"window.scrollBy(0, window.innerHeight * 0.8)")
            await page.wait_for_timeout(300)
        await page.evaluate("window.scrollTo(0, 0)")
        return {"status": "ok", "steps": steps}
    except Exception as e:
        return {"status": "error", "msg": str(e)}


# ═══════════════════════════════════════════════════════════════
# TOOL 6: save_session_state
# ═══════════════════════════════════════════════════════════════
async def save_session_state(page: Page, output_path: Path) -> dict:
    try:
        context = page.context
        cookies = await context.cookies()
        local_storage = await page.evaluate("""() => {
            let data = {};
            for (let i = 0; i < localStorage.length; i++) {
                let k = localStorage.key(i);
                data[k] = localStorage.getItem(k);
            }
            return data;
        }""")
        session_storage = await page.evaluate("""() => {
            let data = {};
            for (let i = 0; i < sessionStorage.length; i++) {
                let k = sessionStorage.key(i);
                data[k] = sessionStorage.getItem(k);
            }
            return data;
        }""")
        state = {
            "cookies": cookies,
            "local_storage": local_storage,
            "session_storage": session_storage,
            "url": page.url,
        }
        Path(output_path).write_text(json.dumps(state, indent=2))
        return {"status": "ok", "cookies_saved": len(cookies)}
    except Exception as e:
        return {"status": "error", "msg": str(e)}


# ═══════════════════════════════════════════════════════════════
# TOOL 7: Traffic capture factory
# Returns a (log, on_request_handler) tuple
# ═══════════════════════════════════════════════════════════════
def make_traffic_listener(session_label: str) -> tuple[list, callable]:
    """
    Returns (log_list, on_request_handler).
    Each captured request includes timestamp for temporal leak analysis.
    """
    log = []
    gpc_start_time = None   # set externally when GPC is injected

    def on_request(request):
        url = request.url
        domain = url.split("/")[2] if "//" in url else ""
        is_tracker = any(t in domain for t in KNOWN_TRACKERS)
        pii_found = [
            name for name, pat in PII_PATTERNS.items()
            if re.search(pat, url, re.IGNORECASE)
        ]
        ts_ms = int(time.time() * 1000)
        log.append({
            "session":       session_label,
            "url":           url,
            "method":        request.method,
            "domain":        domain,
            "timestamp_ms":  ts_ms,
            "is_tracker":    is_tracker,
            "pii_detected":  pii_found,
            "resource_type": request.resource_type,
        })

    return log, on_request


# ═══════════════════════════════════════════════════════════════
# TOOL 8: detect_cookie_banner
# ═══════════════════════════════════════════════════════════════
async def detect_cookie_banner(page: Page) -> dict:
    selectors = [
        "[class*='cookie']", "[id*='cookie']",
        "[class*='consent']", "[id*='consent']",
        "[class*='gdpr']", "[id*='privacy-banner']",
        "div[aria-label*='cookie']",
    ]
    found = []
    for sel in selectors:
        try:
            el = await page.query_selector(sel)
            if el and await el.is_visible():
                found.append(sel)
        except Exception:
            pass
    return {"banner_detected": bool(found), "matched_selectors": found}


# ═══════════════════════════════════════════════════════════════
# TOOL 9: detect_do_not_sell_link
# CCPA §1798.135(a) — required on every page
# ═══════════════════════════════════════════════════════════════
async def detect_do_not_sell_link(page: Page) -> dict:
    patterns = [
        "do not sell", "do not share", "your privacy choices",
        "california privacy", "opt-out", "opt out",
        "limit the use", "your ad choices",
    ]
    found_texts = []
    try:
        links = await page.query_selector_all("a, button, [role='link']")
        for link in links:
            try:
                text = (await link.inner_text()).strip().lower()
                for p in patterns:
                    if p in text:
                        found_texts.append(text[:80])
                        break
            except Exception:
                pass
    except Exception:
        pass
    return {"link_found": bool(found_texts), "link_texts": list(set(found_texts))}


# ═══════════════════════════════════════════════════════════════
# TOOL 10: handle_cookie_consent
# Actively clicks Accept or Reject based on session type.
# Baseline session (accept_all=True)  → clicks "Accept All"
# Compliance session (accept_all=False) → clicks "Reject All"
# ═══════════════════════════════════════════════════════════════
async def handle_cookie_consent(page: Page, accept_all: bool = True) -> dict:
    """
    Finds and clicks the correct cookie consent button.
    accept_all=True  → Accept / Allow / Agree  (Baseline session)
    accept_all=False → Reject / Decline / Necessary only  (Compliance session)
    """
    action = "ACCEPT" if accept_all else "REJECT"

    patterns_accept = [
        "accept all", "allow all", "agree", "accept cookies",
        "i accept", "allow cookies", "got it", "i agree", "accept"
    ]
    patterns_reject = [
        "reject all", "decline all", "reject", "decline",
        "necessary only", "only essential", "decline cookies",
        "no thanks", "save settings"
    ]
    target_patterns = patterns_accept if accept_all else patterns_reject

    try:
        # Pass 1: Match button text
        elements = await page.query_selector_all("button, a, [role='button']")
        for el in elements:
            try:
                if not await el.is_visible():
                    continue
                text = (await el.inner_text()).strip().lower()
                if not text:
                    continue
                if any(p in text for p in target_patterns):
                    await el.click()
                    await page.wait_for_timeout(ACTION_DELAY_MS)
                    return {"status": "ok", "action": action, "button_text": text[:50]}
            except Exception:
                continue

        # Pass 2: Fallback CSS selectors
        selectors_accept = ["#accept-all", ".accept-all", "#cookie-accept",
                            ".cookie-accept-all", "[id*='accept-all']"]
        selectors_reject = ["#reject-all", ".reject-all", "#cookie-reject",
                            ".cookie-reject-all", "[id*='reject-all']"]
        for sel in (selectors_accept if accept_all else selectors_reject):
            try:
                el = await page.query_selector(sel)
                if el and await el.is_visible():
                    await el.click()
                    await page.wait_for_timeout(ACTION_DELAY_MS)
                    return {"status": "ok", "action": action, "selector": sel}
            except Exception:
                continue

        return {"status": "not_found", "action": action,
                "msg": "No matching cookie consent button found"}
    except Exception as e:
        return {"status": "error", "action": action, "msg": str(e)}


# ═══════════════════════════════════════════════════════════════
# TOOL 10: detect_temporal_leak
# Checks if trackers fired within TEMPORAL_LEAK_MS after a page load
# ═══════════════════════════════════════════════════════════════
def detect_temporal_leak(traffic_log: list, page_load_ts_ms: int) -> list:
    """
    Returns list of tracker requests that fired within
    TEMPORAL_LEAK_MS milliseconds of page load.
    These represent temporal leaks — data escaped before opt-out processed.
    """
    leaks = []
    window_end = page_load_ts_ms + TEMPORAL_LEAK_MS
    for req in traffic_log:
        if req["is_tracker"] and req["timestamp_ms"] <= window_end:
            leaks.append({
                "domain": req["domain"],
                "url": req["url"],
                "fired_ms_after_load": req["timestamp_ms"] - page_load_ts_ms,
            })
    return leaks
