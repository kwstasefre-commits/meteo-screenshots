import asyncio
from playwright.async_api import async_playwright
import sys
from datetime import datetime

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

            print("Αναμονή 15 δευτερολέπτων για εμφάνιση popup cookies...")
            await page.wait_for_timeout(15000) 

            # --- Κλείσιμο Cookies ---
            try:
                confirm_button = page.locator("button", has_text="CONFIRM").first
                if await confirm_button.is_visible():
                    await confirm_button.click()
                    print("Το popup των cookies έκλεισε με επιτυχία.")
                    await page.wait_for_timeout(5000) # Περιμένουμε να φορτώσει η διαφήμιση
                else:
                    raise Exception("Το κουμπί δεν είναι ορατό")
            except Exception as e:
                print(f"Αποτυχία κλεισίματος cookies: {e}")

            # --- ΝΕΟ: Κλείσιμο Διαφήμισης ---
            print("Έλεγχος για διαφημίσεις...")
            try:
                # Ψάχνουμε για το κουμπί "Κλείσιμο" ή "Close" ή το εικονίδιο 'x'
                close_ad_button = page.locator("button:has-text('Κλείσιμο'), button:has-text('Close'), text='Κλείσιμο', text='Close', [aria-label='Close'], .close-ad, .ad-close").first
                
                if await close_ad_button.is_visible():
                    await close_ad_button.click()
                    print("Η διαφήμιση έκλεισε επιτυχώς.")
                    await page.wait_for_timeout(2000)
                else:
                    print("Δεν βρέθηκε κουμπί κλεισίματος διαφήμισης. Προσπάθεια απόκρυψης...")
                    # Κρύβουμε δυναμικά τα γνωστά containers διαφημίσεων
                    await page.add_style_tag(content="""
                        .ic-consent, [id^='ic-consent'], [class^='ic-consent'], 
                        .qc-cmp2-container, #qc-cmp2-container, 
                        .cmp-container, #cmp-container, 
                        div[class*='ad-'], div[id*='ad-'], div[class*='banner'], div[id*='banner'],
                        div[style*='z-index: 999'], div[style*='z-index:9999'],
                        div[style*='position: fixed'][style*='top: 0']
                        { display: none !important; visibility: hidden !important; }
                    """)
                    print("Έγινε προσπάθεια απόκρυψης της διαφήμισης με CSS.")
            except Exception as e:
                print(f"Αποτυχία κλεισίματος διαφήμισης: {e}")

            print("Αναμονή για το πλαίσιο του χάρτη...")
            map_container = page.locator(".embed-responsive.embed-responsive-1by1").first
            await map_container.wait_for(state="visible", timeout=180000)

            print("Αναμονή 60 δευτερολέπτων για φόρτωση δεδομένων χάρτη...")
            await page.wait_for_timeout(60000)

            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            filename = f"screenshot_{timestamp}.png"

            print(f"Λήψη στιγμιότυπου ως {filename}...")
            await map_container.screenshot(path=filename)
            print(f"Επιτυχία! Το στιγμιότυπο αποθηκεύτηκε ως {filename}")

        except Exception as e:
            print(f"Σφάλμα: {e}")
            print("Λήψη ολόκληρης της σελίδας για debugging...")
            await page.screenshot(path="debug_full_page.png")
            sys.exit(1)
        finally:
            await browser.close()

asyncio.run(capture_map())
