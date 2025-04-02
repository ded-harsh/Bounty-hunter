import sqlite3
import requests
import schedule
import time
import logging
import telegram

API_KEY = "your_hibp_api_key"  #add your own api key
HEADERS = {"hibp-api-key": API_KEY}
BOT_TOKEN = "7764480585:AAFtJq8IW2N2yyDdCPZpXn-VqohNDlAvY9A"
CHAT_ID = "your_chat_id_here" #add your own chatID

# Database setup
conn = sqlite3.connect("breaches.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS breaches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        breach_name TEXT,
        domain TEXT,
        date TEXT
    )
""")
conn.commit()

def check_breach(email):
    url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}?truncateResponse=false"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        breaches = response.json()
        for breach in breaches:
            cursor.execute("INSERT INTO breaches (email, breach_name, domain, date) VALUES (?, ?, ?, ?)", 
                           (email, breach['Name'], breach['Domain'], breach['BreachDate']))
            conn.commit()
            print(f"[ALERT] Breach found: {breach['Name']} - {breach['Domain']}")
    elif response.status_code == 404:
        print("[SAFE] No breaches found.")
    else:
        print(f"[ERROR] {response.status_code} - {response.text}")

# Example usage
check_breach("test@example.com")

def get_breach_history(email):
    cursor.execute("SELECT breach_name, domain, date FROM breaches WHERE email = ?", (email,))
    results = cursor.fetchall()
    
    if results:
        print(f"[HISTORY] Breach history for {email}:")
        for breach in results:
            print(f"- {breach[0]} ({breach[1]}) on {breach[2]}")
    else:
        print(f"[SAFE] No previous breaches found for {email}")

# Example usage
get_breach_history("test@example.com")

# Set up logging
logging.basicConfig(filename="scan_history.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# Initialize bot
bot = telegram.Bot(token=BOT_TOKEN)

def send_telegram_alert(message):
    bot.send_message(chat_id=CHAT_ID, text=message)

def scheduled_scan():
    logging.info("[SCAN] Running daily breach scan...")
    results = check_for_breaches()  # Make sure this function exists in your script
    
    if results:
        alert_msg = f"🚨 *Breach Detected!* 🚨\nDetails: {results}"
        send_telegram_alert(alert_msg)
        logging.info(f"[ALERT] {alert_msg}")
    else:
        logging.info("[RESULT] No breaches detected.")

# Schedule daily scan
schedule.every().day.at("00:00").do(scheduled_scan)

# Keep running
while True:
    schedule.run_pending()
    time.sleep(60)
