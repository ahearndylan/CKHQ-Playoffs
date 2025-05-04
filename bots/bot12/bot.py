# === bot.py ===

import tweepy
from nba_api.stats.endpoints import leaguedashplayerstats
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
#    MAIN BOT LOGIC       #
# ======================= #

def get_top_playoff_scorers():
    try:
        # Only include playoff stats
        player_stats = leaguedashplayerstats.LeagueDashPlayerStats(
            season_type_all_star='Playoffs'
        ).get_normalized_dict()

        players = player_stats.get('LeagueDashPlayerStats', [])

        # Sort by POINTS scored (PTS field)
        players_sorted = sorted(players, key=lambda x: x['PTS'], reverse=True)

        # Take top 5
        top5 = players_sorted[:5]

        return top5

    except Exception as e:
        print("Error fetching playoff scoring leaders:", e)
        return []

def compose_tweet(top5):
    today = datetime.now().strftime("%B %d, %Y")
    tweet = f"👑🔥 Playoff Scoring Leaders ({today})\n\n"
    medals = ["🥇", "🥈", "🥉"]

    for idx, player in enumerate(top5, 1):
        name = player['PLAYER_NAME']
        points = int(player['PTS'])
        games = int(player['GP'])

        line = f"{points} PTS ({games} GP)"

        if idx <= 3:
            medal = medals[idx-1]
            tweet += f"{medal} {name} – {line}\n"
        else:
            tweet += f"{idx}. {name} – {line}\n"

    tweet += "\n#NBAPlayoffs #CourtKingsHQ"
    return tweet


# ======================= #
#        MAIN RUN         #
# ======================= #

def run_bot():
    print("🤖 Running Playoff Points Leaderboard Bot...")

    top5 = get_top_playoff_scorers()
    if not top5:
        print("🔝 No data found. Try again later.")
        return

    tweet = compose_tweet(top5)

    print("\n" + tweet + "\n")

    client.create_tweet(text=tweet)

if __name__ == "__main__":
    run_bot()
