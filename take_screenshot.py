import asyncio
from playwright.async_api import async_playwright
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

URL = "https://www.meteo.gr/thunders.cfm"

async def dismiss_popups(page):
    """Προσπαθεί να κλείσει όλα τα popups που εμφανίζονται."""
    print("Έλεγχος και κλείσιμο popups...")
    # Λίστα με πιθανά κείμενα κουμπιών για κλείσιμο popup
    buttons = ["CONFIRM", "OK", "ΟΚ", "Close", "Κλείσιμο", "Accept", "Αποδοχή", "Συνέχεια"]
    
    # Προσπαθούμε να κλείσουμε popups σε ένα loop (μπορεί να εμφανιστούν πολλά διαδοχικά)
    for i in range(5):
        closed = False
        for text in buttons:
            try:
                # Ψάχνουμε σε buttons, a, divs με role=button
                btn = page.locator(f"button:has-text('{text}'), a:has-text('{text}'), div[role='button']:has-text('{text}')").first
                if await btn.is_visible():
                    await btn.click()
                    print(f"  -> Έκλεισε popup με κουμπί: '{text}'")
                    await page.wait_for_timeout(2000) # Περιμένουμε να δράσει το κλικ
                    closed = True
                    break # Ξαναρχίζουμε το loop γιατί μπορεί να εμφανιστεί άλλο popup
            except:
                continue
        if not closed:
            break # Αν δεν κλείσαμε τίποτα σε αυτόν τον κύκλο, σταματάμε
    
    print("Έλεγχος για υπολειπόμενα overlays...")
    # Κρύβουμε οποιοδήποτε στοιχείο έχει υψηλό z-index και είναι fixed (εκτός αν είναι ο χάρτης)
    await page.add_style_tag(content="""
        /* Στοχεύουμε popups, overlays, διαφημίσεις και consent screens */
        .ic-consent, [id^='ic-consent'], [class^='ic-consent'], 
        .qc-cmp2-container, #qc-cmp2-container, 
        .cmp-container, #cmp-container, 
        div[class*='ad-'], div[id*='ad-'], div[class*='banner'], div[id*='banner'],
        [role='dialog'], [role='alertdialog'],
        div[class*='modal'], div[id*='modal'],
        div[class*='overlay'], div[id*='overlay'],
        div[style*='position: fixed'][style*='z-index: 999'],
        div[style*='position: fixed'][style*='z-index: 9999'],
        div[style*='position: fixed'][style*='z-index: 10000'],
        div[style*='position: fixed'][style*='z-index: 99999']
        { 
            display: none !important; 
            visibility: hidden !important; 
            opacity: 0 !important;
        }
    """)
    print("Έγινε απόκρυψη πιθανών overlays με CSS.")

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

            print("Αναμονή 15 δευτερολέπτων για αρχικό φόρτωμα...")
            await page.wait_for_timeout(15000) 

            # Κλήση της συνάρτησης για κλείσιμο popups
            await dismiss_popups(page)

            print("Αναμονή για το πλαίσιο του χάρτη...")
            map_container = page.locator(".embed-responsive.embed-responsive-1by1").first
            await map_container.wait_for(state="visible", timeout=180000)

            print("Αναμονή 60 δευτερολέπτων για φόρτωση δεδομένων χάρτη...")
            await page.wait_for_timeout(60000)

            # Τελικός έλεγχος για popups που μπορεί να εμφανίστηκαν όσο περιμέναμε
            await dismiss_popups(page)

            timestamp = datetime.now(ZoneInfo("Europe/Athens")).strftime("%Y-%m-%d_%H-%M")
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
