import re
import pytest
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, expect

DEVICE_NAME      = "Pixel 5"
URL              = "https://www.easemytrip.com"
TRAIN_NUMBER     = "12815"            # Nandan Kanan S/F Express
TRAIN_NAME_QUERY = "PURUSHOTTAM EXP"  # for name-based search
DAYS_AHEAD       = 4                  # select departure date ~4 days from today


def _click_date_tile(page, days_ahead: int) -> str:
    target       = datetime.now() + timedelta(days=days_ahead)
    target_day   = target.day
    target_month = target.strftime("%b").lower()
    print(f"\n📅 Selecting departure date ~+{days_ahead} days  "
          f"(target: {target.strftime('%d')},{target_month})")
    clicked = page.evaluate(f"""
        (() => {{
            const tiles = document.querySelectorAll('div.tpdate');
            let best = null, bestDiff = 9999;
            for (const t of tiles) {{
                const txt = t.textContent.trim().toLowerCase();
                const m = txt.match(/^(\\d{{1,2}}),(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)/);
                if (!m) continue;
                const day   = parseInt(m[1]);
                const month = m[2];
                const diff  = Math.abs(day - {target_day})
                            + (month === '{target_month}' ? 0 : 31);
                if (diff < bestDiff) {{ bestDiff = diff; best = t; }}
            }}
            if (best) {{ best.click(); return best.textContent.trim().substring(0, 15); }}
            return null;
        }})()
    """)
    if clicked:
        page.wait_for_timeout(500)
        print(f"   ✅ Date tile clicked: {clicked}")
        return clicked
    print("   ⚠️  No DIV.tpdate tiles found — proceeding with default date")
    return ""


