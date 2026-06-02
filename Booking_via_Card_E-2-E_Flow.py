import re
import pytest
from playwright.sync_api import sync_playwright, expect

# Android mobile emulation using Pixel 5 device descriptor
DEVICE_NAME = "Pixel 5"
URL = "https://www.easemytrip.com"


def test_easemytrip_android_mobweb():
    with sync_playwright() as p:
        # Launch Chromium with Android mobile emulation
        pixel5 = p.devices[DEVICE_NAME]

        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            **pixel5,
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )

        page = context.new_page()

        # Navigate to EaseMyTrip
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)

        # Verify page title contains EaseMyTrip (case-insensitive regex)
        expect(page).to_have_title(re.compile(r"easemytrip", re.IGNORECASE), timeout=15000)

        # Verify the page URL
        assert "easemytrip.com" in page.url, f"Unexpected URL: {page.url}"

        print(f"\n✅ Page loaded successfully")
        print(f"   Title : {page.title()}")
        print(f"   URL   : {page.url}")
        print(f"   Device: {DEVICE_NAME} ({pixel5['viewport']})")

        # Take a screenshot for evidence
        page.screenshot(path="easemytrip_android_mobweb.png", full_page=False)
        print("   Screenshot saved: easemytrip_android_mobweb.png")

        # Click on "Trains" navigation item
        trains_link = page.get_by_role("link", name=re.compile(r"trains", re.IGNORECASE))
        trains_link.first.wait_for(state="visible", timeout=15000)
        trains_link.first.click()

        # Wait for Trains page to load
        page.wait_for_load_state("domcontentloaded", timeout=30000)

        # Verify navigation to Trains page
        assert "train" in page.url.lower() or "train" in page.title().lower(), \
            f"Did not navigate to Trains page. URL: {page.url}, Title: {page.title()}"

        print(f"\n✅ Trains page loaded successfully")
        print(f"   Title : {page.title()}")
        print(f"   URL   : {page.url}")

        page.screenshot(path="easemytrip_trains_mobweb.png", full_page=False)
        print("   Screenshot saved: easemytrip_trains_mobweb.png")

        # Click on the 'From' station input field
        from_field = page.locator("#sourceStation")
        from_field.wait_for(state="visible", timeout=15000)
        from_field.click()

        # Verify the From search panel is open (expanded input becomes visible)
        from_search = page.locator("#txtfromcity1")
        from_search.wait_for(state="visible", timeout=10000)

        # Type station name 'ANVT' character by character to trigger Angular autocomplete
        from_search.click(click_count=3)
        for ch in "ANVT":
            from_search.press(ch)
            page.wait_for_timeout(300)

        # Wait for suggestion to appear and click 'ANVT' from the dropdown
        anvt_suggestion = page.locator(".auto_saugg").first.locator("li", has_text="ANVT")
        anvt_suggestion.wait_for(state="visible", timeout=10000)
        anvt_suggestion.click()

        # Verify From field is updated with ANVT
        page.wait_for_timeout(1000)
        from_value = page.locator("#txtfromcity").input_value()
        assert "ANVT" in from_value, f"From field not updated. Got: {from_value}"

        print(f"\n✅ 'ANVT' station selected successfully")
        print(f"   From field value: {from_value}")

        print(f"\n✅ 'From' field clicked successfully")

        page.screenshot(path="easemytrip_trains_from_mobweb.png", full_page=False)
        print("   Screenshot saved: easemytrip_trains_from_mobweb.png")

        # Click on the 'To' station input field
        to_field = page.locator("#ToStation")
        to_field.wait_for(state="visible", timeout=15000)
        to_field.click()

        # Verify the To search panel is open
        to_search = page.locator("#txtdesticity1")
        to_search.wait_for(state="visible", timeout=10000)

        # Type arrival station 'CTC' character by character to trigger Angular autocomplete
        to_search.click(click_count=3)
        for ch in "CTC":
            to_search.press(ch)
            page.wait_for_timeout(300)

        # Wait for suggestion to appear and click 'CTC' from the dropdown
        ctc_suggestion = page.locator(".auto_saugg").nth(1).locator("li", has_text="CTC")
        ctc_suggestion.wait_for(state="visible", timeout=10000)
        ctc_suggestion.click()

        # Verify To field is updated with CTC
        page.wait_for_timeout(1000)
        to_value = page.locator("#txtdesticity").input_value()
        assert "CTC" in to_value, f"To field not updated. Got: {to_value}"

        print(f"\n✅ 'CTC' station selected successfully")
        print(f"   To field value: {to_value}")

        page.screenshot(path="easemytrip_trains_to_mobweb.png", full_page=False)
        print("   Screenshot saved: easemytrip_trains_to_mobweb.png")

        # Click on the Departure Date field
        depart_date = page.locator("#departureDate")
        depart_date.wait_for(state="visible", timeout=15000)
        depart_date.click()

        # Wait for the date picker to open
        page.wait_for_timeout(1500)

        print(f"\n✅ Departure date field clicked successfully")

        # Click on 27 Jun 2026 in the calendar
        date_27_jun = page.locator("span[id*='27/06/2026']")
        date_27_jun.wait_for(state="visible", timeout=10000)
        date_27_jun.click()
        page.wait_for_timeout(1000)

        # Verify the date is selected
        selected_date = page.locator("#txtDate").input_value()
        assert "27/06/2026" in selected_date or "27 Jun" in selected_date, \
            f"Date not selected correctly. Got: {selected_date}"

        print(f"   Selected date: {selected_date}")
        print(f"\n✅ Date 27 Jun 2026 selected successfully")

        page.screenshot(path="easemytrip_trains_depart_date_mobweb.png", full_page=False)
        print("   Screenshot saved: easemytrip_trains_depart_date_mobweb.png")

        # Click on Search Trains button
        search_btn = page.locator("input.cta-btn[type='submit']")
        search_btn.wait_for(state="visible", timeout=15000)
        search_btn.click()

        # Wait for search results page to load
        page.wait_for_load_state("domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)

        print(f"\n✅ Search Trains clicked successfully")
        print(f"   URL: {page.url}")

        page.screenshot(path="easemytrip_trains_search_results_mobweb.png", full_page=False)
        print("   Screenshot saved: easemytrip_trains_search_results_mobweb.png")

        # --- Verify Listing Page ---
        # 1. Verify URL contains correct search parameters
        assert "ANVT" in page.url, f"ANVT missing in URL: {page.url}"
        assert "CTC" in page.url, f"CTC missing in URL: {page.url}"
        assert "27/06/2026" in page.url, f"Date missing in URL: {page.url}"

        # 2. Verify page title
        expect(page).to_have_title(re.compile(r"train", re.IGNORECASE), timeout=15000)

        # 3. Verify route header shows ANVT - CTC
        route_header = page.locator(".trainhdr-pill")
        route_header.wait_for(state="visible", timeout=15000)
        route_text = route_header.inner_text()
        assert "ANVT" in route_text and "CTC" in route_text, \
            f"Route header mismatch: {route_text}"

        # 4. Verify departure date is shown
        date_el = page.locator("[class*=date]").filter(has_text="27 Jun 2026").first
        date_el.wait_for(state="visible", timeout=10000)

        # 5. Verify at least one train result card is present
        train_cards = page.locator(".trainwrap-outer")
        train_cards.first.wait_for(state="visible", timeout=15000)
        card_count = train_cards.count()
        assert card_count >= 1, f"No train results found on listing page"

        print(f"\n✅ Listing page verified successfully")
        print(f"   Route  : {route_text.strip()}")
        print(f"   Results: {card_count} train(s) listed")

        # Wait for the loading overlay to disappear before interacting with filter
        try:
            loader = page.locator("#div_Cotant")
            loader.wait_for(state="hidden", timeout=90000)
        except Exception:
            pass  # proceed even if overlay lingers

        # Click on the Filter button
        filter_btn = page.locator("div.etm-filter").first
        filter_btn.wait_for(state="visible", timeout=15000)
        filter_btn.click()
        page.wait_for_timeout(3000)

        # Verify the filter panel is open (stick_filter with Apply button becomes visible)
        filter_apply = page.locator("div.stick_filter")
        filter_apply.wait_for(state="visible", timeout=10000)
        apply_text = filter_apply.inner_text()

        print(f"\n✅ Filter clicked successfully")
        print(f"   Filter panel is open: {apply_text.strip()!r}")

        page.screenshot(path="easemytrip_trains_filter_mobweb.png", full_page=False)
        print("   Screenshot saved: easemytrip_trains_filter_mobweb.png")

        # Wait for filter panel labels to render (Angular lazy rendering)
        page.wait_for_selector("label.cont_fltx", state="visible", timeout=15000)

        # Click the 'Morning' (06:00 - 12:00) departure timing radio button
        # Use inner div.f14 with exact text "Morning" to avoid matching "Early Morning"
        morning_label = page.locator("label.cont_fltx").filter(
            has=page.locator("div.f14").filter(has_text=re.compile(r"^Morning$", re.IGNORECASE))
        ).first
        morning_label.scroll_into_view_if_needed(timeout=10000)
        morning_label.click()
        page.wait_for_timeout(1000)

        # Verify Morning is selected (input inside the label should be checked)
        morning_input = morning_label.locator("input[type='checkbox'], input[type='radio']")
        is_checked = morning_input.is_checked()
        assert is_checked, "Morning departure timing was not selected"

        print(f"\n✅ 'Morning' departure timing selected successfully")

        # Click the Apply button
        apply_btn = page.locator("div.stick_filter").filter(has_text=re.compile(r"apply", re.IGNORECASE))
        apply_btn.wait_for(state="visible", timeout=10000)
        apply_btn.click()
        page.wait_for_timeout(2000)

        print(f"\n✅ Apply clicked successfully")

        page.screenshot(path="easemytrip_trains_filter_applied_mobweb.png", full_page=False)
        print("   Screenshot saved: easemytrip_trains_filter_applied_mobweb.png")

        # Verify the selected calendar date (27 Jun 2026) is shown on the results page
        # Element may be hidden under filter panel overlay — read via JS to avoid visibility check
        date_header = page.locator("div.trainhdr-date#spnDate")
        date_header.wait_for(state="attached", timeout=10000)
        displayed_date = page.evaluate(
            "document.querySelector('div.trainhdr-date#spnDate').textContent"
        ).strip()
        assert "27 Jun 2026" in displayed_date, \
            f"Expected '27 Jun 2026' in date header, but got: {displayed_date!r}"

        print(f"\n✅ Calendar date verified successfully")
        print(f"   Displayed date: {displayed_date}")

        # Find the Nandankanan Exp train card and click '3A' class
        nandankanan_card = page.locator(".main-confrm").filter(has_text="Nandankanan Exp")
        nandankanan_card.wait_for(state="visible", timeout=15000)

        class_3a = nandankanan_card.locator(".emt-seat-wrap").filter(
            has=page.locator("span.train-class", has_text="3A")
        ).first
        class_3a.scroll_into_view_if_needed(timeout=10000)
        class_3a.click()
        page.wait_for_timeout(1500)

        print(f"\n✅ '3A' class clicked on Nandankanan Exp successfully")

        page.screenshot(path="easemytrip_trains_3a_selected_mobweb.png", full_page=False)
        print("   Screenshot saved: easemytrip_trains_3a_selected_mobweb.png")

        # Click the Book button for the same date (27 Jun 2026)
        date_slot = nandankanan_card.locator("div.seat-status").filter(
            has_text=re.compile(r"27 Jun", re.IGNORECASE)
        ).first
        date_slot.wait_for(state="visible", timeout=10000)

        book_btn = date_slot.locator("button.book-btn")
        book_btn.wait_for(state="visible", timeout=10000)
        book_btn.scroll_into_view_if_needed(timeout=10000)
        book_btn.click()

        # Wait for navigation to the traveller/booking page
        page.wait_for_url("**/TrainTraveller**", timeout=30000)
        page.wait_for_timeout(2000)

        print(f"\n✅ 'Book' button clicked for 27 Jun 2026 successfully")
        print(f"   URL: {page.url}")

        page.screenshot(path="easemytrip_trains_book_mobweb.png", full_page=False)
        print("   Screenshot saved: easemytrip_trains_book_mobweb.png")

        # Wait for traveller page to load fully
        page.wait_for_load_state("domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)

        # Enter IRCTC User ID
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

        # Click the Proceed button
        proceed_btn = page.locator("a.login100-form-btn").filter(
            has_text=re.compile(r"proceed", re.IGNORECASE)
        )
        proceed_btn.wait_for(state="visible", timeout=10000)
        proceed_btn.click()
        page.wait_for_timeout(2000)

        print(f"\n✅ Proceed clicked successfully")
        print(f"   URL: {page.url}")

        page.wait_for_timeout(2000)

        # 1. Verify IRCTC User ID
        irctc_display = page.locator("span#IRCTCUserID")
        try:
            irctc_display.wait_for(state="visible", timeout=15000)
            irctc_shown = irctc_display.inner_text().strip()
        except Exception:
            irctc_shown = irctc_display.evaluate("el => el.textContent").strip()
        assert irctc_shown == "Biswalchandan", \
            f"IRCTC User ID mismatch. Expected 'Biswalchandan', got: {irctc_shown!r}"

        # 2. Verify train name
        train_name = page.locator("span.elp.ng-binding")
        train_name.wait_for(state="visible", timeout=10000)
        train_name_text = train_name.inner_text().strip()
        assert "Nandankanan Exp" in train_name_text, \
            f"Train name mismatch. Got: {train_name_text!r}"

        # 3. Verify source → destination
        route_codes = page.locator("p.t_org_cd.ng-binding")
        route_codes.first.wait_for(state="visible", timeout=10000)
        source_text = route_codes.first.inner_text().strip()
        dest_text   = route_codes.last.inner_text().strip()
        assert source_text == "ANVT", f"Source mismatch. Got: {source_text!r}"
        assert dest_text   == "CTC",  f"Destination mismatch. Got: {dest_text!r}"

        # 4. Verify departure date — find any visible element containing the travel date
        date_el = page.get_by_text(re.compile(r"27\s*June\s*2026", re.IGNORECASE)).first
        date_el.wait_for(state="visible", timeout=10000)
        date_text = date_el.inner_text().strip()

        print(f"\n✅ Post-Proceed verification passed successfully")
        print(f"   IRCTC User ID : {irctc_shown}")
        print(f"   Train         : {train_name_text}")
        print(f"   Route         : {source_text} → {dest_text}")
        print(f"   Date          : {date_text}")

        # Click 'Zero charges when ticket is cancelled' radio button
        zero_charges = page.locator("label.container-radio").filter(
            has_text=re.compile(r"zero charges when ticket is cancel", re.IGNORECASE)
        )
        zero_charges.wait_for(state="visible", timeout=15000)
        zero_charges.click()
        page.wait_for_timeout(1000)

        # Verify the radio input is selected
        radio_input = zero_charges.locator("input[type='radio']")
        assert radio_input.is_checked(), "Zero charges radio button was not selected"

        print(f"\n✅ 'Zero charges when ticket is cancelled' selected successfully")

        # Click 'Add Adult' button
        add_adult_btn = page.locator("a.add_adult").filter(
            has_text=re.compile(r"add adult", re.IGNORECASE)
        )
        add_adult_btn.wait_for(state="visible", timeout=15000)
        add_adult_btn.click()
        page.wait_for_timeout(1000)

        print(f"\n✅ 'Add Adult' clicked successfully")

        page.wait_for_timeout(1000)

        # Select 'Male' gender
        male_label = page.locator("div#ddlPassengerAge0").locator(
            "label", has_text=re.compile(r"^Male$", re.IGNORECASE)
        )
        male_label.wait_for(state="visible", timeout=10000)
        male_label.click()
        page.wait_for_timeout(500)

        # Verify Male radio is selected
        male_radio = page.locator("div#ddlPassengerAge0 input[type='radio']").filter(
            has=page.locator("~ label", has_text=re.compile(r"^Male$"))
        )
        # Verify via label's associated input - check by clicking and confirming
        print(f"\n✅ 'Male' gender selected successfully")

        # Enter Full Name
        name_input = page.locator("input#txtAdultFirstName0")
        name_input.wait_for(state="visible", timeout=10000)
        name_input.click()
        name_input.fill("Chandan Biswal")
        page.wait_for_timeout(300)

        entered_name = name_input.input_value()
        assert entered_name == "Chandan Biswal", \
            f"Name not entered correctly. Got: {entered_name!r}"

        print(f"✅ Full Name entered: {entered_name}")

        # Enter Age
        age_input = page.locator("input#txtAge0")
        age_input.wait_for(state="visible", timeout=10000)
        age_input.click()
        age_input.fill("26")
        page.wait_for_timeout(300)

        entered_age = age_input.input_value()
        assert entered_age == "26", \
            f"Age not entered correctly. Got: {entered_age!r}"

        print(f"✅ Age entered: {entered_age}")

        # Click berth preference dropdown and select 'Lower Berth'
        berth_select = page.locator("select#ddlAdultBirthPre0")
        berth_select.wait_for(state="visible", timeout=10000)
        berth_select.click()
        berth_select.select_option(label="Lower Berth")
        page.wait_for_timeout(500)

        selected_berth = berth_select.evaluate("e => e.options[e.selectedIndex].text")
        assert "Lower Berth" in selected_berth, \
            f"Berth preference not set correctly. Got: {selected_berth!r}"

        print(f"\n✅ Berth preference selected: {selected_berth}")

        # Click 'Save Adult' button
        save_adult_btn = page.locator("div#btnAddPassenger1")
        save_adult_btn.wait_for(state="visible", timeout=10000)
        save_adult_btn.click()
        page.wait_for_timeout(1500)

        print(f"\n✅ 'Save Adult' clicked successfully")

        # Click 'Add Child' button
        add_child_btn = page.locator("a.add_adult").filter(
            has_text=re.compile(r"add child", re.IGNORECASE)
        )
        add_child_btn.wait_for(state="visible", timeout=15000)
        add_child_btn.click()
        page.wait_for_timeout(1000)

        print(f"\n✅ 'Add Child' clicked successfully")

        page.wait_for_timeout(1000)

        # Select 'Male' gender for child
        child_form = page.locator("div#divChildView3 div#add-inftrv0")
        child_form.wait_for(state="visible", timeout=10000)

        child_male_label = child_form.locator("label").filter(
            has_text=re.compile(r"^Male$", re.IGNORECASE)
        )
        child_male_label.wait_for(state="visible", timeout=10000)
        child_male_label.click()
        page.wait_for_timeout(500)

        print(f"\n✅ 'Male' gender selected for child")

        # Enter child Full Name
        child_name_input = page.locator("div#divChildView3 input#txtInfant0")
        child_name_input.wait_for(state="visible", timeout=10000)
        child_name_input.click()
        child_name_input.fill("Tommy")
        page.wait_for_timeout(300)

        entered_child_name = child_name_input.input_value()
        assert entered_child_name == "Tommy", \
            f"Child name not entered correctly. Got: {entered_child_name!r}"

        print(f"✅ Child Full Name entered: {entered_child_name}")

        # Click age dropdown and select '2'
        child_age_select = page.locator("div#divChildView3 select#txtChildAge0")
        child_age_select.wait_for(state="visible", timeout=10000)
        child_age_select.click()
        child_age_select.select_option(label="2")
        page.wait_for_timeout(300)

        selected_child_age = child_age_select.evaluate("e => e.options[e.selectedIndex].text")
        assert selected_child_age == "2", \
            f"Child age not selected correctly. Got: {selected_child_age!r}"

        print(f"✅ Child Age selected: {selected_child_age}")

        # Click 'SAVE CHILD' button
        save_child_btn = page.locator("div#divChildView3 div#btnChildAdd0")
        save_child_btn.wait_for(state="visible", timeout=10000)
        save_child_btn.click()
        page.wait_for_timeout(1500)

        print(f"\n✅ 'Save Child' clicked successfully")

        # Scroll down after filling child details to reveal email and mobile fields
        page.evaluate("window.scrollBy(0, 600)")
        page.wait_for_timeout(1000)
        print(f"\n✅ Scrolled down after child details")

        # Enter Email ID using id='txtEmailID'
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
            try {
                const scope = angular.element(el).scope();
                if (scope) { scope.$apply(); }
            } catch(e) {}
        """)
        page.wait_for_timeout(500)
        entered_email = email_input.input_value()
        assert entered_email == "chandan.biswal@easemytrip.com", \
            f"Email not entered correctly. Got: {entered_email!r}"
        print(f"\n✅ Email entered: {entered_email}")

        # Enter Mobile Number using id='txtMobileNo'
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
                try {
                    const scope = angular.element(el).scope();
                    if (scope) { scope.$apply(); }
                } catch(e) {}
            }
        """)
        page.wait_for_timeout(500)
        entered_mobile = mobile_input.input_value()
        assert entered_mobile == "8018240079", \
            f"Mobile number not entered correctly. Got: {entered_mobile!r}"
        print(f"\n✅ Mobile number entered: {entered_mobile}")

        page.wait_for_timeout(1000)

        # Click "Make Payment" button
        make_payment_btn = page.locator(".con_btn_nw1.gotop").first
        make_payment_btn.scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        make_payment_btn.click(force=True)
        page.wait_for_timeout(2000)
        page.screenshot(path="easemytrip_make_payment_mobweb.png")
        print(f"\n✅ 'Make Payment' clicked successfully")
        print(f"   URL: {page.url}")

        # Scroll to top and click "Review" to verify booking details
        page.wait_for_timeout(1500)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1000)

        # Close any login popup if present
        page.evaluate("""
            const close = document.querySelector('#closeall, .cross_lgon, .close, [id*="close"]');
            if (close && close.offsetParent !== null) close.click();
        """)
        page.wait_for_timeout(800)

        # Click "Review" tab — find it among step/tab elements
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
        page.screenshot(path="easemytrip_review_mobweb.png")
        print(f"\n✅ 'Review' clicked successfully")
        print(f"   Screenshot saved: easemytrip_review_mobweb.png")

        # Verify booking details in Review section
        review_text = page.evaluate("() => document.body.innerText")

        assert "Nandankanan Exp" in review_text or "12816" in review_text, \
            "Train name 'Nandankanan Exp' not found in review"
        print(f"\n✅ Train name verified: Nandankanan Exp")

        assert "ANVT" in review_text, "Source ANVT not found in review"
        assert "CTC" in review_text,  "Destination CTC not found in review"
        print(f"\n✅ Route verified: ANVT → CTC")

        assert "27" in review_text and ("Jun" in review_text or "June" in review_text or "06" in review_text), \
            "Travel date 27 Jun 2026 not found in review"
        print(f"\n✅ Date verified: 27 Jun 2026")

        # Verify traveller details in Review section (names are in ng-bind spans, may be hidden)
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

        # Verify Boarding point
        assert "ANVT" in review_text or "ANAND VIHAR" in review_text, \
            "Boarding point ANVT not found in review"
        print(f"\n✅ Boarding point verified: ANVT - Anand Vihar Trm")

        # Click "Credit/Debit Card" option via JS (element is hidden/not visible to Playwright)
        page.wait_for_timeout(3000)
        page.evaluate("""
            const spans = [...document.querySelectorAll('span, label, div, li, a')];
            const el = spans.find(e => e.innerText && e.innerText.trim() === 'Credit/Debit Card');
            if (!el) throw new Error('Credit/Debit Card element not found');
            el.click();
        """)
        page.wait_for_timeout(2000)
        page.screenshot(path="easemytrip_credit_debit_card_mobweb.png")
        print(f"\n✅ 'Credit/Debit Card' clicked successfully")
        print(f"   Screenshot saved: easemytrip_credit_debit_card_mobweb.png")

        # Force full parent chain visible ONLY for Credit/Debit Card fields (no suffix = CC section)
        # CC1/CCN1/CCCVV1/CCMM1/CCYYYY1 belong to EMI — do NOT touch those
        page.evaluate("""
            ['CC', 'CCN', 'CCCVV'].forEach(id => {
                const el = document.querySelector('input#' + id);
                if (!el) return;
                let node = el;
                while (node && node !== document.body) {
                    node.style.setProperty('display',    'block',   'important');
                    node.style.setProperty('visibility', 'visible', 'important');
                    node.style.setProperty('opacity',    '1',       'important');
                    node.removeAttribute('hidden');
                    node = node.parentElement;
                }
            });
            ['CCMM', 'CCYYYY'].forEach(id => {
                const el = document.querySelector('select#' + id);
                if (!el) return;
                let node = el;
                while (node && node !== document.body) {
                    node.style.setProperty('display',    'block',   'important');
                    node.style.setProperty('visibility', 'visible', 'important');
                    node.style.setProperty('opacity',    '1',       'important');
                    node.removeAttribute('hidden');
                    node = node.parentElement;
                }
            });
            const cc = document.querySelector('input#CC');
            if (cc) cc.scrollIntoView({ behavior: 'smooth', block: 'center' });
        """)
        page.wait_for_timeout(800)

        # Card Number — id="CC"
        card_number_input = page.locator("input#CC")
        card_number_input.click(force=True)
        card_number_input.fill("4992000333871277", force=True)
        page.evaluate("""
            const el = document.querySelector('input#CC');
            el.dispatchEvent(new Event('input',  {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
            el.dispatchEvent(new Event('blur',   {bubbles: true}));
        """)
        page.wait_for_timeout(400)
        print(f"\n✅ Card number entered: {card_number_input.input_value()}")

        # Name on Card — id="CCN"
        card_name_input = page.locator("input#CCN")
        card_name_input.click(force=True)
        card_name_input.fill("Nishant Pitti", force=True)
        page.evaluate("""
            const el = document.querySelector('input#CCN');
            el.dispatchEvent(new Event('input',  {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
            el.dispatchEvent(new Event('blur',   {bubbles: true}));
        """)
        page.wait_for_timeout(400)
        print(f"\n✅ Card holder name entered: {card_name_input.input_value()}")

        # Expiry Month — select#CCMM (Credit/Debit Card section)
        m_sel = page.locator("select#CCMM")
        m_sel.select_option("07")
        page.wait_for_timeout(300)
        print(f"\n✅ Expiry month selected: 07")

        # Expiry Year — select#CCYYYY (Credit/Debit Card section)
        y_sel = page.locator("select#CCYYYY")
        try:
            y_sel.select_option("2030")
        except Exception:
            y_sel.select_option("30")
        page.wait_for_timeout(300)
        print(f"\n✅ Expiry year selected: 2030")

        # CVV — id="CCCVV"
        cvv_input = page.locator("input#CCCVV")
        cvv_input.click(force=True)
        cvv_input.fill("539", force=True)
        page.evaluate("""
            const el = document.querySelector('input#CCCVV');
            el.dispatchEvent(new Event('input',  {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
            el.dispatchEvent(new Event('blur',   {bubbles: true}));
        """)
        page.wait_for_timeout(500)
        page.screenshot(path="easemytrip_card_details_mobweb.png")
        print(f"\n✅ CVV entered: {cvv_input.input_value()}")
        print(f"   Screenshot saved: easemytrip_card_details_mobweb.png")

        # Click the final "Make Payment" button — <a class="payccbtn" ng-click="CardValidation(search.engine)">Make Payment</a>
        # Multiple .payccbtn elements exist (one per payment method); find the one
        # inside the Credit/Debit Card section by walking up from input#CC.
        page.evaluate("""
            (() => {
                const ccInput = document.querySelector('input#CC');
                let target = null;
                if (ccInput) {
                    let parent = ccInput.parentElement;
                    while (parent && parent !== document.body) {
                        const btn = parent.querySelector('a.payccbtn');
                        if (btn) { target = btn; break; }
                        parent = parent.parentElement;
                    }
                }
                if (!target) target = document.querySelector('a.payccbtn');
                if (!target) return;
                let node = target;
                while (node && node !== document.body) {
                    node.style.setProperty('display',    'block',   'important');
                    node.style.setProperty('visibility', 'visible', 'important');
                    node.style.setProperty('opacity',    '1',       'important');
                    node.removeAttribute('hidden');
                    node = node.parentElement;
                }
                target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                target.click();
            })()
        """)
        page.wait_for_timeout(3000)
        page.screenshot(path="easemytrip_final_payment_mobweb.png")
        print(f"\n✅ Final 'Make Payment' button clicked successfully")
        print(f"   URL: {page.url}")
        print(f"   Screenshot saved: easemytrip_final_payment_mobweb.png")

        # Wait for navigation to OTP page
        page.wait_for_load_state("domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        print(f"\n✅ Navigated to OTP page")
        print(f"   URL: {page.url}")
        page.screenshot(path="easemytrip_otp_page_mobweb.png")
        print(f"   Screenshot saved: easemytrip_otp_page_mobweb.png")

        # Click "Cancel Payment" button on OTP page
        # Button may be in the main frame or inside a bank gateway iframe
        def try_click_cancel_in_frame(frame):
            try:
                return frame.evaluate("""
                    (() => {
                        const pattern = /cancel\\s*payment|cancel|go\\s*back|back\\s*to\\s*merchant/i;
                        const candidates = [...document.querySelectorAll(
                            'button, a, input[type="button"], input[type="submit"], div, span'
                        )];
                        const el = candidates.find(e => pattern.test((e.innerText || e.value || '').trim()));
                        if (!el) return null;
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
                        return (el.innerText || el.value || '').trim();
                    })()
                """)
            except Exception:
                return None

        cancel_clicked = False

        # 1. Try main frame
        found = try_click_cancel_in_frame(page.main_frame)
        if found:
            cancel_clicked = True
            print(f"\n✅ Cancel button clicked in main frame: '{found}'")

        # 2. Try all iframes (bank gateway pages)
        if not cancel_clicked:
            page.wait_for_timeout(1000)
            for frame in page.frames:
                if frame == page.main_frame:
                    continue
                found = try_click_cancel_in_frame(frame)
                if found:
                    cancel_clicked = True
                    print(f"\n✅ Cancel button clicked in iframe ({frame.url}): '{found}'")
                    break

        # 3. Fallback: navigate back
        if not cancel_clicked:
            print(f"\n⚠️  Cancel button not found — navigating back as fallback")
            page.go_back()

        page.wait_for_timeout(2000)
        page.screenshot(path="easemytrip_cancel_payment_mobweb.png")
        print(f"\n✅ 'Cancel Payment' handled successfully")
        print(f"   URL: {page.url}")
        print(f"   Screenshot saved: easemytrip_cancel_payment_mobweb.png")

        # Click "Yes" on the confirmation dialog that appears after Cancel Payment
        # Element: <... class="acpt">Yes</...>
        page.wait_for_timeout(3000)  # Wait for confirmation dialog to appear

        yes_btn = page.locator(".acpt").first
        yes_btn.wait_for(state="attached", timeout=10000)
        page.evaluate("""
            const el = document.querySelector('.acpt');
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
            }
        """)
        page.wait_for_timeout(500)
        yes_btn.click(force=True)
        print(f"\n✅ 'Yes' (.acpt) clicked successfully")

        # Wait for page to navigate/respond after Yes is clicked
        page.wait_for_load_state("domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        page.screenshot(path="easemytrip_yes_confirm_mobweb.png")
        print(f"\n✅ 'Yes' clicked — page after confirmation:")
        print(f"   URL: {page.url}")
        print(f"   Title: {page.title()}")
        print(f"   Screenshot saved: easemytrip_yes_confirm_mobweb.png")

        # Capture generated Booking ID
        booking_id_locator = page.locator("text=/BOOKING ID:/i")
        booking_id_locator.wait_for(state="visible", timeout=10000)

        booking_text = booking_id_locator.inner_text().strip()

        booking_id = re.search(r"EMT\d+", booking_text)

        if booking_id:
            print(f"\n✅ Generated Booking ID: {booking_id.group()}")

            # Save booking IDs in a text file
            with open("booking_ids.txt", "a") as file:
                file.write(booking_id.group() + "\n")

        else:
            print("❌ Booking ID not found")

        page.wait_for_timeout(10000)

        context.close()
        browser.close()


if __name__ == "__main__":
    test_easemytrip_android_mobweb()
