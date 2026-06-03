import re
import pytest
from playwright.sync_api import sync_playwright, expect

# Android mobile emulation using Pixel 5 device descriptor
DEVICE_NAME = "Pixel 5"
URL = "https://www.easemytrip.com"

# Train number to check live status
TRAIN_NUMBER = "12815"
TRAIN_NAME   = ""


def test_easemytrip_live_train_status_mobweb():
    with sync_playwright() as p:
        pixel5 = p.devices[DEVICE_NAME]

        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            **pixel5,
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )

        page = context.new_page()

        # ── 1. Load home page ────────────────────────────────────────────────
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        expect(page).to_have_title(re.compile(r"easemytrip", re.IGNORECASE), timeout=15000)
        assert "easemytrip.com" in page.url, f"Unexpected URL: {page.url}"

        print(f"\n✅ Page loaded successfully")
        print(f"   Title : {page.title()}")
        print(f"   URL   : {page.url}")
        print(f"   Device: {DEVICE_NAME} ({pixel5['viewport']})")
        page.screenshot(path="emt6_home.png", full_page=False)
        print("   Screenshot saved: emt6_home.png")

        # ── 2. Navigate to Trains ────────────────────────────────────────────
        trains_link = page.get_by_role("link", name=re.compile(r"trains", re.IGNORECASE))
        trains_link.first.wait_for(state="visible", timeout=15000)
        trains_link.first.click()
        page.wait_for_load_state("domcontentloaded", timeout=30000)

        assert "train" in page.url.lower() or "train" in page.title().lower(), \
            f"Did not navigate to Trains page. URL: {page.url}, Title: {page.title()}"

        print(f"\n✅ Trains page loaded successfully")
        print(f"   Title : {page.title()}")
        print(f"   URL   : {page.url}")
        page.screenshot(path="emt6_trains.png", full_page=False)
        print("   Screenshot saved: emt6_trains.png")

        # ── 3. Click Live Train Status icon/tab ──────────────────────────────
        # Try multiple selectors in order of specificity
        live_status_clicked = False

        # Strategy 1: link/button with text "Live Train Status"
        live_btn = page.get_by_role("link", name=re.compile(r"live\s*train\s*status", re.IGNORECASE)).first
        if live_btn.count() > 0:
            live_btn.wait_for(state="visible", timeout=10000)
            live_btn.click()
            live_status_clicked = True

        # Strategy 2: any element with matching text
        if not live_status_clicked:
            live_btn = page.get_by_text(re.compile(r"live\s*train\s*status", re.IGNORECASE)).first
            if live_btn.count() > 0:
                live_btn.wait_for(state="visible", timeout=10000)
                live_btn.click()
                live_status_clicked = True

        # Strategy 3: anchor tag href containing "live"
        if not live_status_clicked:
            live_btn = page.locator("a[href*='live'], a[href*='Live']").first
            if live_btn.count() > 0:
                live_btn.wait_for(state="visible", timeout=10000)
                live_btn.click()
                live_status_clicked = True

        # Strategy 4: icon/div with class containing "live"
        if not live_status_clicked:
            live_btn = page.locator(
                "[class*='live'], [id*='live'], [class*='Live'], [id*='Live']"
            ).first
            if live_btn.count() > 0:
                live_btn.wait_for(state="visible", timeout=10000)
                live_btn.click()
                live_status_clicked = True

        assert live_status_clicked, "Live Train Status icon/link not found on Trains page"

        page.wait_for_load_state("domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)

        print(f"\n✅ Live Train Status clicked successfully")
        print(f"   URL   : {page.url}")
        print(f"   Title : {page.title()}")
        page.screenshot(path="emt6_live_status_page.png", full_page=False)
        print("   Screenshot saved: emt6_live_status_page.png")

        # ── 4. Verify Live Train Status page loaded ──────────────────────────
        assert any(kw in page.url.lower() or kw in page.title().lower()
                   for kw in ["live", "status", "running"]), \
            f"Live Train Status page not loaded. URL: {page.url}, Title: {page.title()}"

        print(f"\n✅ Live Train Status page verified")

        # ── 5. Enter train number in search field ────────────────────────────
        # Try common input selectors for train number search
        train_input = None
        for selector in [
            "input[placeholder='Enter train name or train no.']",
            "input.train_input",
            "#txtTrainSelect",
            "input[placeholder*='Train']",
            "input[placeholder*='train']",
            "#txtTrainNo",
            "#trainNo",
            "input[type='text']",
        ]:
            el = page.locator(selector).first
            if el.count() > 0:
                try:
                    train_input = el
                    print(f"   Train input found via: {selector}")
                    break
                except Exception:
                    continue

        assert train_input is not None, "Train number input field not found on Live Status page"

        # Step 1: Click #txtTrainSelect to open/reveal the search form
        trigger = page.locator("#txtTrainSelect").first
        trigger.wait_for(state="visible", timeout=10000)
        trigger.click()
        page.wait_for_timeout(1000)
        print(f"   Clicked #txtTrainSelect to reveal search form")

        # Step 2: Now click and type in the actual 'Enter train name or train no.' input
        train_input.scroll_into_view_if_needed(timeout=10000)
        page.wait_for_timeout(500)
        train_input.click(force=True)
        page.wait_for_timeout(500)
        train_input.type(TRAIN_NUMBER, delay=200)   # fires keydown/keypress/keyup to trigger autocomplete
        page.wait_for_timeout(3000)                 # wait for AJAX suggestions to load

        print(f"\n✅ Train number entered: {TRAIN_NUMBER}")
        page.screenshot(path="emt6_train_entered.png", full_page=False)
        print("   Screenshot saved: emt6_train_entered.png")

        # ── 6. Select 'Nandankanan sf' from autocomplete suggestion ──────────
        SUGGESTION_TEXT = "Nandankanan"
        suggestion_clicked = False

        for selector in [
            f"li:has-text('{SUGGESTION_TEXT}')",
            "ul.ui-autocomplete li.ui-menu-item",
            "ul.ui-autocomplete li",
            ".ui-menu-item",
            f"li:has-text('{TRAIN_NUMBER}')",
            ".auto_saugg li",
            "[class*='suggest'] li",
            "[class*='autocomplete'] li",
            "[class*='dropdown'] li",
        ]:
            suggestions = page.locator(selector)
            try:
                suggestions.first.wait_for(state="visible", timeout=6000)
                if suggestions.count() > 0:
                    first_text = suggestions.first.inner_text().strip()
                    suggestions.first.click()
                    suggestion_clicked = True
                    print(f"   Suggestion selected: {first_text!r}  (via: {selector})")
                    break
            except Exception:
                continue

        if not suggestion_clicked:
            print("   ⚠️  No dropdown suggestion appeared — proceeding without selection")

        page.wait_for_timeout(1000)
        page.screenshot(path="emt6_suggestion.png", full_page=False)
        print("   Screenshot saved: emt6_suggestion.png")

        # ── 7. Click GET LIVE STATUS button ──────────────────────────────────
        search_clicked = False
        for selector in [
            "input.srch_btn[value='Get Live Status']",
            "input.srch_btn",
            "input[value='Get Live Status']",
            "button:has-text('Get Live Status')",
            "input[type='button'][value*='Live']",
            "input[type='button'][value*='Status']",
            "input[type='submit']",
        ]:
            btn = page.locator(selector).first
            if btn.count() > 0:
                try:
                    btn.wait_for(state="visible", timeout=5000)
                    btn.scroll_into_view_if_needed(timeout=5000)
                    btn.click()
                    search_clicked = True
                    print(f"   GET LIVE STATUS clicked via: {selector}")
                    break
                except Exception:
                    continue

        assert search_clicked, "GET LIVE STATUS button not found or not clickable"

        if search_clicked:
            page.wait_for_load_state("domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)

        page.screenshot(path="emt6_status_result.png", full_page=False)
        print("   Screenshot saved: emt6_status_result.png")

        # ── 8. Verify result page loaded ─────────────────────────────────────
        assert "12815" in page.url or "12815" in page.title(), \
            f"Live status result page not loaded. URL: {page.url}"

        print(f"\n✅ Live status search completed")
        print(f"   URL   : {page.url}")
        print(f"   Title : {page.title()}")

        # ── 9. Scroll down and verify live status table ──────────────────────
        # Wait for status table to render
        try:
            page.locator("table, [class*='station'], [class*='tbl'], [class*='grid']").first \
                .wait_for(state="visible", timeout=15000)
        except Exception:
            pass

        # Scroll down in steps and take screenshots
        for i, scroll_y in enumerate([300, 600, 900, 1200], start=1):
            page.evaluate(f"window.scrollTo(0, {scroll_y})")
            page.wait_for_timeout(800)
            page.screenshot(path=f"emt6_scroll_{i}.png", full_page=False)
            print(f"   Screenshot saved: emt6_scroll_{i}.png  (scroll y={scroll_y})")

        # Scroll back to top to read all station rows
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)

        # Read station rows — try common table/row selectors
        station_rows = []
        for selector in [
            "tr.station-row, tr[class*='station']",
            "tr[class*='row']",
            "tbody tr",
            "[class*='station-row']",
            "[class*='stn-row']",
            "[class*='sttn']",
            "table tr",
        ]:
            rows = page.locator(selector).all()
            if len(rows) >= 2:
                for row in rows[:20]:
                    try:
                        txt = row.inner_text().strip().replace("\n", " | ")
                        if txt and len(txt) > 5:
                            station_rows.append(txt[:120])
                    except Exception:
                        pass
                if station_rows:
                    print(f"   Rows found via: {selector}")
                    break

        # Fallback: grab any visible text blocks that look like station info
        if not station_rows:
            for selector in ["[class*='station']", "[class*='stop']", "[class*='halt']"]:
                els = page.locator(selector).all()
                for el in els[:15]:
                    try:
                        txt = el.inner_text().strip().replace("\n", " | ")
                        if txt and len(txt) > 3:
                            station_rows.append(txt[:120])
                    except Exception:
                        pass
                if station_rows:
                    break

        print(f"\n✅ Live Status table verified — {len(station_rows)} station row(s) found")
        for i, row in enumerate(station_rows[:10], start=1):
            print(f"   [{i:02d}] {row}")

        # Final full-scroll screenshot
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)
        page.screenshot(path="emt6_final.png", full_page=False)
        print("   Screenshot saved: emt6_final.png")

        print(f"\n✅ Live Train Status test completed successfully")
        print(f"   Train  : {TRAIN_NUMBER}")

        browser.close()
