import os
from dotenv import load_dotenv
import random
import discord
import asyncio
from playwright.async_api import async_playwright
import sys
import argparse

# Load environment variables from .env file
load_dotenv()

TARGET_URL = os.getenv("TARGET_URL")
TOKEN = os.getenv("DISCORD_TOKEN")
TARGET_USER_ID = int(os.getenv("TARGET_USER_ID"))  # Ensure this is an integer
# Message you want to send
NOTIFY_MESSAGE = f"✅ 有可報名的場次！請前往 {TARGET_URL} 查看。"


# --- Main scraping logic ---
async def check_exam_slots():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        context = await browser.new_context(user_agent=ua)
        page = await context.new_page()
        await page.goto(TARGET_URL, wait_until="domcontentloaded")
        await page.locator("#licenseTypeCode").select_option("3")
        await page.locator("#expectExamDateStr").click()
        await page.locator("#expectExamDateStr").fill("1140708")
        await page.locator('select[name="dmvNoLv1"]').select_option("20")
        await page.locator("#dmvNo").select_option("21")
        await page.get_by_role("link", name="查詢場次 Search").click()
        await page.get_by_role("link", name="選擇場次繼續報名").click()

        has_slot = await page.evaluate(
            """
            () => {
                const rows = document.querySelectorAll('#trnTable tbody tr');
                for (const row of rows) {
                    const tds = row.querySelectorAll('td');
                    if (tds.length >= 4 && tds[3].textContent.trim() !== '' &&
                        !tds[1].textContent.includes("初考生勿預約本場次")) {
                        return true;
                    }
                }
                return false;
            }
        """
        )

        await browser.close()
        return has_slot


# --- Message sending logic using discord.Client ---
class SlotNotifier(discord.Client):
    def __init__(self, user_id, message, **kwargs):
        super().__init__(intents=discord.Intents.default(), **kwargs)
        self.user_id = user_id
        self.message = message

    async def on_ready(self):
        print(f"🔔 Logged in as {self.user}")
        user = await self.fetch_user(self.user_id)
        for _ in range(5):
            await user.send(self.message)
        await self.close()  # shut down after sending


# --- Main loop ---
async def main():
    has_available = await check_exam_slots()
    if has_available:
        print("✅ Slot found! Sending notification...")
        notifier = SlotNotifier(user_id=TARGET_USER_ID, message=NOTIFY_MESSAGE)
        await notifier.start(TOKEN)  # Runs and auto-shuts down
    else:
        print("❌ No available slots")


async def main_loop():
    while True:
        has_available = await check_exam_slots()
        if has_available:
            print("✅ Slot found! Sending notification...")
            notifier = SlotNotifier(user_id=TARGET_USER_ID, message=NOTIFY_MESSAGE)
            await notifier.start(TOKEN)  # Runs and auto-shuts down
            break  # Exit loop after notifying
        else:
            print("❌ No available slots. Will retry.")

        wait_time = random.randint(30, 60)
        print(f"⏳ Waiting {wait_time} seconds...")
        await asyncio.sleep(wait_time)


# --- Entry point ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", action="store_true", help="Run in loop mode")
    args = parser.parse_args()
    if args.loop:
        asyncio.run(main_loop())
    else:
        asyncio.run(main())
