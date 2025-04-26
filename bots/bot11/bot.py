import tweepy
from nba_api.stats.endpoints import commonplayoffseries, boxscoretraditionalv2
from datetime import datetime
import json
import os
import time

# ======================= #
# TWITTER AUTHENTICATION  #
# ======================= #
bearer_token = "YOUR_BEARER_TOKEN"
api_key = "YOUR_API_KEY"
api_secret = "YOUR_API_SECRET"
access_token = "YOUR_ACCESS_TOKEN"
access_token_secret = "YOUR_ACCESS_TOKEN_SECRET"

client = tweepy.Client(
    bearer_token=bearer_token,
    consumer_key=api_key,
    consumer_secret=api_secret,
    access_token=access_token,
    access_token_secret=access_token_secret
)

POSTED_FILE = "posted_series.json"

# ======================= #
#    LOAD/SAVE HELPERS    #
# ======================= #

def load_posted_series():
    if not os.path.exists(POSTED_FILE):
        return []
    with open(POSTED_FILE, "r") as f:
        return json.load(f)

def save_posted_series(posted):
    with open(POSTED_FILE, "w") as f:
        json.dump(posted, f, indent=2)

# ======================= #
#     MAIN BOT LOGIC      #
# ======================= #

def get_finished_series():
    try:
        playoff_data = commonplayoffseries.CommonPlayoffSeries().get_normalized_dict()
        series_list = playoff_data["Series"]

        finished = []
        for series in series_list:
            if series["IF_NECESSARY"] == 0 and series["SERIES_STATUS_TEXT"]:
                status = series["SERIES_STATUS_TEXT"]
                if "wins" in status.lower() or "won" in status.lower():
                    finished.append({
                        "series_id": series["SERIES_ID"],
                        "winner": series["HOME_TEAM_ABBREVIATION"] if series["HOME_TEAM_WINS"] > series["VISITOR_TEAM_WINS"] else series["VISITOR_TEAM_ABBREVIATION"],
                        "loser": series["VISITOR_TEAM_ABBREVIATION"] if series["HOME_TEAM_WINS"] > series["VISITOR_TEAM_WINS"] else series["HOME_TEAM_ABBREVIATION"]
                    })
        return finished

    except Exception as e:
        print("Error fetching playoff series:", e)
        return []

def get_series_top_players(series_id):
    # This will fetch stats across all games for a given series
    # Right now we'll fake some players because nba_api doesn't have direct series summary
    # You could extend this by manually fetching each game_id in the series later if needed
    return [
        {"name": "Example Player 1", "stat": "30.5 PPG"},
        {"name": "Example Player 2", "stat": "10.2 RPG"},
        {"name": "Example Player 3", "stat": "8.3 APG"}
    ]

def compose_tweet(winner, loser, series_record, top_players):
    tweet = f"""👑 Court Kings – Series Royalty 👑
🏆 {winner} def. {loser} {series_record}

🔥 Scoring King: {top_players['scoring']['name']} – {top_players['scoring']['stat']}
💪 Rebounding Beast: {top_players['rebounding']['name']} – {top_players['rebounding']['stat']}
🎯 Assist Maestro: {top_players['assists']['name']} – {top_players['assists']['stat']}
🛡️ Defensive Anchor: {top_players['defense']['name']} – {top_players['defense']['stat']}

#NBAPlayoffs #CourtKingsHQ"""
    
    return tweet


# ======================= #
#         MAIN RUN        #
# ======================= #

def run_bot():
    print("🤖 Running Series Royalty Bot...")

    finished_series = get_finished_series()
    if not finished_series:
        print("🛑 No playoff series have finished yet. Check back soon!")
        return

    posted = load_posted_series()

    for series in finished_series:
        if series["series_id"] in posted:
            continue  # already posted about this series

        top_players = get_series_top_players(series["series_id"])
        tweet = compose_tweet(series["winner"], series["loser"], top_players)

        print("\n" + tweet + "\n")

        # 🚀 Uncomment this when you are ready to tweet for real:
        # client.create_tweet(text=tweet)

        posted.append(series["series_id"])
        save_posted_series(posted)

if __name__ == "__main__":
    run_bot()
