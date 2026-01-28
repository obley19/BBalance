
import asyncio
import sys
import os

# Ensure src is in python path
sys.path.append(os.getcwd())

from src.crawler.spiders import EbayAsyncSpider

# Full list from user request
KEYWORDS = [
    # --- 1. COMPUTING & GAMING (Core) ---
    "laptop", "gaming laptop", "macbook air m3", "macbook pro m3", "chromebook", "microsoft surface pro",
    "gaming pc", "alienware desktop", "mini pc ryzen", "rtx 4090", "rtx 4080 super", "rtx 3060", 
    "intel i9 14900k", "ryzen 9 7950x", "motherboard am5", "ddr5 ram 32gb", "nvme ssd 2tb",
    "gaming monitor 240hz", "ultrawide monitor", "mechanical keyboard rk61", "logitech g pro mouse",
    "razer headset", "elgato stream deck", "capture card 4k", "nas storage", "workstation laptop",

    # --- 2. MOBILE & WEARABLES ---
    "iphone 15 pro max", "iphone 14 pro", "samsung galaxy s24 ultra", "google pixel 8 pro",
    "ipad pro m2", "ipad air 5", "samsung galaxy tab s9", "kindle paperwhite 5",
    "apple watch ultra 2", "garmin fenix 7", "galaxy watch 6", "fitbit charge 6",
    "airpods pro 2", "sony wf-1000xm5", "bose quietcomfort ultra", "beats studio buds",

    # --- 3. PHOTOGRAPHY & VIDEO ---
    "sony a7 iv", "canon eos r6 mark ii", "fujifilm x-t5", "nikon z6 ii", "leica m11",
    "dji mavic 3 pro", "dji mini 4 pro", "gopro hero 12", "insta360 x3",
    "sony g master lens", "canon rf lens", "sigma art lens", "camera tripod carbon",
    "ronin rs3 gimbal", "wireless microphone dji", "studio light led",

    # --- 4. SMART HOME & HOME APPLIANCES ---
    "dyson v15 vacuum", "roborock s8", "ecovacs deebot", "philips hue starter kit",
    "nest thermostat", "ring video doorbell", "august smart lock", "apple tv 4k",
    "philips air fryer", "kitchenaid artisan mixer", "nespresso coffee machine",
    "blueair purifier", "dehumidifier portable", "portable air conditioner",

    # --- 5. AUDIO & ENTERTAINMENT ---
    "playstation 5 console", "nintendo switch oled", "xbox series x", "steam deck 512gb",
    "sonos era 300", "jbl partybox", "marshall stanmore iii", "vinyl record player",
    "fiio dac amp", "sennheiser hd600", "beyerdynamic dt 990 pro", "blue yeti microphone",

    # --- 6. NETWORK & OFFICE ---
    "starlink internet kit", "asus rog rapture router", "tp-link deco mesh", "synology ds923",
    "brother laser printer", "epson ecotank", "standing desk electric", "herman miller aeron",
    "wacom cintiq", "huion drawing tablet", "anker 100w charger", "portable power station",

    # --- 7. NICHE & HIGH VALUE ---
    "vintage rolex", "omega speedmaster", "pokemon booster box", "lego star wars ucs",
    "rare sneakers", "jordan 1 retro", "graphics card refurbished", "mining rig frame"
]

async def main():
    print("🚀 Starting eBay Crawler (Manual Interaction Mode)...")
    print("ℹ️  Browser window will open. If CAPTCHA appears, solve it in the browser.")
    
    spider = EbayAsyncSpider()
    print(f"📂 Output file: {spider.output_file}")
    
    # Run crawl for each keyword
    # User requested more items, so we increase max_pages to 20
    for kw in KEYWORDS:
        await spider.crawl_category(
            category_id=kw, 
            max_pages=20, 
            headless=False # Enable headful mode for manual CAPTCHA solving
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")