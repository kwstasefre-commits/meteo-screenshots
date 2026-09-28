import asyncio
from playwright.async_api import async_playwright

URL = "https://www.meteo.gr/thunders.cfm"

async def capture_map():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            # Μετάβαση στη σελίδα και αναμονή φόρτωσης
            await page.goto(URL, wait_until="networkidle", timeout=60000)

            # Αναμονή για το iframe του χάρτη
            await page.wait_for_selector("iframe[name='frame1']", timeout=30000)

            # Εντοπισμός του iframe
            map_iframe = page.locator("iframe[name='frame1']").first

            # Αναμονή για να φορτώσουν τα δεδομένα του χάρτη
            await page.wait_for_timeout(8000)

            # Λήψη στιγμιότυπου ΜΟΝΟ του iframe
            await map_iframe.screenshot(path="screenshot.png")
            print("Επιτυχία! Το στιγμιότυπο αποθηκεύτηκε ως screenshot.png")

        except Exception as e:
            print(f"Σφάλμα: {e}")
        finally:
            await browser.close()

asyncio.run(capture_map())
