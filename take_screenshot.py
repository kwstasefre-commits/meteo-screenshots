import asyncio
from playwright.async_api import async_playwright
import sys

URL = "https://www.meteo.gr/thunders.cfm"

async def capture_map():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1280, 'height': 800})

        try:
            print("Μετάβαση στη σελίδα...")
            await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            
            print("Αναμονή για το iframe του χάρτη...")
            # Ψάχνουμε το iframe με βάση το src του (πιο ασφαλές από το name)
            await page.wait_for_selector("iframe[src*='stratus.meteo.noa.gr']", timeout=60000)
            
            map_iframe = page.locator("iframe[src*='stratus.meteo.noa.gr']").first
            
            print("Αναμονή 30 δευτερολέπτων για φόρτωση δεδομένων χάρτη...")
            await page.wait_for_timeout(30000) 
            
            print("Λήψη στιγμιότυπου...")
            await map_iframe.screenshot(path="screenshot.png")
            print("Επιτυχία! Το στιγμιότυπο αποθηκεύτηκε ως screenshot.png")

        except Exception as e:
            print(f"Σφάλμα: {e}")
            # Αν αποτύχει, τραβάμε μια φωτογραφία ΟΛΗΣ της σελίδας για να δούμε τι βλέπει ο browser
            print("Λήψη ολόκληρης της σελίδας για debugging...")
            await page.screenshot(path="debug_full_page.png")
            sys.exit(1)
        finally:
            await browser.close()

asyncio.run(capture_map())
