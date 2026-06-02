import re
from playwright.sync_api import sync_playwright, expect

# Device
DEVICE_NAME = "Pixel 5"
URL = "https://www.easemytrip.com"

# Initial search
FROM_CODE   = "BBS"
TO_CODE     = "NDLS"
TRAVEL_DATE = "13/07/2026"

# Modified search
MOD_FROM_CODE = "DDU"
MOD_TO_CODE   = "CNB"
MOD_DATE      = "28/06/2026"


def test_easemytrip_modify_search_mobweb():
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

        print(f"\n✅ Page loaded successfully")
        print(f"   Title : {page.title()}")
        print(f"   URL   : {page.url}")
        print(f"   Device: {DEVICE_NAME} ({pixel5['viewport']})")
        page.screenshot(path="emt3_home.png", full_page=False)
        print("   Screenshot saved: emt3_home.png")

        # ── 2. Navigate to Trains ────────────────────────────────────────────
        trains_link = page.get_by_role("link", name=re.compile(r"trains", re.IGNORECASE))
        trains_link.first.wait_for(state="visible", timeout=15000)
        trains_link.first.click()
        page.wait_for_load_state("domcontentloaded", timeout=30000)

        print(f"\n✅ Trains page loaded successfully")
        print(f"   URL: {page.url}")
        page.screenshot(path="emt3_trains.png", full_page=False)
        print("   Screenshot saved: emt3_trains.png")

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

        page.wait_for_function("""
            () => {
                const items = document.querySelectorAll('.auto_saugg li');
                return Array.from(items).some(li => /BBS/.test(li.textContent) && !/BBSL/.test(li.textContent));
            }
        """, timeout=10000)
        page.evaluate("""
            () => {
                const items = document.querySelectorAll('.auto_saugg li');
                for (const item of items) {
                    if (/BBS/.test(item.textContent) && !/BBSL/.test(item.textContent)) { item.click(); break; }
                }
            }
        """)
        page.wait_for_timeout(1000)

        print(f"\n✅ '{FROM_CODE}' station selected successfully")
        page.screenshot(path="emt3_from.png", full_page=False)
        print("   Screenshot saved: emt3_from.png")

        # ── 4. Enter To station (NDLS) ───────────────────────────────────────
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

        page.wait_for_function("""
            () => {
                const items = document.querySelectorAll('.auto_saugg li');
                return Array.from(items).some(li => {
                    const rect = li.getBoundingClientRect();
                    return /NDLS/.test(li.textContent) && rect.width > 0 && rect.height > 0;
                });
            }
        """, timeout=15000)
        page.wait_for_timeout(500)
        page.evaluate("""
            () => {
                const items = document.querySelectorAll('.auto_saugg li');
                for (const item of items) {
                    const rect = item.getBoundingClientRect();
                    if (/NDLS/.test(item.textContent) && rect.width > 0 && rect.height > 0) { item.click(); break; }
                }
            }
        """)
        page.wait_for_timeout(1000)

        print(f"\n✅ '{TO_CODE}' station selected successfully")
        page.screenshot(path="emt3_to.png", full_page=False)
        print("   Screenshot saved: emt3_to.png")

        # ── 5. Select departure date (13 Jul 2026) ───────────────────────────
        depart_date = page.locator("#departureDate")
        depart_date.wait_for(state="visible", timeout=15000)
        depart_date.click()
        page.wait_for_timeout(2000)

        for _ in range(8):
            if page.locator("span[id*='13/07/2026']").count() > 0:
                break
            next_btn = page.locator(".next-month, .cal-next, [class*='next'], [aria-label*='next']").first
            if next_btn.count() > 0:
                next_btn.click()
                page.wait_for_timeout(800)

        page.locator("span[id*='13/07/2026']").wait_for(state="visible", timeout=10000)
        page.locator("span[id*='13/07/2026']").click()
        page.wait_for_timeout(1000)

        print(f"\n✅ Date 13 Jul 2026 selected successfully")
        page.screenshot(path="emt3_date.png", full_page=False)
        print("   Screenshot saved: emt3_date.png")

        # ── 6. Search Trains ─────────────────────────────────────────────────
        search_btn = page.locator("input.cta-btn[type='submit']")
        search_btn.wait_for(state="visible", timeout=15000)
        search_btn.click()
        page.wait_for_load_state("domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)

        print(f"\n✅ Search Trains clicked successfully")
        print(f"   URL: {page.url}")
        page.screenshot(path="emt3_results.png", full_page=False)
        print("   Screenshot saved: emt3_results.png")

        # ── 7. Verify initial results page ───────────────────────────────────
        assert FROM_CODE in page.url and TO_CODE in page.url, f"Route not in URL: {page.url}"
        route_header = page.locator(".trainhdr-pill")
        route_header.wait_for(state="visible", timeout=15000)
        route_text = route_header.inner_text()

        print(f"\n✅ Initial results page verified")
        print(f"   Route: {route_text.strip()}")

        # ── 8. Click Edit button (top right of results page) ────────────────
        # Wait for loader to be gone before clicking edit
        page.locator("#div_Cotant").wait_for(state="hidden", timeout=15000)
        page.wait_for_timeout(500)
        edit_clicked = page.evaluate("""
            () => {
                const el = [...document.querySelectorAll('a, button, div, span, i')]
                    .find(e => {
                        const cls = (e.className || '').toLowerCase();
                        const rect = e.getBoundingClientRect();
                        return rect.width > 0 && rect.height > 0 &&
                            (cls.includes('edit') || cls.includes('pencil') || cls.includes('modify'));
                    });
                if (!el) return null;
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                el.click();
                return el.className || 'clicked';
            }
        """)
        assert edit_clicked, "Could not find Edit button on results page"
        # Wait for the loading overlay to disappear before interacting with the form
        page.locator("#div_Cotant").wait_for(state="hidden", timeout=15000)
        page.wait_for_timeout(500)
        page.screenshot(path="emt3_edit_open.png", full_page=False)
        print(f"\n✅ Edit button clicked successfully")
        print(f"   Screenshot saved: emt3_edit_open.png")

        # ── 9. Change From station to DDU ────────────────────────────────────
        from_field2 = page.locator("#mob_txtfromcity")
        from_field2.wait_for(state="visible", timeout=8000)
        from_field2.scroll_into_view_if_needed()
        from_field2.click()
        page.wait_for_timeout(500)
        page.keyboard.press("Control+A")
        page.keyboard.press("Delete")
        page.wait_for_timeout(300)
        for ch in MOD_FROM_CODE:
            page.keyboard.type(ch)
            page.wait_for_timeout(400)
        page.wait_for_timeout(600)

        # Wait for dropdown with DDU suggestion (uses [class*="dropdown"] children, not li)
        page.wait_for_function("""
            () => {
                const dd = document.querySelector('[class*="dropdown"]');
                return dd && dd.getBoundingClientRect().width > 0
                    && /DDU/.test(dd.textContent);
            }
        """, timeout=10000)
        page.evaluate("""
            () => {
                const dd = document.querySelector('[class*="dropdown"]');
                const child = [...dd.children].find(el => /DDU/.test(el.textContent));
                if (child) child.click();
            }
        """)
        page.wait_for_timeout(1000)
        print(f"\n✅ From station changed to 'Dd Upadhyaya Jn (DDU)'")
        page.screenshot(path="emt3_mod_from.png", full_page=False)
        print("   Screenshot saved: emt3_mod_from.png")

        # ── 10. Change To station to CNB ─────────────────────────────────────
        to_field2 = page.locator("#mob_txtdesticity")
        to_field2.wait_for(state="visible", timeout=8000)
        to_field2.scroll_into_view_if_needed()
        to_field2.click()
        page.wait_for_timeout(500)
        page.keyboard.press("Control+A")
        page.keyboard.press("Delete")
        page.wait_for_timeout(300)
        for ch in MOD_TO_CODE:
            page.keyboard.type(ch)
            page.wait_for_timeout(400)
        page.wait_for_timeout(600)

        # Wait for "Kanpur Central (CNB)" suggestion — use querySelectorAll to find visible dropdown
        page.wait_for_function("""
            () => [...document.querySelectorAll('[class*="dropdown"]')]
                .some(dd => dd.getBoundingClientRect().width > 0 && /CNB/.test(dd.textContent))
        """, timeout=10000)
        page.wait_for_timeout(300)
        page.evaluate("""
            () => {
                const dd = [...document.querySelectorAll('[class*="dropdown"]')]
                    .find(dd => dd.getBoundingClientRect().width > 0 && /CNB/.test(dd.textContent));
                if (dd) {
                    const child = [...dd.children].find(el => /CNB/.test(el.textContent));
                    if (child) child.click();
                }
            }
        """)
        page.wait_for_timeout(1000)
        print(f"\n✅ To station changed to 'Kanpur Central (CNB)'")
        page.screenshot(path="emt3_mod_to.png", full_page=False)
        print("   Screenshot saved: emt3_mod_to.png")

        # ── 11. Change date to 28 Jun 2026 ───────────────────────────────────
        # The form submits via hidden #txtDate (DD/MM/YYYY); mob_datePicker is visual only
        page.evaluate("""
            () => {
                // Set the hidden field used for form submission
                const txtDate = document.querySelector('#txtDate');
                if (txtDate) {
                    txtDate.value = '28/06/2026';
                    txtDate.dispatchEvent(new Event('change', {bubbles: true}));
                }
                // Also update the visible date picker
                const el = document.querySelector('#mob_datePicker');
                if (el) {
                    el.scrollIntoView({block:'center'});
                    const setter = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value').set;
                    setter.call(el, '2026-06-28');
                    el.dispatchEvent(new Event('input', {bubbles: true}));
                    el.dispatchEvent(new Event('change', {bubbles: true}));
                }
            }
        """)
        page.wait_for_timeout(1000)
        print(f"\n✅ Date changed to 28 Jun 2026")
        page.screenshot(path="emt3_mod_date.png", full_page=False)
        print("   Screenshot saved: emt3_mod_date.png")

        # ── 12. Click Modify Search ───────────────────────────────────────────
        # The button is <a class="fill_btn ...">Modify Search</a>
        modify_result = page.evaluate("""
            () => {
                const el = document.querySelector('a.fill_btn')
                    || [...document.querySelectorAll('a, button')]
                        .find(e => (e.innerText || '').trim() === 'Modify Search'
                            && e.getBoundingClientRect().width > 0);
                if (!el) return null;
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                el.click();
                return (el.innerText || el.value || '').trim();
            }
        """)
        assert modify_result, "Could not find 'Modify Search' button"
        page.wait_for_load_state("domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)
        page.screenshot(path="emt3_modify_results.png", full_page=False)
        print(f"\n✅ 'Modify Search' clicked successfully (matched: '{modify_result}')")
        print(f"   URL: {page.url}")
        print(f"   Screenshot saved: emt3_modify_results.png")

        # ── 13. Verify new results ────────────────────────────────────────────
        assert MOD_FROM_CODE in page.url, f"Modified From ({MOD_FROM_CODE}) not in URL: {page.url}"
        assert MOD_TO_CODE   in page.url, f"Modified To ({MOD_TO_CODE}) not in URL: {page.url}"
        assert "28/06/2026"  in page.url, f"Modified date not in URL: {page.url}"

        mod_route = page.locator(".trainhdr-pill")
        mod_route.wait_for(state="visible", timeout=15000)
        mod_route_text = mod_route.inner_text()
        assert MOD_FROM_CODE in mod_route_text and MOD_TO_CODE in mod_route_text, \
            f"Modified route mismatch: {mod_route_text}"

        print(f"\n✅ Modified results verified successfully")
        print(f"   Route: {mod_route_text.strip()}")

        context.close()
        browser.close()


if __name__ == "__main__":
    test_easemytrip_modify_search_mobweb()
