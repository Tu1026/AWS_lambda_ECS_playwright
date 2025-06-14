from playwright.sync_api import Playwright, sync_playwright
import requests
import os
from dotenv import load_dotenv
import time
import random

# Load environment variables from .env file
load_dotenv()

TARGET_URL = os.getenv("TARGET_URL")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def run(playwright: Playwright) -> None:
	browser = playwright.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
	ua = (
		"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
	)
	context = browser.new_context(user_agent=ua)
	page = context.new_page()
	page.goto(url=TARGET_URL, wait_until="domcontentloaded")
	page.locator("#licenseTypeCode").select_option("3")
	page.locator("#expectExamDateStr").click()
	page.locator("#expectExamDateStr").fill("1140708")
	page.locator("select[name=\"dmvNoLv1\"]").select_option("20")
	page.locator("#dmvNo").select_option("21")
	page.get_by_role("link", name="查詢場次 Search").click()
	page.get_by_role("link", name="選擇場次繼續報名").click()
	
	has_non_empty_4th_td = page.evaluate("""
		() => {
			const rows = document.querySelectorAll('#trnTable tbody tr');
			for (const row of rows) {
				const tds = row.querySelectorAll('td');
				const fourthTd = tds[3]; // index 3 = 4th td
				if (tds.length >= 4 && tds[3].textContent.trim() !== '' && !tds[1].textContent.includes("初考生勿預約本場次")) {
					return true;
				}
			}
			return false;
		}
	""")
	if has_non_empty_4th_td:
		print("✅ At least one 4th <td> element is non-empty and does not contain '初考生勿預約本場次'.")
		# Notify via Discord
		notify_discord("✅ 有可報名的場次！請前往 {} 查看。".format(TARGET_URL))
	else:
		print("❌ All 4th <td> elements are empty or missing.")

	# ---------------------
	context.close()
	browser.close()




def notify_discord(message: str):
	webhook_url = DISCORD_WEBHOOK_URL
	data = {
		"content": message
	}
	response = requests.post(webhook_url, json=data)
	if response.status_code != 204:
		print(f"Failed to send Discord message: {response.text}")


# with sync_playwright() as playwright:
playwright = sync_playwright().start()
run(playwright)
