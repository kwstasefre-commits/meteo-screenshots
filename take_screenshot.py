import asyncio
from playwright.async_api import async_playwright
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

URL = "https://www.meteo.gr/thunders.cfm"

async def dismiss_popups(page):
    """Κλείνει ή κρύβει όλα τα popups και τις διαφημίσεις."""
    print("Έλεγχος για popups και διαφημίσεις...")
    buttons = ["CONFIRM", "OK", "ΟΚ", "Close", "Κλείσιμο", "Accept", "Αποδοχή", "Συνέχεια"]
    for i in range(5):
        closed = False
        for text in buttons:
            try:
                btn = page.locator(f"button:has-text('{text}'), a:has-text('{text}'), div[role='button']:has-text('{text}'), text='{text}'").first
                if await btn.is_visible():
                    await btn.click(force=True)
                    print(f"  -> Έκλεισε popup με κουμπί: '{text}'")
                    await page.wait_for_timeout(2000)
                    closed = True
                    break
            except:
                continue
        if not closed:
            break

    await page.add_style_tag(content="""
        iframe:not([src*='stratus.meteo.noa.gr']) { display: none !important; visibility: hidden !important; opacity: 0 !important; }
        .ic-consent, [id^='ic-consent'], [class^='ic-consent'], .qc-cmp2-container, #qc-cmp2-container, 
        .cmp-container, #cmp-container, div[class*='ad-'], div[id*='ad-'], div[class*='banner'], div[id*='banner'],
        [role='dialog'], [role='alertdialog'], div[class*='modal'], div[id*='modal'], div[class*='overlay'], div[id*='overlay'],
        div[style*='position: fixed'][style*='z-index'], div[style*='position: absolute'][style*='z-index: 999'],
        div[style*='position: absolute'][style*='z-index: 9999'], div[style*='position: absolute'][style*='z-index: 10000']
        { display: none !important; visibility: hidden !important; opacity: 0 !important; pointer-events: none !important; }
    """)
    print("Έγινε απόκρυψη των overlays.")

async def capture_map():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080} 
        )
        page = await context.new_page()

        try:
            print("Μετάβαση στη σελίδα...")
            await page.goto(URL, wait_until="domcontentloaded", timeout=180000)
            await page.wait_for_timeout(15000) 

            # Πρώτος καθαρισμός popups
            await dismiss_popups(page)

            print("Αναμονή για το πλαίσιο του χάρτη...")
            map_container = page.locator(".embed-responsive.embed-responsive-1by1").first
            await map_container.wait_for(state="visible", timeout=180000)

            # --- Εφαρμογή CSS για Full Screen στον χάρτη ---
            print("Εφαρμογή CSS για Full Screen στον χάρτη...")
            await page.add_style_tag(content="""
                body * { visibility: hidden; }
                .embed-responsive, .embed-responsive * { visibility: visible; }
                .embed-responsive {
                    position: fixed !important;
                    top: 0 !important;
                    left: 0 !important;
                    width: 100vw !important;
                    height: 100vh !important;
                    z-index: 99999 !important;
                    padding-bottom: 0 !important;
                }
                .embed-responsive-item {
                    width: 100% !important;
                    height: 100% !important;
                }
            """)
            await page.wait_for_timeout(3000) 

            # --- 1. Ζουμ με scroll wheel πάνω στο κέντρο του χάρτη ---
            print("Ζουμ με scroll wheel...")
            box = await map_container.bounding_box()
            if box:
                center_x = box['x'] + (box['width'] / 2)
                center_y = box['y'] + (box['height'] / 2)
                
                # Τοποθετούμε τον κέρσορα στο κέντρο του χάρτη
                await page.mouse.move(center_x, center_y)
                await page.wait_for_timeout(1000)
                
                # Κάνουμε scroll up 6 φορές για zoom in
                for i in range(6):
                    await page.mouse.wheel(0, -300)
                    print(f"  -> Scroll {i+1} για zoom in.")
                    await page.wait_for_timeout(2000) # Περιμένουμε να φορτώσουν τα πλακίδια
                
                await page.wait_for_timeout(3000)

            # --- 2. Μετακίνηση του χάρτη για εστίαση στην Καρδίτσα ---
            print("Μετακίνηση του χάρτη για εστίαση στην Καρδίτσα...")
            if box:
                start_x = box['x'] + (box['width'] / 2)
                start_y = box['y'] + (box['height'] / 2)
                
                # Σύρσιμο προς τα ΔΕΞΙΑ και ΚΑΤΩ για να φέρουμε την Καρδίτσα στο κέντρο
                await page.mouse.move(start_x, start_y)
                await page.mouse.down()
                await page.mouse.move(start_x + 1800, start_y + 1350, steps=20) 
                await page.mouse.up()
                print("  -> Ο χάρτης μετακινήθηκε.")
                await page.wait_for_timeout(5000) 

            print("Αναμονή 60 δευτερολέπτων για φόρτωση δεδομένων χάρτη...")
            await page.wait_for_timeout(60000)

            # Δεύτερος καθαρισμός
            await dismiss_popups(page)
            await page.wait_for_timeout(2000)

            timestamp = datetime.now(ZoneInfo("Europe/Athens")).strftime("%Y-%m-%d_%H-%M")
            filename = f"screenshot_{timestamp}.png"

            print(f"Λήψη στιγμιότυπου ως {filename}...")
            await page.screenshot(path=filename)
            print(f"Επιτυχία! Το στιγμιότυπο αποθηκεύτηκε ως {filename}")

        except Exception as e:
            print(f"Σφάλμα: {e}")
            print("Λήψη ολόκληρης της σελίδας για debugging...")
            await page.screenshot(path="debug_full_page.png")
            sys.exit(1)
        finally:
            await browser.close()

asyncio.run(capture_map())
