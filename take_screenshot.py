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
            viewport={'width': 1280, 'height': 800}
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

            # --- ΝΕΟ: Ζουμ και Κέντραρισμα στην Καρδίτσα ---
            print("Προετοιμασία για ζουμ στην Καρδίτσα...")
            
            # Χρήση του frame_locator για να μπούμε μέσα στο iframe του χάρτη
            frame = page.frame_locator("iframe[src*='stratus.meteo.noa.gr']")
            
            # Κλικ στο κουμπί zoom in (+) 4 φορές
            zoom_in_btn = frame.locator(".leaflet-control-zoom-in")
            if await zoom_in_btn.count() > 0:
                print("Ζουμ in (4 κλικ)...")
                for _ in range(4):
                    await zoom_in_btn.click()
                    await page.wait_for_timeout(2000) # Περιμένουμε να φορτώσουν τα πλακίδια του χάρτη
            else:
                print("Δεν βρέθηκε το κουμπί ζουμ. Παράλειψη.")

            # Μετακίνηση του χάρτη (σύρσιμο) για να κεντράρουμε στην Καρδίτσα
            # Επειδή η Καρδίτσα είναι βορειοδυτικά της Αθήνας, σέρνουμε τον χάρτη προς τα δεξιά-κάτω
            print("Μετακίνηση του χάρτη για εστίαση στην Καρδίτσα...")
            box = await map_container.bounding_box()
            if box:
                center_x = box['x'] + (box['width'] / 2)
                center_y = box['y'] + (box['height'] / 2)
                
                # Σύρσιμο από το κέντρο προς τα δεξιά-κάτω (για να πάει ο χάρτης αριστερά-πάνω)
                await page.mouse.move(center_x, center_y)
                await page.mouse.down()
                # Προσαρμόζεις τις παρακάτω τιμές αν χρειαστεί (π.χ. +200, +150)
                await page.mouse.move(center_x + 150, center_y + 100, steps=10)
                await page.mouse.up()
                await page.wait_for_timeout(3000) # Περιμένουμε να σταθεροποιηθεί ο χάρτης
            # ---------------------------------------------

            print("Αναμονή 60 δευτερολέπτων για φόρτωση δεδομένων χάρτη...")
            await page.wait_for_timeout(60000)

            # Δεύτερος καθαρισμός (για διαφημίσεις που φόρτωσαν αργότερα)
            await dismiss_popups(page)
            await page.wait_for_timeout(2000)

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
