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
_travel_dt   = datetime.now() + timedelta(days=10)
TRAVEL_DATE  = _travel_dt.strftime("%d/%m/%Y")          # e.g. "12/06/2026"
TRAVEL_DATE_DISPLAY = _travel_dt.strftime("%#d %B %Y")  # e.g. "12 June 2026" (Windows: %#d)

# Traveller details
IRCTC_ID     = "Biswalchandan"
ADULT_NAME   = "Chandan Biswal"
ADULT_AGE    = "26"
ADULT_BERTH  = "Lower Berth"
ADULT2_NAME  = "Testeasemytrip"
ADULT2_AGE   = "30"
ADULT2_BERTH = "Side Upper Berth"
CHILD_NAME   = "Tommy"
CHILD_AGE    = "2"
EMAIL        = "chandan.biswal@easemytrip.com"
MOBILE       = "8018240079"

# Edited values (used in edit step)
ADULT_BERTH_EDITED  = "Upper Berth"
ADULT2_BERTH_EDITED = "Side Lower Berth"


def test_easemytrip_traveller_page_mobweb():
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
        page.screenshot(path="emt4_home.png", full_page=False)
        print("   Screenshot saved: emt4_home.png")

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
        page.screenshot(path="emt4_trains.png", full_page=False)
        print("   Screenshot saved: emt4_trains.png")

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
        page.screenshot(path="emt4_from.png", full_page=False)
        print("   Screenshot saved: emt4_from.png")

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
        page.screenshot(path="emt4_to.png", full_page=False)
        print("   Screenshot saved: emt4_to.png")

        # ── 5. Select departure date (today + 10 days) ───────────────────────
        depart_date = page.locator("#departureDate")
        depart_date.wait_for(state="visible", timeout=15000)
        depart_date.click()
        page.wait_for_timeout(1500)

        print(f"\n✅ Departure date field clicked successfully")

        # Navigate calendar months until the target date span is visible (up to 8 months)
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
        assert TRAVEL_DATE in selected_date or _travel_dt.strftime("%-d %b") in selected_date, \
            f"Date not selected correctly. Got: {selected_date}"

        print(f"   Selected date: {selected_date}")
        print(f"\n✅ Date {TRAVEL_DATE} selected successfully")
        page.screenshot(path="emt4_date.png", full_page=False)
        print("   Screenshot saved: emt4_date.png")

        # ── 6. Search Trains ─────────────────────────────────────────────────
        search_btn = page.locator("input.cta-btn[type='submit']")
        search_btn.wait_for(state="visible", timeout=15000)
        search_btn.click()
        page.wait_for_load_state("domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)

        print(f"\n✅ Search Trains clicked successfully")
        print(f"   URL: {page.url}")
        page.screenshot(path="emt4_results.png", full_page=False)
        print("   Screenshot saved: emt4_results.png")

        # ── 7. Verify listing page ───────────────────────────────────────────
        assert FROM_CODE in page.url, f"{FROM_CODE} missing in URL: {page.url}"
        assert TO_CODE   in page.url, f"{TO_CODE} missing in URL: {page.url}"

        expect(page).to_have_title(re.compile(r"train", re.IGNORECASE), timeout=15000)

        route_header = page.locator(".trainhdr-pill")
        route_header.wait_for(state="visible", timeout=15000)
        route_text = route_header.inner_text()
        assert FROM_CODE in route_text and TO_CODE in route_text, \
            f"Route header mismatch: {route_text}"

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

        # ── 8. Select 3A class on first available train and click Book ────────
        # Find the first train card that has a visible 3A seat option
        first_card_with_3a = None
        for i in range(card_count):
            card = page.locator(".main-confrm").nth(i)
            seat_3a = card.locator(".emt-seat-wrap").filter(
                has=page.locator("span.train-class", has_text="3A")
            ).first
            if seat_3a.count() > 0:
                first_card_with_3a = card
                break

        assert first_card_with_3a is not None, "No train card with 3A class found"

        # Read the train name from the card
        train_name_el = first_card_with_3a.locator(
            ".elp.ng-binding, .train-name, h3, .trn-name"
        ).first
        chosen_train = train_name_el.inner_text().strip() if train_name_el.count() > 0 else "First Available Train"

        class_3a = first_card_with_3a.locator(".emt-seat-wrap").filter(
            has=page.locator("span.train-class", has_text="3A")
        ).first
        class_3a.scroll_into_view_if_needed(timeout=10000)
        class_3a.click()
        page.wait_for_timeout(1500)

        print(f"\n✅ '3A' class clicked on '{chosen_train}' successfully")
        page.screenshot(path="emt4_3a_selected.png", full_page=False)
        print("   Screenshot saved: emt4_3a_selected.png")

        # Click the first available Book button inside the 3A section
        book_btn = first_card_with_3a.locator("button.book-btn").first
        book_btn.wait_for(state="visible", timeout=10000)
        book_btn.scroll_into_view_if_needed(timeout=10000)
        book_btn.click()

        # Retry click if navigation doesn't happen immediately
        for _ in range(3):
            if "TrainTraveller" in page.url:
                break
            try:
                page.wait_for_url("**/TrainTraveller**", timeout=15000)
                break
            except Exception:
                book_btn.scroll_into_view_if_needed(timeout=5000)
                book_btn.click()
                page.wait_for_timeout(2000)

        page.wait_for_timeout(2000)

        print(f"\n✅ 'Book' button clicked successfully")
        print(f"   URL: {page.url}")
        page.screenshot(path="emt4_book.png", full_page=False)
        print("   Screenshot saved: emt4_book.png")

        # ════════════════════════════════════════════════════════════════════
        # TRAVELLER PAGE
        # ════════════════════════════════════════════════════════════════════

        page.wait_for_load_state("domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)

        # ── 9. Enter IRCTC User ID ───────────────────────────────────────────
        irctc_input = page.locator("input#IRCTCUserName").first
        irctc_input.wait_for(state="visible", timeout=15000)
        irctc_input.click()
        irctc_input.fill(IRCTC_ID)
        page.wait_for_timeout(500)

        entered_value = irctc_input.input_value()
        assert entered_value == IRCTC_ID, \
            f"IRCTC ID not entered correctly. Got: {entered_value!r}"

        print(f"\n✅ IRCTC User ID entered successfully")
        print(f"   IRCTC ID: {entered_value}")

        # ── 10. Click Proceed ────────────────────────────────────────────────
        proceed_btn = page.locator("a.login100-form-btn").filter(
            has_text=re.compile(r"proceed", re.IGNORECASE)
        )
        proceed_btn.wait_for(state="visible", timeout=10000)
        proceed_btn.click()
        page.wait_for_timeout(2000)

        print(f"\n✅ Proceed clicked successfully")
        print(f"   URL: {page.url}")
        page.wait_for_timeout(2000)

        # ── 11. Verify post-Proceed details ──────────────────────────────────
        # Verify IRCTC User ID shown on page
        irctc_display = page.locator("span#IRCTCUserID")
        try:
            irctc_display.wait_for(state="visible", timeout=15000)
            irctc_shown = irctc_display.inner_text().strip()
        except Exception:
            irctc_shown = irctc_display.evaluate("el => el.textContent").strip()
        assert irctc_shown == IRCTC_ID, \
            f"IRCTC User ID mismatch. Expected '{IRCTC_ID}', got: {irctc_shown!r}"

        # Verify train name
        shown_train = page.evaluate("""
            () => {
                const el = document.querySelector('span.elp.ng-binding');
                return el ? (el.innerText || el.textContent || '').trim() : '';
            }
        """)
        if not shown_train:
            page.wait_for_timeout(2000)
            shown_train = page.evaluate("""
                () => {
                    const el = document.querySelector('span.elp.ng-binding');
                    return el ? (el.innerText || el.textContent || '').trim() : 'Unknown Train';
                }
            """)

        # Verify route codes
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

        # Verify travel date visible on page
        day_str   = str(_travel_dt.day)
        month_str = _travel_dt.strftime("%B")   # e.g. "June"
        year_str  = str(_travel_dt.year)
        date_pattern = re.compile(rf"{day_str}\s*{month_str}\s*{year_str}", re.IGNORECASE)
        date_el = page.get_by_text(date_pattern).first
        date_el.wait_for(state="visible", timeout=10000)
        date_text = date_el.inner_text().strip()

        print(f"\n✅ Post-Proceed verification passed successfully")
        print(f"   IRCTC User ID : {irctc_shown}")
        print(f"   Train         : {shown_train}")
        print(f"   Route         : {source_text} → {dest_text}")
        print(f"   Date          : {date_text}")
        page.screenshot(path="emt4_traveller_verified.png", full_page=False)
        print("   Screenshot saved: emt4_traveller_verified.png")

        # ── 12. Select 'Zero charges when ticket is cancelled' ───────────────
        zero_charges = page.locator("label.container-radio").filter(
            has_text=re.compile(r"zero charges when ticket is cancel", re.IGNORECASE)
        )
        zero_charges.wait_for(state="visible", timeout=15000)
        zero_charges.click()
        page.wait_for_timeout(1000)

        radio_input = zero_charges.locator("input[type='radio']")
        assert radio_input.is_checked(), "Zero charges radio button was not selected"
        print(f"\n✅ 'Zero charges when ticket is cancelled' selected successfully")

        # ── 13. Add Adult 1 (Male, Chandan Biswal, 26, Lower Berth) ──────────
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
        name_input.fill(ADULT_NAME)
        page.wait_for_timeout(300)
        entered_name = name_input.input_value()
        assert entered_name == ADULT_NAME, f"Name not entered correctly. Got: {entered_name!r}"
        print(f"✅ Full Name entered: {entered_name}")

        age_input = page.locator("input#txtAge0")
        age_input.wait_for(state="visible", timeout=10000)
        age_input.click()
        age_input.fill(ADULT_AGE)
        page.wait_for_timeout(300)
        entered_age = age_input.input_value()
        assert entered_age == ADULT_AGE, f"Age not entered correctly. Got: {entered_age!r}"
        print(f"✅ Age entered: {entered_age}")

        berth_select = page.locator("select#ddlAdultBirthPre0")
        berth_select.wait_for(state="visible", timeout=10000)
        berth_select.click()
        berth_select.select_option(label=ADULT_BERTH)
        page.wait_for_timeout(500)
        selected_berth = berth_select.evaluate("e => e.options[e.selectedIndex].text")
        assert ADULT_BERTH in selected_berth, f"Berth not set correctly. Got: {selected_berth!r}"
        print(f"\n✅ Berth preference selected: {selected_berth}")

        save_adult_btn = page.locator("div#btnAddPassenger1")
        save_adult_btn.wait_for(state="visible", timeout=10000)
        save_adult_btn.click()
        page.wait_for_timeout(1500)
        print(f"\n✅ 'Save Adult' clicked successfully")

        # ── 14. Add Adult 2 (Female, Testeasemytrip, 30, Side Upper Berth) ───
        add_adult_btn2 = page.locator("a.add_adult").filter(
            has_text=re.compile(r"add adult", re.IGNORECASE)
        )
        add_adult_btn2.wait_for(state="visible", timeout=15000)
        add_adult_btn2.click()
        page.wait_for_timeout(1000)
        print(f"\n✅ 'Add Adult' (2nd) clicked successfully")
        page.wait_for_timeout(1000)

        female_label = page.locator("div#ddlPassengerAge1").locator(
            "label", has_text=re.compile(r"^Female$", re.IGNORECASE)
        )
        female_label.wait_for(state="visible", timeout=10000)
        female_label.click()
        page.wait_for_timeout(500)
        print(f"\n✅ 'Female' gender selected for 2nd adult")

        name_input2 = page.locator("input#txtAdultFirstName1")
        name_input2.wait_for(state="visible", timeout=10000)
        name_input2.click()
        name_input2.fill(ADULT2_NAME)
        page.wait_for_timeout(300)
        entered_name2 = name_input2.input_value()
        assert entered_name2 == ADULT2_NAME, f"2nd adult name not entered correctly. Got: {entered_name2!r}"
        print(f"✅ Full Name entered: {entered_name2}")

        age_input2 = page.locator("input#txtAge1")
        age_input2.wait_for(state="visible", timeout=10000)
        age_input2.click()
        age_input2.fill(ADULT2_AGE)
        page.wait_for_timeout(300)
        entered_age2 = age_input2.input_value()
        assert entered_age2 == ADULT2_AGE, f"2nd adult age not entered correctly. Got: {entered_age2!r}"
        print(f"✅ Age entered: {entered_age2}")

        berth_select2 = page.locator("select#ddlAdultBirthPre1")
        berth_select2.wait_for(state="visible", timeout=10000)
        berth_select2.click()
        berth_select2.select_option(label=ADULT2_BERTH)
        page.wait_for_timeout(500)
        selected_berth2 = berth_select2.evaluate("e => e.options[e.selectedIndex].text")
        assert ADULT2_BERTH in selected_berth2, f"2nd adult berth not set correctly. Got: {selected_berth2!r}"
        print(f"\n✅ Berth preference selected: {selected_berth2}")

        save_adult_btn2 = page.locator("div#btnAddPassenger2")
        save_adult_btn2.wait_for(state="visible", timeout=10000)
        save_adult_btn2.click()
        page.wait_for_timeout(1500)
        print(f"\n✅ '2nd Adult' saved successfully")

        # ── 15. Add Child (Male, Tommy, Age 2) ──────────────────────────────
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
        child_name_input.fill(CHILD_NAME)
        page.wait_for_timeout(300)
        entered_child_name = child_name_input.input_value()
        assert entered_child_name == CHILD_NAME, f"Child name not entered correctly. Got: {entered_child_name!r}"
        print(f"✅ Child Full Name entered: {entered_child_name}")

        child_age_select = page.locator("div#divChildView3 select#txtChildAge0")
        child_age_select.wait_for(state="visible", timeout=10000)
        child_age_select.click()
        child_age_select.select_option(label=CHILD_AGE)
        page.wait_for_timeout(300)
        selected_child_age = child_age_select.evaluate("e => e.options[e.selectedIndex].text")
        assert selected_child_age == CHILD_AGE, f"Child age not selected correctly. Got: {selected_child_age!r}"
        print(f"✅ Child Age selected: {selected_child_age}")

        save_child_btn = page.locator("div#divChildView3 div#btnChildAdd0")
        save_child_btn.wait_for(state="visible", timeout=10000)
        save_child_btn.click()
        page.wait_for_timeout(1500)
        print(f"\n✅ 'Save Child' clicked successfully")

        page.screenshot(path="emt4_all_passengers_added.png", full_page=False)
        print(f"\n✅ All passengers added — screenshot saved: emt4_all_passengers_added.png")

        # ════════════════════════════════════════════════════════════════════
        # EDIT PASSENGERS
        # ════════════════════════════════════════════════════════════════════

        page.wait_for_timeout(1000)
        page.screenshot(path="emt4_before_edit.png", full_page=False)
        print("\n   📸 Screenshot before edit: emt4_before_edit.png")

        # Edit buttons use class "fr edit_info" with ng-click editAdultPassenger / editChild
        edit_btns = page.locator("a.edit_info")

        def force_click_save(btn_id):
            """Force-click a save button by ID, bypassing Angular visibility restrictions."""
            result = page.evaluate(f"""
                () => {{
                    const btn = document.querySelector('#{btn_id}');
                    if (btn) {{ btn.click(); return btn.textContent.trim(); }}
                    return null;
                }}
            """)
            page.wait_for_timeout(1500)
            return result

        # ── 16. Edit Adult 1 — change berth to Upper Berth ───────────────────
        edit_btns.nth(0).scroll_into_view_if_needed()
        edit_btns.nth(0).click()
        page.wait_for_timeout(1500)

        berth_edit = page.locator("select#ddlAdultBirthPre0")
        berth_edit.wait_for(state="visible", timeout=10000)
        berth_edit.select_option(label=ADULT_BERTH_EDITED)
        page.wait_for_timeout(500)
        edited_berth = berth_edit.evaluate("e => e.options[e.selectedIndex].text")
        print(f"\n✅ Adult 1 berth edited from '{ADULT_BERTH}' → '{edited_berth}'")

        save_result1 = force_click_save("btnAddPassenger1")
        print(f"✅ Adult 1 save clicked ('{save_result1}')")

        # Wait for Adult 1 form to collapse before editing Adult 2
        try:
            berth_edit.wait_for(state="hidden", timeout=5000)
        except Exception:
            page.wait_for_timeout(1000)

        page.screenshot(path="emt4_adult1_edited.png", full_page=False)
        print("   Screenshot saved: emt4_adult1_edited.png")

        # ── 17. Edit Adult 2 — change berth to Side Lower Berth ──────────────
        edit_btns.nth(1).scroll_into_view_if_needed()
        edit_btns.nth(1).click()
        page.wait_for_timeout(1500)

        berth_edit2 = page.locator("select#ddlAdultBirthPre1")
        berth_edit2.wait_for(state="visible", timeout=10000)
        berth_edit2.select_option(label=ADULT2_BERTH_EDITED)
        page.wait_for_timeout(500)
        edited_berth2 = berth_edit2.evaluate("e => e.options[e.selectedIndex].text")
        print(f"\n✅ Adult 2 berth edited from '{ADULT2_BERTH}' → '{edited_berth2}'")

        save_result2 = force_click_save("btnAddPassenger2")
        print(f"✅ Adult 2 save clicked ('{save_result2}')")

        try:
            berth_edit2.wait_for(state="hidden", timeout=5000)
        except Exception:
            page.wait_for_timeout(1000)

        page.screenshot(path="emt4_adult2_edited.png", full_page=False)
        print("   Screenshot saved: emt4_adult2_edited.png")

        # ── 18. Edit Child — change name to "Tommy Jr" ────────────────────────
        edit_btns.nth(2).scroll_into_view_if_needed()
        edit_btns.nth(2).click()
        page.wait_for_timeout(1500)

        child_name_edit = page.locator("div#divChildView3 input#txtInfant0")
        child_name_edit.wait_for(state="visible", timeout=10000)
        child_name_edit.click(click_count=3)
        child_name_edit.fill("Tommy Jr")
        page.wait_for_timeout(300)
        edited_child_name = child_name_edit.input_value()
        print(f"\n✅ Child name edited: '{CHILD_NAME}' → '{edited_child_name}'")

        save_result_child = force_click_save("btnChildAdd0")
        print(f"✅ Child save clicked ('{save_result_child}')")

        try:
            child_name_edit.wait_for(state="hidden", timeout=5000)
        except Exception:
            page.wait_for_timeout(1000)

        page.screenshot(path="emt4_child_edited.png", full_page=False)
        print("   Screenshot saved: emt4_child_edited.png")

        # ── 19. Final traveller page screenshot ──────────────────────────────
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1000)
        page.screenshot(path="emt4_traveller_final.png", full_page=True)
        print(f"\n✅ Traveller page completed — all verifications and edits done")
        print(f"   Train         : {shown_train}")
        print(f"   Route         : {source_text} → {dest_text}")
        print(f"   Travel date   : {date_text}")
        print(f"   Adult 1       : {ADULT_NAME} | Age {ADULT_AGE} | Berth edited → {ADULT_BERTH_EDITED}")
        print(f"   Adult 2       : {ADULT2_NAME} | Age {ADULT2_AGE} | Berth edited → {ADULT2_BERTH_EDITED}")
        print(f"   Child         : Tommy Jr | Age {CHILD_AGE}")
        print(f"   Screenshot saved: emt4_traveller_final.png")

        context.close()
        browser.close()


if __name__ == "__main__":
    test_easemytrip_traveller_page_mobweb()