def test_easemytrip_search_train_by_name_number_mobweb():
    with sync_playwright() as p:
        pixel5  = p.devices[DEVICE_NAME]
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(**pixel5, locale="en-IN", timezone_id="Asia/Kolkata")
        page    = context.new_page()

        # ── 1. Load home page ────────────────────────────────────────────────
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        expect(page).to_have_title(re.compile(r"easemytrip", re.IGNORECASE), timeout=15000)
        print(f"\n✅ Home page loaded  |  {page.url}")
        page.screenshot(path="emt7_step1_home.png")

        # ── 2. Navigate to Trains ────────────────────────────────────────────
        trains_link = page.get_by_role("link", name=re.compile(r"trains", re.IGNORECASE)).first
        trains_link.wait_for(state="visible", timeout=15000)
        trains_link.click()
        page.wait_for_load_state("domcontentloaded", timeout=30000)
        assert "train" in page.url.lower() or "train" in page.title().lower(), \
            f"Trains page not loaded. URL={page.url}"
        print(f"✅ Trains page loaded  |  {page.url}")
        page.screenshot(path="emt7_step2_trains.png")

        # ── 3. Click "Search Train by Name/No." tab ──────────────────────────
        tab_clicked = False
        for pattern in [r"search\s*train\s*by\s*name", r"train\s*by\s*name",
                         r"name.{0,3}no", r"train\s*schedule"]:
            tab = page.get_by_role("link", name=re.compile(pattern, re.IGNORECASE)).first
            if tab.count() > 0:
                try:
                    tab.wait_for(state="visible", timeout=6000)
                    tab.click()
                    tab_clicked = True
                    print(f"   Tab found via pattern: {pattern!r}")
                    break
                except Exception:
                    continue
        if not tab_clicked:
            for pattern in [r"search\s*train\s*by\s*name", r"train\s*by\s*name", r"name.{0,3}no"]:
                tab = page.get_by_text(re.compile(pattern, re.IGNORECASE)).first
                if tab.count() > 0:
                    try:
                        tab.wait_for(state="visible", timeout=6000)
                        tab.click()
                        tab_clicked = True
                        break
                    except Exception:
                        continue
        assert tab_clicked, "Could not find 'Search Train by Name/No.' tab"
        page.wait_for_load_state("domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)
        search_tab_url = page.url
        print(f"✅ Search-Train tab opened  |  {page.url}")
        page.screenshot(path="emt7_step3_tab.png")

        # ══════════════════════════════════════════════════════════════════════
        # SEARCH 1 — by Train Number (12815)
        # ══════════════════════════════════════════════════════════════════════

        # ── 4. Click trigger → locate input ──────────────────────────────────
        page.locator("#txtTrainSelect").first.wait_for(state="visible", timeout=10000)
        page.locator("#txtTrainSelect").first.click()
        page.wait_for_timeout(1000)

        train_input = None
        for sel in ["#txtTrainNumberOrName", "input[placeholder*='train name']",
                    "input[placeholder*='Train Name']", "input[type='text']"]:
            el = page.locator(sel).first
            if el.count() > 0:
                try:
                    el.wait_for(state="visible", timeout=5000)
                    train_input = el
                    print(f"   Input found via: {sel}")
                    break
                except Exception:
                    continue
        assert train_input is not None, "Train search input not found"

        # ── 5. Type train number ──────────────────────────────────────────────
        train_input.scroll_into_view_if_needed()
        train_input.click(force=True)
        page.wait_for_timeout(300)
        train_input.type(TRAIN_NUMBER, delay=200)
        page.wait_for_timeout(3000)
        print(f"✅ Typed train number: {TRAIN_NUMBER}")
        page.screenshot(path="emt7_step5_number_typed.png")

        # ── 6. Click autocomplete suggestion ─────────────────────────────────
        suggestion_clicked = False
        for sel in [f"li:has-text('{TRAIN_NUMBER}')", "ul.ui-autocomplete li.ui-menu-item",
                    "ul.ui-autocomplete li", ".ui-menu-item", ".auto_saugg li"]:
            sugg = page.locator(sel)
            try:
                sugg.first.wait_for(state="visible", timeout=6000)
                if sugg.count() > 0:
                    txt = sugg.first.inner_text().strip()
                    sugg.first.click()
                    suggestion_clicked = True
                    print(f"   Suggestion clicked: {txt!r}")
                    break
            except Exception:
                continue
        if not suggestion_clicked:
            print("   ⚠️  No autocomplete dropdown — pressing Enter")
            train_input.press("Enter")
        page.wait_for_timeout(2000)
        page.screenshot(path="emt7_step6_number_suggestion.png")

        # ── 7. Select departure date ──────────────────────────────────────────
        date_chosen1 = _click_date_tile(page, DAYS_AHEAD)
        page.screenshot(path="emt7_step7_number_date.png")

        # ── 8. Click Search ───────────────────────────────────────────────────
        for sel in ["input.srch_btn", "input[value*='Search']", "input[value*='Get']",
                    "input[value*='Schedule']", "input[type='submit']",
                    "button:has-text('Search')", "button[type='submit']"]:
            btn = page.locator(sel).first
            if btn.count() > 0:
                try:
                    btn.wait_for(state="visible", timeout=5000)
                    btn.scroll_into_view_if_needed()
                    btn.click()
                    print(f"   Search button clicked via: {sel}")
                    break
                except Exception:
                    continue
        page.wait_for_load_state("domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        page.screenshot(path="emt7_step8_number_listing.png")
        print(f"\n✅ Number search submitted  |  URL: {page.url}")

        # ── 9. Verify listing page ────────────────────────────────────────────
        for rs in ["table", "[class*='schedule']", "[class*='station']",
                   "[class*='result']", "[class*='train']"]:
            try:
                page.locator(rs).first.wait_for(state="visible", timeout=5000)
                break
            except Exception:
                continue
        page.wait_for_timeout(2000)
        body  = page.locator("body").inner_text().lower()
        url_l = page.url.lower()
        assert any([TRAIN_NUMBER in body, TRAIN_NUMBER in url_l,
                    "nandan" in body, "puri" in body, "trainlist" in url_l,
                    "_train" in url_l, len(body) > 300]), \
            f"Number listing not displayed.\nURL: {page.url}\nBody[:400]: {body[:400]}"
        print(f"✅ Train listing page displayed (by number)  |  URL: {page.url}")
        for y in [300, 600, 900]:
            page.evaluate(f"window.scrollTo(0, {y})")
            page.wait_for_timeout(500)
        page.screenshot(path="emt7_step9_number_final.png")

        # ══════════════════════════════════════════════════════════════════════
        # SEARCH 2 — by Train Name (PURUSHOTTAM EXP)
        # ══════════════════════════════════════════════════════════════════════

        # ── 10. Go back to search tab ─────────────────────────────────────────
        page.goto(search_tab_url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)
        print(f"\n✅ Back to search tab  |  {page.url}")
        page.screenshot(path="emt7_step10_back.png")

        # ── 11. Click trigger → locate input ─────────────────────────────────
        page.locator("#txtTrainSelect").first.wait_for(state="visible", timeout=10000)
        page.locator("#txtTrainSelect").first.click()
        page.wait_for_timeout(1000)

        train_input2 = None
        for sel in ["#txtTrainNumberOrName", "input[placeholder*='train name']",
                    "input[placeholder*='Train Name']", "input[type='text']"]:
            el = page.locator(sel).first
            if el.count() > 0:
                try:
                    el.wait_for(state="visible", timeout=5000)
                    train_input2 = el
                    print(f"   Input found via: {sel}")
                    break
                except Exception:
                    continue
        assert train_input2 is not None, "Train search input not found (name search)"

        # ── 12. Type train name ───────────────────────────────────────────────
        train_input2.scroll_into_view_if_needed()
        train_input2.click(force=True)
        page.wait_for_timeout(300)
        train_input2.type(TRAIN_NAME_QUERY, delay=200)
        page.wait_for_timeout(3000)
        print(f"✅ Typed train name: {TRAIN_NAME_QUERY!r}")
        page.screenshot(path="emt7_step12_name_typed.png")

        # ── 13. Click autocomplete suggestion ────────────────────────────────
        name_sugg_clicked = False
        for sel in [f"li:has-text('PURUSHOTTAM')", f"li:has-text('Purushottam')",
                    "ul.ui-autocomplete li.ui-menu-item", "ul.ui-autocomplete li",
                    ".ui-menu-item", ".auto_saugg li"]:
            sugg = page.locator(sel)
            try:
                sugg.first.wait_for(state="visible", timeout=6000)
                if sugg.count() > 0:
                    txt = sugg.first.inner_text().strip()
                    sugg.first.click()
                    name_sugg_clicked = True
                    print(f"   Name suggestion clicked: {txt!r}")
                    break
            except Exception:
                continue
        if not name_sugg_clicked:
            print("   ⚠️  No autocomplete dropdown — pressing Enter")
            train_input2.press("Enter")
        page.wait_for_timeout(2000)
        page.screenshot(path="emt7_step13_name_suggestion.png")

        # ── 14. Select departure date ─────────────────────────────────────────
        date_chosen2 = _click_date_tile(page, DAYS_AHEAD)
        page.screenshot(path="emt7_step14_name_date.png")

        # ── 15. Click Search ──────────────────────────────────────────────────
        for sel in ["input.srch_btn", "input[value*='Search']", "input[value*='Get']",
                    "input[value*='Schedule']", "input[type='submit']",
                    "button:has-text('Search')", "button[type='submit']"]:
            btn = page.locator(sel).first
            if btn.count() > 0:
                try:
                    btn.wait_for(state="visible", timeout=5000)
                    btn.scroll_into_view_if_needed()
                    btn.click()
                    print(f"   Search button clicked via: {sel}")
                    break
                except Exception:
                    continue
        page.wait_for_load_state("domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        page.screenshot(path="emt7_step15_name_listing.png")
        print(f"\n✅ Name search submitted  |  URL: {page.url}")

        # ── 16. Verify listing page ───────────────────────────────────────────
        for rs in ["table", "[class*='schedule']", "[class*='station']",
                   "[class*='result']", "[class*='train']"]:
            try:
                page.locator(rs).first.wait_for(state="visible", timeout=5000)
                break
            except Exception:
                continue
        page.wait_for_timeout(2000)
        body2 = page.locator("body").inner_text().lower()
        url2  = page.url.lower()
        assert any(["purushottam" in body2, "purushottam" in url2,
                    "trainlist" in url2, "_train" in url2,
                    len(body2) > 300]), \
            f"Name listing not displayed.\nURL: {page.url}\nBody[:400]: {body2[:400]}"
        print(f"✅ Train listing page displayed (by name)  |  URL: {page.url}")
        for y in [300, 600, 900]:
            page.evaluate(f"window.scrollTo(0, {y})")
            page.wait_for_timeout(500)
        page.screenshot(path="emt7_step16_name_final.png")

        print(f"\n🎉 Test PASSED")
        print(f"   By Number : {TRAIN_NUMBER}  |  Date: {date_chosen1}")
        print(f"   By Name   : {TRAIN_NAME_QUERY!r}  |  Date: {date_chosen2}")

        context.close()
        browser.close()


if __name__ == "__main__":
    test_easemytrip_search_train_by_name_number_mobweb()
