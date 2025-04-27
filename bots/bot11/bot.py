import tweepy
from nba_api.stats.endpoints import playoffpicture
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
        playoff_data = playoffpicture.PlayoffPicture().get_normalized_dict()
        east = playoff_data.get("eastConfPlayoffPicture", [])
        west = playoff_data.get("westConfPlayoffPicture", [])

        finished = []

        for series in east + west:
            if series.get("Clinched") == "Y":
                finished.append({
                    "series_id": str(series["SeedNum"]) + series["Conference"] + str(series["TeamID"]),
                    "team_name": series["TeamCity"] + " " + series["TeamName"]
                })

        return finished

    except Exception as e:
        print("Error fetching playoff picture:", e)
        return []


def get_series_top_players(series_id):
    # Placeholder players for now
    return {
        "scoring": {"name": "Example Player 1", "stat": "30.5 PPG"},
        "rebounding": {"name": "Example Player 2", "stat": "10.2 RPG"},
        "assists": {"name": "Example Player 3", "stat": "8.3 APG"},
        "defense": {"name": "Example Player 4", "stat": "2.1 STL+BLK"}
    }

def compose_tweet(team_name, top_players):
    tweet = f"""👑 Court Kings – Series Royalty 👑
🏆 {team_name} advance to the next round!

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
        print("🔝 No playoff series have finished yet. Check back soon!")
        return

    posted = load_posted_series()

    for series in finished_series:
        if series["series_id"] in posted:
            continue  # already posted about this team

        top_players = get_series_top_players(series["series_id"])
        tweet = compose_tweet(series["team_name"], top_players)

        print("\n" + tweet + "\n")

        # Uncomment to post live:
        # client.create_tweet(text=tweet)

        posted.append(series["series_id"])
        save_posted_series(posted)

if __name__ == "__main__":
    run_bot()
