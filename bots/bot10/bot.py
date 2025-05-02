import tweepy
import json
import random
from datetime import datetime
import os

# ======================= #
# TWITTER AUTHENTICATION  #
# ======================= #
bearer_token = "AAAAAAAAAAAAAAAAAAAAAPztzwEAAAAAvBGCjApPNyqj9c%2BG7740SkkTShs%3DTCpOQ0DMncSMhaW0OA4UTPZrPRx3BHjIxFPzRyeoyMs2KHk6hM"
api_key = "uKyGoDr5LQbLvu9i7pgFrAnBr"
api_secret = "KGBVtj1BUmAEsyoTmZhz67953ItQ8TIDcChSpodXV8uGMPXsoH"
access_token = "1901441558596988929-WMdEPOtNDj7QTJgLHVylxnylI9ObgD"
access_token_secret = "9sf83R8A0MBdijPdns6nWaG7HF47htcWo6oONPmMS7o98"

client = tweepy.Client(
    bearer_token=bearer_token,
    consumer_key=api_key,
    consumer_secret=api_secret,
    access_token=access_token,
    access_token_secret=access_token_secret
)

# ======================= #
#    MAIN BOT FUNCTION    #
# ======================= #

def load_events():
    base_dir = os.path.dirname(__file__)
    file_path = os.path.join(base_dir, "playoff_moments.json")

    with open(file_path, "r") as f:
        return json.load(f)

def get_today_event(events):
    today = datetime.now()
    today_str = today.strftime("%B %-d")  # Example: "May 15"
    today_str_alt = today.strftime("%B %#d")  # Windows alternate (for local testing)

    todays_events = [e for e in events if e["date"] in (today_str, today_str_alt)]
    return random.choice(todays_events) if todays_events else None

def compose_tweet(event):
    # Parse date components
    today_date = datetime.strptime(event["date"], "%B %d")
    full_date = today_date.strftime("%B %d")
    year = event["year"]

    return f"""🏀 On This Day - NBA Playoff History  
🗓️ {full_date}, {year}

{event['event']}

#NBAPlayoffs #OTD #CourtKingsHQ"""


def run_bot():
    events = load_events()
    event = get_today_event(events)

    if event:
        tweet = compose_tweet(event)
        print("Tweeting:\n", tweet)
        try:
            client.create_tweet(text=tweet)
            print("✅ Tweet posted!")
        except Exception as e:
            print("❌ Failed to post tweet:", e)
    else:
        print("🕰️ No playoff event found for today.")

if __name__ == "__main__":
    run_bot()
