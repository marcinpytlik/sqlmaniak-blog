import asyncio
from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:8765"
GOOGLE = ("googletagmanager.com", "google-analytics.com", "analytics.google.com")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        requests = []
        page.on("request", lambda r: requests.append(r.url))
        await page.goto(BASE, wait_until="networkidle")
        assert await page.locator("#site-pref-banner").is_visible(), "Consent banner not shown"
        assert not any(h in url for url in requests for h in GOOGLE), "Google requested before consent"
        await page.get_by_role("button", name="Odrzucam", exact=True).click()
        assert not await page.locator("#site-pref-banner").is_visible()
        await page.reload(wait_until="networkidle")
        assert not await page.locator("#site-pref-banner").is_visible()
        assert not any(h in url for url in requests for h in GOOGLE), "Google requested after rejection"
        await page.locator("#site-pref-open").click()
        assert await page.locator("#site-pref-settings").is_visible()
        # Prevent external analytics requests reaching Google in test environment.
        await page.route("**/gtag/js?*", lambda route: route.fulfill(status=200, content_type="application/javascript", body=""))
        await page.get_by_role("button", name="Akceptuję analitykę").click()
        await page.wait_for_function("window.gtag !== undefined")
        assert await page.evaluate("localStorage.getItem('sqlmaniak.site-preferences.v1')") == "accepted"
        assert await page.locator("#site-pref-settings").is_hidden()
        assert any("googletagmanager.com/gtag/js" in url for url in requests), "Tag not requested after consent"
        await page.reload(wait_until="networkidle")
        assert not await page.locator("#site-pref-banner").is_visible()
        await page.locator("#site-pref-open").click()
        await page.get_by_role("button", name="Odrzucam / Wycofuję zgodę").click()
        await page.wait_for_load_state("domcontentloaded")
        await page.reload(wait_until="networkidle")
        assert await page.evaluate("localStorage.getItem('sqlmaniak.site-preferences.v1')") == "rejected"
        assert not await page.locator("#site-pref-banner").is_visible()
        print("PASS: opt-in, reject, persistence, and withdrawal")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
