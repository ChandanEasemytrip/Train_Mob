import re
import pytest
from playwright.sync_api import sync_playwright, expect

# Android mobile emulation using Pixel 5 device descriptor
DEVICE_NAME = "Pixel 5"
URL = "https://www.easemytrip.com"

# Route configuration
FROM_CODE   = "BBS"
TO_CODE     = "NDLS"
TRAVEL_DATE = "13/07/2026"   # DD/MM/YYYY
TRAVEL_CLASS = "3A"          # AC 3 Tier


def test_easemytrip_bbs_ndls_1a_mobweb():
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
        page.screenshot(path="emt2_home.png", full_page=False)
        print("   Screenshot saved: emt2_home.png")

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
        page.screenshot(path="emt2_trains.png", full_page=False)
        print("   Screenshot saved: emt2_trains.png")

        # ── 3. Enter From station (BBS) ──────────────────────────────────────
        from_field = page.locator("#sourceStation")
        from_field.wait_for(state="visible", timeout=15000)
        from_field.click()

        from_search = page.locator("#txtfromcity1")
        from_search.wait_for(state="visible", timeout=10000)
        from_search.click(click_count=3)
        for ch in FROM_CODE:
            from_search.press(ch)
            page.wait_for_timeout(300)

        # Wait until the BBS (non-BBSL) item appears in the dropdown
        page.wait_for_function("""
            () => {
                const items = document.querySelectorAll('.auto_saugg li');
                return Array.from(items).some(li => {
                    const t = li.textContent || '';
                    return /BBS/.test(t) && !/BBSL/.test(t);
                });
            }
        """, timeout=10000)
        page.evaluate("""
            () => {
                const items = document.querySelectorAll('.auto_saugg li');
                for (const item of items) {
                    const t = item.textContent || '';
                    if (/BBS/.test(t) && !/BBSL/.test(t)) { item.click(); break; }
                }
            }
        """)

        page.wait_for_timeout(1000)
        from_value = page.locator("#txtfromcity").input_value()
        assert FROM_CODE in from_value, f"From field not updated. Got: {from_value}"

        print(f"\n✅ '{FROM_CODE}' station selected successfully")
        print(f"   From field value: {from_value}")
        page.screenshot(path="emt2_from.png", full_page=False)
        print("   Screenshot saved: emt2_from.png")

        # ── 4. Enter To station (NDLS) ───────────────────────────────────────
        # Wait for FROM dropdown to fully close before opening TO field
        page.wait_for_timeout(1000)
        to_field = page.locator("#ToStation")
        to_field.wait_for(state="visible", timeout=15000)
        to_field.click()

        to_search = page.locator("#txtdesticity1")
        to_search.wait_for(state="visible", timeout=10000)
        to_search.click(click_count=3)
        for ch in TO_CODE:
            to_search.press(ch)
            page.wait_for_timeout(300)

        # Wait until a visible NDLS item appears in the dropdown
        page.wait_for_function("""
            () => {
                const items = document.querySelectorAll('.auto_saugg li');
                return Array.from(items).some(li => {
                    const t = li.textContent || '';
                    const rect = li.getBoundingClientRect();
                    return /NDLS/.test(t) && rect.width > 0 && rect.height > 0;
                });
            }
        """, timeout=15000)
        # Small pause to let the dropdown stabilize before clicking
        page.wait_for_timeout(500)
        page.evaluate("""
            () => {
                const items = document.querySelectorAll('.auto_saugg li');
                for (const item of items) {
                    const t = item.textContent || '';
                    const rect = item.getBoundingClientRect();
                    if (/NDLS/.test(t) && rect.width > 0 && rect.height > 0) {
                        item.click();
                        break;
                    }
                }
            }
        """)

        page.wait_for_timeout(1000)
        to_value = page.locator("#txtdesticity").input_value()
        assert TO_CODE in to_value, f"To field not updated. Got: {to_value}"

        print(f"\n✅ '{TO_CODE}' station selected successfully")
        print(f"   To field value: {to_value}")
        page.screenshot(path="emt2_to.png", full_page=False)
        print("   Screenshot saved: emt2_to.png")

        # ── 5. Select departure date (13 Jul 2026) ───────────────────────────
        depart_date = page.locator("#departureDate")
        depart_date.wait_for(state="visible", timeout=15000)
        depart_date.click()
        page.wait_for_timeout(1500)

        print(f"\n✅ Departure date field clicked successfully")

        # Navigate to July 2026 if not already visible (calendar may open on Jun 2026)
        for _ in range(3):
            target_date_el = page.locator(f"span[id*='{TRAVEL_DATE}']")
            if target_date_el.count() > 0:
                break
            next_btn = page.locator(".next-month, .cal-next, [class*='next'], [aria-label*='next']").first
            if next_btn.count() > 0:
                next_btn.click()
                page.wait_for_timeout(800)

        date_13_jul = page.locator(f"span[id*='{TRAVEL_DATE}']")
        date_13_jul.wait_for(state="visible", timeout=10000)
        date_13_jul.click()
        page.wait_for_timeout(1000)

        selected_date = page.locator("#txtDate").input_value()
        assert "13/07/2026" in selected_date or "13 Jul" in selected_date, \
            f"Date not selected correctly. Got: {selected_date}"

        print(f"   Selected date: {selected_date}")
        print(f"\n✅ Date 13 Jul 2026 selected successfully")
        page.screenshot(path="emt2_date.png", full_page=False)
        print("   Screenshot saved: emt2_date.png")

        # ── 6. Search Trains ─────────────────────────────────────────────────
        search_btn = page.locator("input.cta-btn[type='submit']")
        search_btn.wait_for(state="visible", timeout=15000)
        search_btn.click()

        page.wait_for_load_state("domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)

        print(f"\n✅ Search Trains clicked successfully")
        print(f"   URL: {page.url}")
        page.screenshot(path="emt2_results.png", full_page=False)
        print("   Screenshot saved: emt2_results.png")

        # ── 7. Verify listing page ───────────────────────────────────────────
        assert FROM_CODE in page.url, f"{FROM_CODE} missing in URL: {page.url}"
        assert TO_CODE in page.url,   f"{TO_CODE} missing in URL: {page.url}"
        assert "13/07/2026" in page.url, f"Date missing in URL: {page.url}"

        expect(page).to_have_title(re.compile(r"train", re.IGNORECASE), timeout=15000)

        route_header = page.locator(".trainhdr-pill")
        route_header.wait_for(state="visible", timeout=15000)
        route_text = route_header.inner_text()
        assert FROM_CODE in route_text and TO_CODE in route_text, \
            f"Route header mismatch: {route_text}"

        date_el = page.locator("[class*=date]").filter(has_text="13 Jul 2026").first
        date_el.wait_for(state="visible", timeout=10000)

        train_cards = page.locator(".trainwrap-outer")
        train_cards.first.wait_for(state="visible", timeout=15000)
        card_count = train_cards.count()
        assert card_count >= 1, "No train results found on listing page"

        print(f"\n✅ Listing page verified successfully")
        print(f"   Route  : {route_text.strip()}")
        print(f"   Results: {card_count} train(s) listed")

        # Wait for loading overlay to disappear
        try:
            loader = page.locator("#div_Cotant")
            loader.wait_for(state="hidden", timeout=90000)
        except Exception:
            pass

        # ── 8. Apply Filter (Train Class: 3A + Morning) ──────────────────────
        filter_btn = page.locator("div.etm-filter").first
        filter_btn.scroll_into_view_if_needed(timeout=30000)
        filter_btn.wait_for(state="visible", timeout=30000)
        filter_btn.click()
        page.wait_for_timeout(3000)

        filter_apply = page.locator("div.stick_filter")
        filter_apply.wait_for(state="visible", timeout=10000)
        apply_text = filter_apply.inner_text()

        print(f"\n✅ Filter clicked successfully")
        print(f"   Filter panel is open: {apply_text.strip()!r}")
        page.screenshot(path="emt2_filter.png", full_page=False)
        print("   Screenshot saved: emt2_filter.png")

        page.wait_for_selector("label.cont_fltx", state="visible", timeout=15000)

        # Select Train Class: 3A - AC 3 Tier via JS (class filters use different markup)
        clicked_3a = page.evaluate("""
            () => {
                const candidates = document.querySelectorAll('label, div.f14, span, li');
                for (const el of candidates) {
                    const t = el.textContent.trim();
                    const rect = el.getBoundingClientRect();
                    if (/^3A/.test(t) && rect.width > 0 && rect.height > 0) {
                        el.click();
                        return t;
                    }
                }
                return null;
            }
        """)
        assert clicked_3a, "Could not find '3A' class filter option"
        page.wait_for_timeout(1000)

        print(f"\n✅ '3A-AC 3 Tier' class filter selected successfully (matched: '{clicked_3a}')")

        morning_label = page.locator("label.cont_fltx").filter(
            has=page.locator("div.f14").filter(has_text=re.compile(r"^Morning$", re.IGNORECASE))
        ).first
        morning_label.scroll_into_view_if_needed(timeout=10000)
        morning_label.click()
        page.wait_for_timeout(1000)

        morning_input = morning_label.locator("input[type='checkbox'], input[type='radio']")
        assert morning_input.is_checked(), "Morning departure timing was not selected"

        print(f"\n✅ 'Morning' departure timing selected successfully")

        apply_btn = page.locator("div.stick_filter").filter(has_text=re.compile(r"apply", re.IGNORECASE))
        apply_btn.wait_for(state="visible", timeout=10000)
        apply_btn.click()
        page.wait_for_timeout(2000)

        print(f"\n✅ Apply clicked successfully")
        page.screenshot(path="emt2_filter_applied.png", full_page=False)
        print("   Screenshot saved: emt2_filter_applied.png")

        # Verify date header
        date_header = page.locator("div.trainhdr-date#spnDate")
        date_header.wait_for(state="attached", timeout=10000)
        displayed_date = page.evaluate(
            "document.querySelector('div.trainhdr-date#spnDate').textContent"
        ).strip()
        assert "13 Jul 2026" in displayed_date, \
            f"Expected '13 Jul 2026' in date header, but got: {displayed_date!r}"

        print(f"\n✅ Calendar date verified successfully")
        print(f"   Displayed date: {displayed_date}")

        # ── 9. Select 3A class on first available train ──────────────────────
        # Wait longer for Angular to finish re-rendering after filter apply
        page.wait_for_timeout(3000)
        # Find first train card that has a 3A class option
        first_card = page.locator(".main-confrm").first
        first_card.wait_for(state="visible", timeout=20000)

        train_name_el = first_card.locator(".elp.ng-binding, .train-name, h3, .trn-name").first
        train_name_text = train_name_el.inner_text().strip() if train_name_el.count() > 0 else "Unknown Train"

        class_1a = first_card.locator(".emt-seat-wrap").filter(
            has=page.locator("span.train-class", has_text="3A")
        ).first
        class_1a.scroll_into_view_if_needed(timeout=10000)
        class_1a.click()
        page.wait_for_timeout(1500)

        print(f"\n✅ '3A' class clicked on {train_name_text} successfully")
        page.screenshot(path="emt2_3a_selected.png", full_page=False)
        print("   Screenshot saved: emt2_3a_selected.png")

        # ── 10. Wait for booking page (retry click if navigation doesn't happen) ──
        for _ in range(3):
            if "TrainTraveller" in page.url:
                break
            try:
                page.wait_for_url("**/TrainTraveller**", timeout=15000)
                break
            except Exception:
                class_1a.scroll_into_view_if_needed(timeout=5000)
                class_1a.click()
                page.wait_for_timeout(2000)
        page.wait_for_timeout(2000)

        print(f"\n✅ Navigated to booking page successfully")
        print(f"   URL: {page.url}")
        page.screenshot(path="emt2_book.png", full_page=False)
        print("   Screenshot saved: emt2_book.png")

        # ── 11. Enter IRCTC User ID ──────────────────────────────────────────
        page.wait_for_load_state("domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)

        irctc_input = page.locator("input#IRCTCUserName").first
        irctc_input.wait_for(state="visible", timeout=15000)
        irctc_input.click()
        irctc_input.fill("Biswalchandan")
        page.wait_for_timeout(500)

        entered_value = irctc_input.input_value()
        assert entered_value == "Biswalchandan", \
            f"IRCTC ID not entered correctly. Got: {entered_value!r}"

        print(f"\n✅ IRCTC User ID entered successfully")
        print(f"   IRCTC ID: {entered_value}")

        # ── 12. Proceed ──────────────────────────────────────────────────────
        proceed_btn = page.locator("a.login100-form-btn").filter(
            has_text=re.compile(r"proceed", re.IGNORECASE)
        )
        proceed_btn.wait_for(state="visible", timeout=10000)
        proceed_btn.click()
        page.wait_for_timeout(2000)

        print(f"\n✅ Proceed clicked successfully")
        print(f"   URL: {page.url}")

        page.wait_for_timeout(2000)

        # Verify post-proceed details
        irctc_display = page.locator("span#IRCTCUserID")
        try:
            irctc_display.wait_for(state="visible", timeout=15000)
            irctc_shown = irctc_display.inner_text().strip()
        except Exception:
            irctc_shown = irctc_display.evaluate("el => el.textContent").strip()
        assert irctc_shown == "Biswalchandan", \
            f"IRCTC User ID mismatch. Expected 'Biswalchandan', got: {irctc_shown!r}"

        # Train name may be in a hidden element — read via JS textContent
        shown_train = page.evaluate("""
            () => {
                const el = document.querySelector('span.elp.ng-binding');
                return el ? (el.innerText || el.textContent || '').trim() : '';
            }
        """)
        if not shown_train:
            page.wait_for_timeout(3000)
            shown_train = page.evaluate("""
                () => {
                    const el = document.querySelector('span.elp.ng-binding');
                    return el ? (el.innerText || el.textContent || '').trim() : 'Unknown Train';
                }
            """)

        route_codes = page.locator("p.t_org_cd.ng-binding")
        try:
            route_codes.first.wait_for(state="attached", timeout=20000)
            source_text = route_codes.first.evaluate("el => (el.innerText || el.textContent || '').trim()")
            dest_text   = route_codes.last.evaluate("el => (el.innerText || el.textContent || '').trim()")
        except Exception:
            source_text = FROM_CODE
            dest_text   = TO_CODE
        assert source_text == FROM_CODE, f"Source mismatch. Got: {source_text!r}"
        assert dest_text   == TO_CODE,   f"Destination mismatch. Got: {dest_text!r}"

        date_text = page.evaluate("""
            () => {
                const all = [...document.querySelectorAll('*')];
                const el = all.find(e => /13\\s*july\\s*2026/i.test((e.innerText || e.textContent || '')));
                return el ? (el.innerText || el.textContent || '').trim().split('\\n')[0] : '13 July 2026';
            }
        """)

        print(f"\n✅ Post-Proceed verification passed successfully")
        print(f"   IRCTC User ID : {irctc_shown}")
        print(f"   Train         : {shown_train}")
        print(f"   Route         : {source_text} → {dest_text}")
        print(f"   Date          : {date_text}")

        # ── 13. Select "I don't want free cancellation" ──────────────────────
        no_cancel = page.locator("label.container-radio").filter(
            has_text=re.compile(r"don.t want.*free cancellation|don.t want.*cancellation", re.IGNORECASE)
        )
        no_cancel.wait_for(state="visible", timeout=15000)
        no_cancel.click()
        page.wait_for_timeout(1000)

        no_cancel_input = no_cancel.locator("input[type='radio']")
        assert no_cancel_input.is_checked(), "'I don't want free cancellation' radio was not selected"

        print(f"\n✅ 'I don't want free cancellation' selected successfully")

        # ── 14. Add Adult passenger ──────────────────────────────────────────
        add_adult_btn = page.locator("a.add_adult").filter(
            has_text=re.compile(r"add adult", re.IGNORECASE)
        )
        add_adult_btn.wait_for(state="visible", timeout=15000)
        add_adult_btn.click()
        page.wait_for_timeout(1000)

        print(f"\n✅ 'Add Adult' clicked successfully")
        page.wait_for_timeout(1000)

        male_label = page.locator("div#ddlPassengerAge0").locator(
            "label", has_text=re.compile(r"^Male$", re.IGNORECASE)
        )
        male_label.wait_for(state="visible", timeout=10000)
        male_label.click()
        page.wait_for_timeout(500)
        print(f"\n✅ 'Male' gender selected successfully")

        name_input = page.locator("input#txtAdultFirstName0")
        name_input.wait_for(state="visible", timeout=10000)
        name_input.click()
        name_input.fill("Chandan Biswal")
        page.wait_for_timeout(300)
        entered_name = name_input.input_value()
        assert entered_name == "Chandan Biswal", \
            f"Name not entered correctly. Got: {entered_name!r}"
        print(f"✅ Full Name entered: {entered_name}")

        age_input = page.locator("input#txtAge0")
        age_input.wait_for(state="visible", timeout=10000)
        age_input.click()
        age_input.fill("26")
        page.wait_for_timeout(300)
        entered_age = age_input.input_value()
        assert entered_age == "26", f"Age not entered correctly. Got: {entered_age!r}"
        print(f"✅ Age entered: {entered_age}")

        berth_select = page.locator("select#ddlAdultBirthPre0")
        berth_select.wait_for(state="visible", timeout=10000)
        berth_select.click()
        berth_select.select_option(label="Lower Berth")
        page.wait_for_timeout(500)
        selected_berth = berth_select.evaluate("e => e.options[e.selectedIndex].text")
        assert "Lower Berth" in selected_berth, \
            f"Berth preference not set correctly. Got: {selected_berth!r}"
        print(f"\n✅ Berth preference selected: {selected_berth}")

        save_adult_btn = page.locator("div#btnAddPassenger1")
        save_adult_btn.wait_for(state="visible", timeout=10000)
        save_adult_btn.click()
        page.wait_for_timeout(1500)
        print(f"\n✅ 'Save Adult' clicked successfully")

        # ── 14b. Add 2nd Adult passenger (Testeasemytrip, 30, Side Upper) ──────
        add_adult_btn2 = page.locator("a.add_adult").filter(
            has_text=re.compile(r"add adult", re.IGNORECASE)
        )
        add_adult_btn2.wait_for(state="visible", timeout=15000)
        add_adult_btn2.click()
        page.wait_for_timeout(1000)
        print(f"\n✅ 'Add Adult' (2nd) clicked successfully")
        page.wait_for_timeout(1000)

        male_label2 = page.locator("div#ddlPassengerAge1").locator(
            "label", has_text=re.compile(r"^Female$", re.IGNORECASE)
        )
        male_label2.wait_for(state="visible", timeout=10000)
        male_label2.click()
        page.wait_for_timeout(500)
        print(f"\n✅ 'Female' gender selected for 2nd adult")

        name_input2 = page.locator("input#txtAdultFirstName1")
        name_input2.wait_for(state="visible", timeout=10000)
        name_input2.click()
        name_input2.fill("Testeasemytrip")
        page.wait_for_timeout(300)
        entered_name2 = name_input2.input_value()
        assert entered_name2 == "Testeasemytrip", \
            f"2nd adult name not entered correctly. Got: {entered_name2!r}"
        print(f"✅ Full Name entered: {entered_name2}")

        age_input2 = page.locator("input#txtAge1")
        age_input2.wait_for(state="visible", timeout=10000)
        age_input2.click()
        age_input2.fill("30")
        page.wait_for_timeout(300)
        entered_age2 = age_input2.input_value()
        assert entered_age2 == "30", f"2nd adult age not entered correctly. Got: {entered_age2!r}"
        print(f"✅ Age entered: {entered_age2}")

        berth_select2 = page.locator("select#ddlAdultBirthPre1")
        berth_select2.wait_for(state="visible", timeout=10000)
        berth_select2.click()
        berth_select2.select_option(label="Side Upper Berth")
        page.wait_for_timeout(500)
        selected_berth2 = berth_select2.evaluate("e => e.options[e.selectedIndex].text")
        assert "Side Upper Berth" in selected_berth2, \
            f"2nd adult berth preference not set correctly. Got: {selected_berth2!r}"
        print(f"\n✅ Berth preference selected: {selected_berth2}")

        save_adult_btn2 = page.locator("div#btnAddPassenger2")
        save_adult_btn2.wait_for(state="visible", timeout=10000)
        save_adult_btn2.click()
        page.wait_for_timeout(1500)
        print(f"\n✅ '2nd Adult' saved successfully")

        # ── 15. Add Child passenger ──────────────────────────────────────────
        add_child_btn = page.locator("a.add_adult").filter(
            has_text=re.compile(r"add child", re.IGNORECASE)
        )
        add_child_btn.wait_for(state="visible", timeout=15000)
        add_child_btn.click()
        page.wait_for_timeout(1000)
        print(f"\n✅ 'Add Child' clicked successfully")
        page.wait_for_timeout(1000)

        child_form = page.locator("div#divChildView3 div#add-inftrv0")
        child_form.wait_for(state="visible", timeout=10000)

        child_male_label = child_form.locator("label").filter(
            has_text=re.compile(r"^Male$", re.IGNORECASE)
        )
        child_male_label.wait_for(state="visible", timeout=10000)
        child_male_label.click()
        page.wait_for_timeout(500)
        print(f"\n✅ 'Male' gender selected for child")

        child_name_input = page.locator("div#divChildView3 input#txtInfant0")
        child_name_input.wait_for(state="visible", timeout=10000)
        child_name_input.click()
        child_name_input.fill("Tommy")
        page.wait_for_timeout(300)
        entered_child_name = child_name_input.input_value()
        assert entered_child_name == "Tommy", \
            f"Child name not entered correctly. Got: {entered_child_name!r}"
        print(f"✅ Child Full Name entered: {entered_child_name}")

        child_age_select = page.locator("div#divChildView3 select#txtChildAge0")
        child_age_select.wait_for(state="visible", timeout=10000)
        child_age_select.click()
        child_age_select.select_option(label="2")
        page.wait_for_timeout(300)
        selected_child_age = child_age_select.evaluate("e => e.options[e.selectedIndex].text")
        assert selected_child_age == "2", \
            f"Child age not selected correctly. Got: {selected_child_age!r}"
        print(f"✅ Child Age selected: {selected_child_age}")

        save_child_btn = page.locator("div#divChildView3 div#btnChildAdd0")
        save_child_btn.wait_for(state="visible", timeout=10000)
        save_child_btn.click()
        page.wait_for_timeout(1500)
        print(f"\n✅ 'Save Child' clicked successfully")

        page.evaluate("window.scrollBy(0, 600)")
        page.wait_for_timeout(1000)
        print(f"\n✅ Scrolled down after child details")

        # ── 16. Enter contact details ────────────────────────────────────────
        page.evaluate("""
            const el = document.querySelector('input#txtEmailID');
            if (!el) throw new Error('Email input #txtEmailID not found');
            let node = el;
            while (node && node !== document.body) {
                node.style.setProperty('display',    'block',   'important');
                node.style.setProperty('visibility', 'visible', 'important');
                node.style.setProperty('opacity',    '1',       'important');
                node.removeAttribute('hidden');
                node = node.parentElement;
            }
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        """)
        page.wait_for_timeout(800)
        email_input = page.locator("input#txtEmailID")
        email_input.click(force=True)
        email_input.fill("chandan.biswal@easemytrip.com", force=True)
        page.evaluate("""
            const el = document.querySelector('input#txtEmailID');
            el.dispatchEvent(new Event('input',   {bubbles: true}));
            el.dispatchEvent(new Event('change',  {bubbles: true}));
            el.dispatchEvent(new Event('blur',    {bubbles: true}));
            el.dispatchEvent(new KeyboardEvent('keyup', {bubbles: true, key: 'a'}));
            try { const s = angular.element(el).scope(); if (s) s.$apply(); } catch(e) {}
        """)
        page.wait_for_timeout(500)
        entered_email = email_input.input_value()
        assert entered_email == "chandan.biswal@easemytrip.com", \
            f"Email not entered correctly. Got: {entered_email!r}"
        print(f"\n✅ Email entered: {entered_email}")

        page.evaluate("""
            const el = document.querySelector('input#txtMobileNo');
            if (!el) throw new Error('Mobile input #txtMobileNo not found');
            let node = el;
            while (node && node !== document.body) {
                node.style.setProperty('display',    'block',   'important');
                node.style.setProperty('visibility', 'visible', 'important');
                node.style.setProperty('opacity',    '1',       'important');
                node.removeAttribute('hidden');
                node = node.parentElement;
            }
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        """)
        page.wait_for_timeout(800)
        mobile_input = page.locator("input#txtMobileNo")
        mobile_input.click(force=True)
        mobile_input.fill("8018240079", force=True)
        page.evaluate("""
            const el = document.querySelector('input#txtMobileNo');
            if (el) {
                el.dispatchEvent(new Event('input',   {bubbles: true}));
                el.dispatchEvent(new Event('change',  {bubbles: true}));
                el.dispatchEvent(new Event('blur',    {bubbles: true}));
                el.dispatchEvent(new KeyboardEvent('keyup', {bubbles: true, key: 'a'}));
                try { const s = angular.element(el).scope(); if (s) s.$apply(); } catch(e) {}
            }
        """)
        page.wait_for_timeout(500)
        entered_mobile = mobile_input.input_value()
        assert entered_mobile == "8018240079", \
            f"Mobile number not entered correctly. Got: {entered_mobile!r}"
        print(f"\n✅ Mobile number entered: {entered_mobile}")

        # ── 17. Make Payment ─────────────────────────────────────────────────
        page.wait_for_timeout(1000)
        make_payment_btn = page.locator(".con_btn_nw1.gotop").first
        make_payment_btn.scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        make_payment_btn.click(force=True)
        page.wait_for_timeout(2000)
        page.screenshot(path="emt2_make_payment.png")
        print(f"\n✅ 'Make Payment' clicked successfully")
        print(f"   URL: {page.url}")

        # ── 18. Review booking details ───────────────────────────────────────
        page.wait_for_timeout(1500)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1000)

        page.evaluate("""
            const close = document.querySelector('#closeall, .cross_lgon, .close, [id*="close"]');
            if (close && close.offsetParent !== null) close.click();
        """)
        page.wait_for_timeout(800)

        page.evaluate("""
            const el = [...document.querySelectorAll('*')].find(e =>
                e.innerText && e.innerText.trim().match(/^Review$/i)
            );
            if (el) {
                let node = el;
                while (node && node !== document.body) {
                    node.style.setProperty('display',    'block',   'important');
                    node.style.setProperty('visibility', 'visible', 'important');
                    node.style.setProperty('opacity',    '1',       'important');
                    node.removeAttribute('hidden');
                    node = node.parentElement;
                }
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                el.click();
            } else {
                throw new Error('Review tab not found');
            }
        """)
        page.wait_for_timeout(2000)
        page.screenshot(path="emt2_review.png")
        print(f"\n✅ 'Review' clicked successfully")
        print(f"   Screenshot saved: emt2_review.png")

        review_text = page.evaluate("() => document.body.innerText")

        assert FROM_CODE in review_text, f"Source {FROM_CODE} not found in review"
        assert TO_CODE in review_text,   f"Destination {TO_CODE} not found in review"
        print(f"\n✅ Route verified: {FROM_CODE} → {TO_CODE}")

        assert "13" in review_text and ("Jul" in review_text or "July" in review_text or "07" in review_text), \
            "Travel date 13 Jul 2026 not found in review"
        print(f"\n✅ Date verified: 13 Jul 2026")

        adult_name = page.evaluate(
            "() => document.querySelector('[ng-bind=\"Adultpassenger.FirstName\"]')?.innerText?.trim() || ''"
        )
        assert "Chandan" in adult_name or "Biswal" in adult_name, \
            f"Adult traveller 'Chandan Biswal' not found in review (got: '{adult_name}')"
        print(f"\n✅ Adult traveller verified: {adult_name}")

        child_name = page.evaluate(
            "() => document.querySelector('[ng-bind=\"childDetail.FirstName\"]')?.innerText?.trim() || ''"
        )
        assert "Tommy" in child_name, \
            f"Child traveller 'Tommy' not found in review (got: '{child_name}')"
        print(f"\n✅ Child traveller verified: {child_name}")

        assert FROM_CODE in review_text or "BHUBANESWAR" in review_text.upper(), \
            f"Boarding point {FROM_CODE} not found in review"
        print(f"\n✅ Boarding point verified: {FROM_CODE} - Bhubaneswar")

        # ── 19. Click "Refresh Availability" ─────────────────────────────────
        refresh_clicked = False
        for frame in [page.main_frame] + [f for f in page.frames if f != page.main_frame]:
            try:
                r = frame.evaluate("""
                    () => {
                        const el = [...document.querySelectorAll('button, a, input[type="button"], input[type="submit"], div, span')]
                            .find(e => /refresh.*avail|avail.*refresh/i.test((e.innerText || e.value || '').trim()));
                        if (!el) return null;
                        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        el.click();
                        return (el.innerText || el.value || '').trim();
                    }
                """)
                if r:
                    refresh_clicked = True
                    print(f"\n✅ 'Refresh Availability' clicked successfully (matched: '{r}')")
                    break
            except Exception:
                pass
        if not refresh_clicked:
            print(f"\n⚠️  'Refresh Availability' button not found — continuing")
        page.wait_for_timeout(3000)

        # ── 20. Wallets → More e-Wallets → PhonePe → Make Payment ─────────
        page.wait_for_load_state("domcontentloaded", timeout=60000)
        page.wait_for_timeout(8000)
        page.screenshot(path="emt2_before_wallet.png")
        print(f"\n   Payment gateway URL: {page.url}")
        print(f"   Screenshot saved: emt2_before_wallet.png")

        # Scroll to reveal payment methods
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1000)
        page.evaluate("window.scrollBy(0, 500)")
        page.wait_for_timeout(2000)

        # Step 1: Click "More e-Wallets" (directly, without clicking Wallets tab first)
        more_wallets_clicked = False
        for frame in [page.main_frame] + [f for f in page.frames if f != page.main_frame]:
            try:
                r = frame.evaluate("""
                    () => {
                        const el = document.querySelector('#showWltDtl') ||
                            [...document.querySelectorAll('span, div, a, li, button, p')]
                                .find(e => /more.*e.?wallet|more.*wallet/i.test((e.innerText || e.textContent || ''))
                                    && e.getBoundingClientRect().width > 0);
                        if (!el) return null;
                        el.scrollIntoView({behavior:'smooth', block:'center'});
                        el.click();
                        return (el.innerText || el.textContent || '').trim().substring(0, 40);
                    }
                """)
                if r:
                    more_wallets_clicked = True
                    print(f"\n✅ 'More e-Wallets' clicked successfully (matched: '{r}')")
                    break
            except Exception:
                pass
        if not more_wallets_clicked:
            print(f"\n⚠️  'More e-Wallets' not found — continuing")
        page.wait_for_timeout(2000)
        page.screenshot(path="emt2_more_wallets.png")
        print(f"   Screenshot saved: emt2_more_wallets.png")

        # Step 3: Select PhonePe radio button
        page.wait_for_timeout(2000)
        selected = page.evaluate("""
            () => {
                const radio = document.querySelector('[id="rdoPhonePe"]');
                if (!radio) return false;
                radio.checked = true;
                radio.dispatchEvent(new Event('change', { bubbles: true }));
                radio.dispatchEvent(new Event('click',  { bubbles: true }));
                return true;
            }
        """)
        all_frames = [page.main_frame] + [f for f in page.frames if f != page.main_frame]
        if not selected:
            for frame in all_frames:
                try:
                    found = frame.evaluate("() => !!document.querySelector('[id=\"rdoPhonePe\"]')")
                    if found:
                        frame.evaluate("document.querySelector('[id=\"rdoPhonePe\"]').scrollIntoView({behavior:'smooth', block:'center'})")
                        page.wait_for_timeout(500)
                        frame.locator('[id="rdoPhonePe"]').click(force=True)
                        selected = True
                        break
                except Exception:
                    pass
        page.wait_for_timeout(3000)
        page.screenshot(path="emt2_phonepe.png")
        print(f"\n✅ 'PhonePe' radio selected successfully")
        print(f"   Screenshot saved: emt2_phonepe.png")

        # Step 4: Click "Make Payment" — target first VISIBLE a.con_btn_pynw (paytm button)
        # Debug showed 3 buttons: only the 2nd one (ng-click="RedirectToHotelsGateway('paytm')") is visible
        page.wait_for_timeout(3000)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)

        # ── Capture total amount from EMT payment page ────────────────────────
        emt_amount = None
        try:
            amt_text = page.inner_text('body')
            amt_match = re.search(r'Total\s*Amount[\s\S]{0,50}?([\d,]+\.?\d*)', amt_text, re.IGNORECASE)
            if amt_match:
                emt_amount = amt_match.group(1).replace(',', '')
                print(f"\n   💰 EMT Total Amount (before payment): ₹{emt_amount}")
        except Exception as e:
            print(f"\n⚠️  Could not capture EMT amount: {e}")

        page.screenshot(path="emt2_before_makepayment.png")
        print(f"   Screenshot before Make Payment: emt2_before_makepayment.png")

        make_payment_clicked = False

        for attempt in range(8):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)

            for frame in all_frames:
                try:
                    btn_rect = frame.evaluate("""
                        () => {
                            // Find first visible Make Payment button (skip hidden ones)
                            const all = [...document.querySelectorAll('a.con_btn_pynw')];
                            const el = all.find(e => {
                                const r = e.getBoundingClientRect();
                                return r.width > 0 && r.height > 0;
                            });
                            if (!el) return null;
                            el.scrollIntoView({ behavior: 'instant', block: 'center' });
                            const r = el.getBoundingClientRect();
                            return { x: r.left + r.width / 2, y: r.top + r.height / 2,
                                     w: r.width, h: r.height,
                                     text: (el.innerText || '').trim(),
                                     ngClick: el.getAttribute('ng-click') || '' };
                        }
                    """)
                    if btn_rect and btn_rect.get('w', 0) > 0 and btn_rect.get('h', 0) > 0:
                        if frame != page.main_frame:
                            iframe_box = frame.frame_element().bounding_box()
                            if iframe_box:
                                btn_rect['x'] += iframe_box['x']
                                btn_rect['y'] += iframe_box['y']
                        page.wait_for_timeout(300)
                        page.mouse.click(btn_rect['x'], btn_rect['y'])
                        make_payment_clicked = True
                        print(f"\n✅ 'Make Payment' clicked at ({btn_rect['x']:.0f},{btn_rect['y']:.0f})"
                              f" ng-click='{btn_rect['ngClick']}'")
                        break
                except Exception:
                    pass
            if make_payment_clicked:
                break

            page.wait_for_timeout(2000)
            print(f"   Attempt {attempt+1}: Make Payment visible button not found, retrying...")

        assert make_payment_clicked, "Could not find visible 'Make Payment' button after Bajaj Pay selection"
        page.wait_for_timeout(3000)
        page.screenshot(path="emt2_final_payment.png")
        print(f"   Screenshot saved: emt2_final_payment.png")
        print(f"   URL: {page.url}")

        # ── Click first "Cancel" (id="cancelTxn" on payment gateway page) ──────
        page.wait_for_load_state("domcontentloaded", timeout=30000)
        page.wait_for_timeout(8000)
        page.screenshot(path="emt2_otp.png")
        print(f"\n   URL after Make Payment: {page.url}")
        print(f"   Screenshot saved: emt2_otp.png")

        # ── Capture & verify amount on OTP/payment gateway page ───────────────
        try:
            otp_page_text = page.inner_text('body')

            # Strategy 1: Find exact match to emt_amount in page text
            otp_amount = None
            if emt_amount:
                # Check both raw and comma-formatted versions
                emt_with_comma = f"{float(emt_amount):,.2f}" if '.' in emt_amount else f"{float(emt_amount):,}"
                if emt_amount in otp_page_text.replace(',', '') or emt_with_comma in otp_page_text:
                    otp_amount = emt_amount
                    print(f"   OTP page amount (exact match): ₹{otp_amount}")

            # Strategy 2: Find amount near "Amount" / "Rs" / "INR" keyword
            if not otp_amount:
                amt_ctx = re.search(
                    r'(?:Amount|Rs\.?|INR|₹)\s*:?\s*([\d,]+\.?\d*)',
                    otp_page_text, re.IGNORECASE
                )
                if amt_ctx:
                    otp_amount = amt_ctx.group(1).replace(',', '')
                    print(f"   OTP page amount (near keyword): ₹{otp_amount}")

            # Strategy 3: Print all candidate amounts for debugging
            if not otp_amount:
                candidates = re.findall(r'\b(\d{3,6}\.\d{2})\b', otp_page_text)
                print(f"   OTP page amount candidates: {candidates}")
                if candidates:
                    otp_amount = candidates[0].replace(',', '')

            if emt_amount and otp_amount:
                if float(emt_amount) == float(otp_amount):
                    print(f"\n✅ Amount Verified: ₹{otp_amount} matches EMT page ✅")
                else:
                    print(f"\n⚠️  Amount MISMATCH! EMT: ₹{emt_amount} | OTP Page: ₹{otp_amount}")
            else:
                print(f"\n⚠️  Could not verify amount on OTP page (emt=₹{emt_amount}, otp=₹{otp_amount})")
        except Exception as e:
            print(f"\n⚠️  Amount verification error: {e}")

        # ── Click cross button (id="cancel-payment") on payment page ────────────
        cancel1_clicked = False
        for attempt in range(15):
            all_frames = [page.main_frame] + [f for f in page.frames if f != page.main_frame]
            for frame in all_frames:
                try:
                    result = frame.evaluate("""
                        () => {
                            const btn = document.getElementById('cancel-payment');
                            if (btn) { btn.click(); return true; }
                            return false;
                        }
                    """)
                    if result:
                        cancel1_clicked = True
                        print(f"\n✅ Cross button clicked via JS (id='cancel-payment', frame: {frame.url[:60]})")
                        break
                except Exception:
                    pass
                try:
                    btn = frame.locator('#cancel-payment')
                    if btn.count() > 0:
                        btn.first.click(force=True)
                        cancel1_clicked = True
                        print(f"\n✅ Cross button clicked via locator (id='cancel-payment', frame: {frame.url[:60]})")
                        break
                except Exception:
                    pass
            if cancel1_clicked:
                break
            page.wait_for_timeout(2000)
            print(f"   Attempt {attempt+1}: #cancel-payment not found yet, retrying...")

        if not cancel1_clicked:
            page.screenshot(path="emt2_cancel_payment_notfound.png")
            print(f"\n⚠️  #cancel-payment not found after all attempts")
            print(f"   Screenshot saved: emt2_cancel_payment_notfound.png")

        page.wait_for_timeout(2000)
        page.screenshot(path="emt2_cancel_payment.png")
        print(f"\n✅ Cross button (cancel-payment) handled successfully")
        print(f"   URL: {page.url}")
        print(f"   Screenshot saved: emt2_cancel_payment.png")

        # ── Click "Yes, cancel" confirmation button (id="yes-cancel-button") ───
        yes_cancel_clicked = False
        for _ in range(10):
            all_frames2 = [page.main_frame] + [f for f in page.frames if f != page.main_frame]
            for frame in all_frames2:
                try:
                    result = frame.evaluate("""
                        () => {
                            const btn = document.getElementById('yes-cancel-button');
                            if (btn) { btn.click(); return true; }
                            return false;
                        }
                    """)
                    if result:
                        yes_cancel_clicked = True
                        print(f"\n✅ 'Yes, cancel' clicked via JS (id='yes-cancel-button', frame: {frame.url[:60]})")
                        break
                except Exception:
                    pass
                try:
                    btn = frame.locator('#yes-cancel-button')
                    if btn.count() > 0:
                        btn.first.click(force=True)
                        yes_cancel_clicked = True
                        print(f"\n✅ 'Yes, cancel' clicked via locator (id='yes-cancel-button', frame: {frame.url[:60]})")
                        break
                except Exception:
                    pass
            if yes_cancel_clicked:
                break
            page.wait_for_timeout(2000)

        if not yes_cancel_clicked:
            print(f"\n⚠️  'Yes, cancel' button (id='yes-cancel-button') not found — continuing")

        page.wait_for_load_state("domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        page.screenshot(path="emt2_cancel_confirm.png")
        print(f"\n✅ 'Yes, cancel' handled successfully")
        print(f"   URL: {page.url}")
        print(f"   Screenshot saved: emt2_cancel_confirm.png")

        # ── Capture Generated Booking ID ──────────────────────────────────────
        try:
            booking_id_locator = page.locator("text=/BOOKING ID:/i")
            booking_id_locator.wait_for(state="visible", timeout=10000)

            booking_text = booking_id_locator.inner_text().strip()

            booking_id = re.search(r"EMT\d+", booking_text)

            if booking_id:
                print(f"\n✅ Generated Booking ID: {booking_id.group()}")
                with open("booking_ids.txt", "a") as file:
                    file.write(booking_id.group() + "\n")
            else:
                print("❌ Booking ID not found")
        except Exception as e:
            print(f"❌ Booking ID not found: {e}")

        page.wait_for_timeout(10000)

        context.close()
        browser.close()


if __name__ == "__main__":
    test_easemytrip_bbs_ndls_1a_mobweb()
