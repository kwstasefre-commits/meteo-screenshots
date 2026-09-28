import asyncio
from playwright.async_api import async_playwright
import sys
import os

URL = "https://www.meteo.gr/thunders.cfm"

async def capture_map():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Προσθήκη User-Agent για να μην μας μπλοκάρει το site
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()

        try:
            print("Μετάβαση στη σελίδα...")
            await page.goto(URL, wait_until="domcontentloaded", timeout=60000)

            # Απλή αναμονή 20 δευτερολέπτων για να προλάβει να φορτώσει ο χάρτης
            print("Αναμονή 20 δευτερολέπτων για φόρτωση δεδομένων...")
            await page.wait_for_timeout(20000)

            print("Λήψη στιγμιότυπου...")
            # Ψάχνουμε το πλαίσιο (div) που περιέχει το iframe, είναι πιο σταθερό
            map_container = page.locator(".embed-responsive.embed-responsive-1by1").first
            
            if await map_container.count() > 0:
                await map_container.screenshot(path="screenshot.png")
                print("Επιτυχία! Το στιγμιότυπο αποθηκεύτηκε ως screenshot.png")
            else:
                print("Δεν βρέθηκε το container, λήψη ολόκληρης της σελίδας.")
                await page.screenshot(path="screenshot.png")
                print("Αποθηκεύτηκε ολόκληρη η σελίδα ως screenshot.png")

        except Exception as e:
            print(f"Σφάλμα: {e}")
            # Αν αποτύχει, τραβάμε μια φωτογραφία ΟΛΗΣ της σελίδας για να δούμε τι βλέπει ο browser
            print("Λήψη ολόκληρης της σελίδας για debugging...")
            await page.screenshot(path="debug_full_page.png")
            sys.exit(1)
        finally:
            await browser.close()

asyncio.run(capture_map())
