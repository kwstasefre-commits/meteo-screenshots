import asyncio
from playwright.async_api import async_playwright
import sys

URL = "https://www.meteo.gr/thunders.cfm"

async def capture_map():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()

        try:
            print("Μετάβαση στη σελίδα...")
            await page.goto(URL, wait_until="domcontentloaded", timeout=180000)

            # --- ΝΕΟ: Προσπάθεια κλεισίματος του popup των cookies ---
            print("Έλεγχος για popup cookies...")
            # Περιμένουμε 5 δευτερόλεπτα μήπως εμφανιστεί το popup
            await page.wait_for_timeout(5000) 
            
            try:
                # Ψάχνουμε το κουμπί με το κείμενο "CONFIRM"
                confirm_button = page.locator("button:has-text('CONFIRM'), a:has-text('CONFIRM'), text='CONFIRM'").first
                
                if await confirm_button.is_visible():
                    await confirm_button.click()
                    print("Το popup των cookies έκλεισε επιτυχώς.")
                    # Περιμένουμε λίγο να εξαφανιστεί το popup από την οθόνη
                    await page.wait_for_timeout(2000) 
                else:
                    print("Δεν βρέθηκε popup cookies. Συνεχίζουμε...")
            except Exception as e:
                print(f"Αποτυχία κλεισίματος cookies (ίσως να μην υπάρχει popup): {e}")
            # --------------------------------------------------------

            print("Αναμονή για το πλαίσιο του χάρτη...")
            map_container = page.locator(".embed-responsive.embed-responsive-1by1").first
            await map_container.wait_for(state="visible", timeout=180000)

            print("Αναμονή 60 δευτερολέπτων για φόρτωση δεδομένων...")
            await page.wait_for_timeout(60000)

            print("Λήψη στιγμιότυπου...")
            await map_container.screenshot(path="screenshot.png")
            print("Επιτυχία! Το στιγμιότυπο αποθηκεύτηκε ως screenshot.png")

        except Exception as e:
            print(f"Σφάλμα: {e}")
            print("Λήψη ολόκληρης της σελίδας για debugging...")
            await page.screenshot(path="debug_full_page.png")
            sys.exit(1)
        finally:
            await browser.close()

asyncio.run(capture_map())
