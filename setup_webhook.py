"""
Run once after Vercel deployment to register the webhook URL with Telegram.
Usage: python3 setup_webhook.py https://your-project.vercel.app
"""
import sys
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN", "")

if not TOKEN:
    sys.exit("TELEGRAM_TOKEN not set in .env")

if len(sys.argv) < 2:
    sys.exit("Usage: python3 setup_webhook.py https://your-project.vercel.app")

url = sys.argv[1].rstrip("/") + "/api/webhook"

r = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={url}")
data = r.json()

if data.get("ok"):
    print(f"Webhook set: {url}")
else:
    print(f"Failed: {data}")
