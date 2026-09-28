import asyncio
from playwright.async_api import async_playwright
import sys

URL = "https://www.meteo.gr/thunders.cfm"

async def capture_map():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Ορισμός viewport για σωστή απόδοση του χάρτη
        page = await browser.new_page(viewport={'width': 1280, 'height': 800})

        try:
            print("Μετάβαση στη σελίδα...")
            # Αλλάξαμε το networkidle σε domcontentloaded για να μην κολλάει
            await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            
            print("Αναμονή για το iframe του χάρτη...")
            await page.wait_for_selector("iframe[name='frame1']", timeout=30000)
            
            map_iframe = page.locator("iframe[name='frame1']").first
            
            print("Αναμονή 15 δευτερολέπτων για φόρτωση δεδομένων χάρτη...")
            await page.wait_for_timeout(15000) 
            
            print("Λήψη στιγμιότυπου...")
            await map_iframe.screenshot(path="screenshot.png")
            print("Επιτυχία! Το στιγμιότυπο αποθηκεύτηκε ως screenshot.png")

        except Exception as e:
            print(f"Σφάλμα: {e}")
            sys.exit(1) # Τερματισμός με σφάλμα για να φανεί στο GitHub Actions
        finally:
            await browser.close()

asyncio.run(capture_map())
