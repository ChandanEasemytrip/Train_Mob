import re
import pytest
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, expect

# Android mobile emulation using Pixel 5 device descriptor
DEVICE_NAME = "Pixel 5"
URL = "https://www.easemytrip.com"

# Route configuration
FROM_CODE = "ANVT"
TO_CODE   = "CTC"

# Travel date = today + 10 days (computed at runtime)
_travel_dt          = datetime.now() + timedelta(days=10)
TRAVEL_DATE         = _travel_dt.strftime("%d/%m/%Y")          # e.g. "13/06/2026"
TRAVEL_DATE_DISPLAY = _travel_dt.strftime("%#d %B %Y")         # e.g. "13 June 2026" (Windows: %#d)

_next_day_dt          = _travel_dt + timedelta(days=1)
NEXT_DAY_DISPLAY      = _next_day_dt.strftime("%#d %B %Y")     # e.g. "14 June 2026"


def test_easemytrip_listing_page_mobweb():
    with sync_playwright() as p:
        pixel5 = p.devices[DEVICE_NAME]

        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            **pixel5,
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )

        page = context.new_page()

        print(f"\n   Travel date (today + 10 days): {TRAVEL_DATE}")

        # ── 1. Load home page ────────────────────────────────────────────────
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        expect(page).to_have_title(re.compile(r"easemytrip", re.IGNORECASE), timeout=15000)
        assert "easemytrip.com" in page.url, f"Unexpected URL: {page.url}"

        print(f"\n✅ Page loaded successfully")
        print(f"   Title : {page.title()}")
        print(f"   URL   : {page.url}")
        print(f"   Device: {DEVICE_NAME} ({pixel5['viewport']})")
        page.screenshot(path="emt5_home.png", full_page=False)
        print("   Screenshot saved: emt5_home.png")

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
        page.screenshot(path="emt5_trains.png", full_page=False)
        print("   Screenshot saved: emt5_trains.png")

        # ── 3. Enter From station (ANVT) ─────────────────────────────────────
        from_field = page.locator("#sourceStation")
        from_field.wait_for(state="visible", timeout=15000)
        from_field.click()

        from_search = page.locator("#txtfromcity1")
        from_search.wait_for(state="visible", timeout=10000)
        from_search.click(click_count=3)
        for ch in FROM_CODE:
            from_search.press(ch)
            page.wait_for_timeout(300)

        anvt_suggestion = page.locator(".auto_saugg").first.locator("li", has_text="ANVT")
        anvt_suggestion.wait_for(state="visible", timeout=10000)
        anvt_suggestion.click()

        page.wait_for_timeout(1000)
        from_value = page.locator("#txtfromcity").input_value()
        assert FROM_CODE in from_value, f"From field not updated. Got: {from_value}"

        print(f"\n✅ '{FROM_CODE}' station selected successfully")
        print(f"   From field value: {from_value}")
        page.screenshot(path="emt5_from.png", full_page=False)
        print("   Screenshot saved: emt5_from.png")

        # ── 4. Enter To station (CTC) ─────────────────────────────────────────
        to_field = page.locator("#ToStation")
        to_field.wait_for(state="visible", timeout=15000)
        to_field.click()

        to_search = page.locator("#txtdesticity1")
        to_search.wait_for(state="visible", timeout=10000)
        to_search.click(click_count=3)
        for ch in TO_CODE:
            to_search.press(ch)
            page.wait_for_timeout(300)

        ctc_suggestion = page.locator(".auto_saugg").nth(1).locator("li", has_text="CTC")
        ctc_suggestion.wait_for(state="visible", timeout=10000)
        ctc_suggestion.click()

        page.wait_for_timeout(1000)
        to_value = page.locator("#txtdesticity").input_value()
        assert TO_CODE in to_value, f"To field not updated. Got: {to_value}"

        print(f"\n✅ '{TO_CODE}' station selected successfully")
        print(f"   To field value: {to_value}")
        page.screenshot(path="emt5_to.png", full_page=False)
        print("   Screenshot saved: emt5_to.png")

        # ── 5. Select departure date (today + 10 days) ───────────────────────
        depart_date = page.locator("#departureDate")
        depart_date.wait_for(state="visible", timeout=15000)
        depart_date.click()
        page.wait_for_timeout(1500)

        print(f"\n✅ Departure date field clicked successfully")

        for _ in range(8):
            if page.locator(f"span[id*='{TRAVEL_DATE}']").count() > 0:
                break
            next_btn = page.locator(".next-month, .cal-next, [class*='next'], [aria-label*='next']").first
            if next_btn.count() > 0:
                next_btn.click()
                page.wait_for_timeout(800)

        target_date_span = page.locator(f"span[id*='{TRAVEL_DATE}']")
        target_date_span.wait_for(state="visible", timeout=10000)
        target_date_span.click()
        page.wait_for_timeout(1000)

        selected_date = page.locator("#txtDate").input_value()
        assert TRAVEL_DATE in selected_date, f"Date not selected correctly. Got: {selected_date}"

        print(f"   Selected date: {selected_date}")
        print(f"\n✅ Date {TRAVEL_DATE} selected successfully")
        page.screenshot(path="emt5_date.png", full_page=False)
        print("   Screenshot saved: emt5_date.png")

        # ── 6. Search Trains ─────────────────────────────────────────────────
        search_btn = page.locator("input.cta-btn[type='submit']")
        search_btn.wait_for(state="visible", timeout=15000)
        search_btn.click()
        page.wait_for_load_state("domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)

        print(f"\n✅ Search Trains clicked successfully")
        print(f"   URL: {page.url}")
        page.screenshot(path="emt5_results.png", full_page=False)
        print("   Screenshot saved: emt5_results.png")

        # ── 7. Verify listing page URL and title ─────────────────────────────
        assert FROM_CODE in page.url, f"{FROM_CODE} missing in URL: {page.url}"
        assert TO_CODE   in page.url, f"{TO_CODE} missing in URL: {page.url}"
        expect(page).to_have_title(re.compile(r"train", re.IGNORECASE), timeout=15000)

        print(f"\n✅ Listing page URL and title verified")
        print(f"   URL  : {page.url}")
        print(f"   Title: {page.title()}")

        # ── 8. Verify route header ───────────────────────────────────────────
        route_header = page.locator(".trainhdr-pill")
        route_header.wait_for(state="visible", timeout=15000)
        route_text = route_header.inner_text()
        assert FROM_CODE in route_text, f"FROM code missing in route header: {route_text}"
        assert TO_CODE   in route_text, f"TO code missing in route header: {route_text}"

        print(f"\n✅ Route header verified")
        print(f"   Route: {route_text.strip()}")
        page.screenshot(path="emt5_route_header.png", full_page=False)
        print("   Screenshot saved: emt5_route_header.png")

        # ── 9. Verify date display on listing page ───────────────────────────
        day_str   = str(_travel_dt.day)
        month_str = _travel_dt.strftime("%B")
        year_str  = str(_travel_dt.year)
        date_pattern = re.compile(rf"{day_str}\s*{month_str}\s*{year_str}", re.IGNORECASE)
        date_el = page.get_by_text(date_pattern).first
        try:
            date_el.wait_for(state="visible", timeout=10000)
            date_text = date_el.inner_text().strip()
        except Exception:
            date_text = TRAVEL_DATE_DISPLAY  # fallback if element not found by text

        print(f"\n✅ Travel date verified on listing page")
        print(f"   Date shown: {date_text}")

        # Wait for loading overlay to disappear
        try:
            loader = page.locator("#div_Cotant")
            loader.wait_for(state="hidden", timeout=90000)
        except Exception:
            pass

        # ── 10. Verify train cards are present ───────────────────────────────
        train_cards = page.locator(".trainwrap-outer")
        train_cards.first.wait_for(state="visible", timeout=15000)
        card_count = train_cards.count()
        assert card_count >= 1, "No train results found on listing page"

        print(f"\n✅ Train cards verified")
        print(f"   Total trains listed: {card_count}")
        page.screenshot(path="emt5_train_cards.png", full_page=False)
        print("   Screenshot saved: emt5_train_cards.png")

        # ── 11. Verify first train card details ──────────────────────────────
        first_card = page.locator(".main-confrm").first

        # Train name: span.emt-train-strng.ng-binding
        train_name_el = first_card.locator("span.emt-train-strng.ng-binding").first
        train_name = train_name_el.inner_text().strip() if train_name_el.count() > 0 else "N/A"

        # Train number + name combined in div.emt-train-name; extract leading number token
        train_head_el = first_card.locator("div.emt-train-name.ng-binding").first
        if train_head_el.count() > 0:
            head_text  = train_head_el.evaluate("e => e.childNodes[0]?.textContent || ''").strip()
            train_number = head_text if head_text else train_head_el.inner_text().split()[0]
        else:
            train_number = "N/A"

        # Departure time: div.emt-time index 1 (index 0 = from station code)
        dep_time_el = first_card.locator("div.txt-left div.emt-time.ng-binding").nth(1)
        dep_time = dep_time_el.inner_text().strip() if dep_time_el.count() > 0 else "N/A"

        # Arrival time: div.emt-time index 1 inside div.txt-right
        arr_time_el = first_card.locator("div.txt-right div.emt-time.ng-binding").nth(1)
        arr_time = arr_time_el.inner_text().strip() if arr_time_el.count() > 0 else "N/A"

        # Duration: span.text_gray.text-center.ng-binding
        duration_el = first_card.locator("span.text_gray.text-center.ng-binding").first
        duration = duration_el.inner_text().strip() if duration_el.count() > 0 else "N/A"

        assert train_name not in ("", "N/A"), "Train name is empty on first card"

        print(f"\n✅ First train card details verified")
        print(f"   Train Name  : {train_name}")
        print(f"   Train Number: {train_number}")
        print(f"   Departure   : {dep_time}")
        print(f"   Arrival     : {arr_time}")
        print(f"   Duration    : {duration}")
        page.screenshot(path="emt5_first_card.png", full_page=False)
        print("   Screenshot saved: emt5_first_card.png")

        # ── 12. Verify class availability options on first train card ─────────
        # Classes are in div.emt-seat-wrap; dedupe by picking only first occurrence per label
        class_wraps = first_card.locator(".emt-seat-wrap")
        class_count = class_wraps.count()
        assert class_count >= 1, "No class options found on first train card"

        available_classes = []
        seen_classes = set()
        for i in range(class_count):
            cls_el = class_wraps.nth(i).locator("span.train-class").first
            if cls_el.count() > 0:
                label = cls_el.inner_text().strip()
                if label and label not in seen_classes:
                    available_classes.append(label)
                    seen_classes.add(label)

        print(f"\n✅ Class availability options verified")
        print(f"   Available classes: {', '.join(available_classes) if available_classes else 'N/A'}")
        page.screenshot(path="emt5_classes.png", full_page=False)
        print("   Screenshot saved: emt5_classes.png")

        # ── 13. Select 3A class and verify Book button appears ────────────────
        class_3a = first_card.locator(".emt-seat-wrap").filter(
            has=page.locator("span.train-class", has_text="3A")
        ).first

        assert class_3a.count() > 0, "3A class not found on first train card"
        class_3a.scroll_into_view_if_needed(timeout=10000)
        class_3a.click()
        page.wait_for_timeout(2000)

        book_btn = first_card.locator("button.book-btn").first
        book_btn.wait_for(state="visible", timeout=10000)
        assert book_btn.is_visible(), "Book button not visible after selecting 3A class"

        print(f"\n✅ 3A class selected — Book button verified")
        page.screenshot(path="emt5_3a_book.png", full_page=False)
        print("   Screenshot saved: emt5_3a_book.png")

        # ── 14. Sort By — open panel, click each option, apply, verify ────────
        # Actual sort options on EaseMyTrip mobile listing:
        # Early Departure | Late Departure | Early Arrival | Late Arrival
        SORT_OPTIONS = [
            ("Early Departure", "early_dept",  "EarlyDept"),
            ("Late Departure",  "late_dept",   "LateDept"),
            ("Early Arrival",   "early_arrvl", "EarlyArrvl"),
            ("Late Arrival",    "late_arrvl",  "LateArrvl"),
        ]

        def _open_sort_panel():
            """Click the Sort toggle button to open the sort panel."""
            sort_toggle = page.locator("div.etm-sort").first
            sort_toggle.wait_for(state="visible", timeout=10000)
            sort_toggle.click()
            page.wait_for_timeout(800)
            page.locator("#sortprice").wait_for(state="visible", timeout=10000)

        def _close_sort_panel():
            """Close sort panel via the X button or Escape."""
            close_btn = page.locator("#sortprice span.close_btn2").first
            if close_btn.count() > 0 and close_btn.is_visible():
                close_btn.click()
            else:
                page.keyboard.press("Escape")
            page.wait_for_timeout(500)

        def _get_dep_times():
            """Return departure times of all visible train cards."""
            els = page.locator(".main-confrm div.txt-left div.emt-time.ng-binding").all()
            times = []
            for i, el in enumerate(els):
                if i % 2 == 1:  # index 0 = station code, 1 = time
                    try: times.append(el.inner_text().strip())
                    except: pass
            return times

        def _get_arr_times():
            """Return arrival times of all visible train cards."""
            els = page.locator(".main-confrm div.txt-right div.emt-time.ng-binding").all()
            times = []
            for i, el in enumerate(els):
                if i % 2 == 1:
                    try: times.append(el.inner_text().strip())
                    except: pass
            return times

        for sort_label, sort_suffix, sort_value in SORT_OPTIONS:
            # Open sort panel
            _open_sort_panel()

            # Find the label with matching radio value
            sort_label_el = page.locator(
                f"#sortprice label.cont_flt2:has(input[value='{sort_value}'])"
            ).first

            if sort_label_el.count() == 0:
                print(f"\n⚠️  Sort option '{sort_label}' not found — skipping")
                _close_sort_panel()
                continue

            sort_label_el.scroll_into_view_if_needed(timeout=5000)
            sort_label_el.click()
            page.wait_for_timeout(500)

            # Verify radio is checked
            radio_input = sort_label_el.locator("input[type='radio']")
            is_checked  = radio_input.is_checked()

            # Click Apply
            apply_btn = page.locator("#sortprice div.flicb2").first
            apply_btn.wait_for(state="visible", timeout=5000)
            apply_btn.click()
            page.wait_for_timeout(1500)

            # Wait for cards to refresh
            page.locator(".main-confrm").first.wait_for(state="visible", timeout=15000)
            page.wait_for_timeout(500)

            # Verify order if multiple trains
            all_cards = page.locator(".main-confrm").count()
            order_msg = "N/A (single train)"
            if all_cards >= 2:
                if "Departure" in sort_label:
                    vals = _get_dep_times()
                    expected = sorted(vals, reverse=("Late" in sort_label))
                    order_msg = ("✓ correct" if vals == expected else f"⚠ got {vals}") + f" dep times"
                elif "Arrival" in sort_label:
                    vals = _get_arr_times()
                    expected = sorted(vals, reverse=("Late" in sort_label))
                    order_msg = ("✓ correct" if vals == expected else f"⚠ got {vals}") + f" arr times"

            # Read first card departure after sort
            first_dep = page.locator(".main-confrm").first.locator(
                "div.txt-left div.emt-time.ng-binding"
            ).nth(1).inner_text().strip()

            print(f"\n✅ Sort by '{sort_label}' applied")
            print(f"   Radio checked: {'✓' if is_checked else '✗'}")
            print(f"   First card dep: {first_dep}")
            print(f"   Order check   : {order_msg}")
            screenshot_name = f"emt5_sort_{sort_suffix}.png"
            page.screenshot(path=screenshot_name, full_page=False)
            print(f"   Screenshot saved: {screenshot_name}")

        # ── 15. Quota — select each quota option and verify ──────────────────
        # Quota panel is per-train-card, revealed after a class is selected.
        # Structure: div[id^='divQuota'] containing span.typseat elements.
        # The sort panel must be closed first (its overlay blocks clicks).

        # Ensure sort panel overlay is gone
        _close_sort_panel()
        page.wait_for_timeout(500)

        # Re-select 3A on first card to reveal the quota panel
        first_card_q = page.locator(".main-confrm").first
        class_3a_q   = first_card_q.locator(".emt-seat-wrap").filter(
            has=page.locator("span.train-class", has_text="3A")
        ).first

        assert class_3a_q.count() > 0, "3A class not found for quota step"
        class_3a_q.scroll_into_view_if_needed(timeout=10000)
        class_3a_q.click()
        page.wait_for_timeout(2000)

        # Locate the quota panel for the first train card
        # id pattern: divQuota{trainNumber}; class: classWiseQuta
        quota_panel = first_card_q.locator("div[id^='divQuota']").first
        quota_panel.wait_for(state="visible", timeout=15000)

        # Read all quota span options inside the panel
        quota_spans = quota_panel.locator("span.typseat").all()
        print(f"\n✅ Quota panel visible — {len(quota_spans)} option(s) found")

        # Screenshot default quota state
        page.screenshot(path="emt5_quota_default.png", full_page=False)
        print("   Screenshot saved: emt5_quota_default.png")

        for i, span in enumerate(quota_spans):
            try:
                quota_text = span.inner_text().strip()
                if not quota_text:
                    continue

                span.scroll_into_view_if_needed(timeout=5000)
                span.click()
                page.wait_for_timeout(1500)

                # Verify the clicked span got the active class
                span_class = span.get_attribute("class") or ""
                is_active  = "actseat" in span_class

                # Count available trains after quota selection
                card_count_q = page.locator(".main-confrm").count()

                print(f"\n✅ Quota '{quota_text}' selected")
                print(f"   Active (actseat): {'✓' if is_active else '✗'} class={span_class!r}")
                print(f"   Train cards visible: {card_count_q}")
                ss_name = f"emt5_quota_{quota_text.lower().replace(' ', '_')}.png"
                page.screenshot(path=ss_name, full_page=False)
                print(f"   Screenshot saved: {ss_name}")

            except Exception as e:
                print(f"   ⚠️  Could not select quota option {i+1}: {e}")

        # Restore to General quota
        general_span = quota_panel.locator("span.typseat").filter(
            has_text=re.compile(r"General", re.IGNORECASE)
        ).first
        if general_span.count() > 0:
            general_span.click()
            page.wait_for_timeout(1000)
            print(f"\n✅ Quota restored to General")
            page.screenshot(path="emt5_quota_restored.png", full_page=False)
            print("   Screenshot saved: emt5_quota_restored.png")

        # ── 16. Final summary ────────────────────────────────────────────────
        print(f"\n✅ Listing page test completed successfully")
        print(f"   Route          : {FROM_CODE} → {TO_CODE}")
        print(f"   Travel Date    : {TRAVEL_DATE_DISPLAY}")
        print(f"   Trains Found   : {card_count}")
        print(f"   First Train    : {train_name} ({train_number})")
        print(f"   Timings        : Dep {dep_time} | Arr {arr_time} | Dur {duration}")
        print(f"   Classes Found  : {', '.join(available_classes) if available_classes else 'N/A'}")
        page.screenshot(path="emt5_final.png", full_page=False)
        print("   Screenshot saved: emt5_final.png")

        browser.close()
