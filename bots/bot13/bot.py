# === bot.py ===

from nba_api.stats.endpoints import scoreboardv2
from datetime import datetime
import tweepy

# ============================ #
#      TWITTER AUTH SETUP     #
# ============================ #

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

# ============================ #
#    FETCH TODAY'S GAMES      #
# ============================ #

def fetch_todays_playoff_games():
    today = datetime.now().strftime("%m/%d/%Y")

    team_id_to_abbrev = {
        1610612737: "ATL", 1610612738: "BOS", 1610612739: "CLE", 1610612740: "NOP",
        1610612741: "CHI", 1610612742: "DAL", 1610612743: "DEN", 1610612744: "GSW",
        1610612745: "HOU", 1610612746: "LAC", 1610612747: "LAL", 1610612748: "MIA",
        1610612749: "MIL", 1610612750: "MIN", 1610612751: "BKN", 1610612752: "NYK",
        1610612753: "ORL", 1610612754: "IND", 1610612755: "PHI", 1610612756: "PHX",
        1610612757: "POR", 1610612758: "SAC", 1610612759: "SAS", 1610612760: "OKC",
        1610612761: "TOR", 1610612762: "UTA", 1610612763: "MEM", 1610612764: "WAS",
        1610612765: "DET", 1610612766: "CHA"
    }

    try:
        scoreboard = scoreboardv2.ScoreboardV2(game_date=today)
        games = scoreboard.get_normalized_dict()["GameHeader"]

        playoff_games = []

        for game in games:
            home_id = game["HOME_TEAM_ID"]
            away_id = game["VISITOR_TEAM_ID"]
            status = game["GAME_STATUS_TEXT"].strip()
            channel = game.get("NATL_TV_BROADCASTER_ABBREVIATION", "").strip()

            home = team_id_to_abbrev.get(home_id, "???")
            away = team_id_to_abbrev.get(away_id, "???")

            matchup = f"{away} vs {home}"
            time_channel = f"{status}"
            if channel:
                time_channel += f" on {channel}"

            playoff_games.append({
                "matchup": matchup,
                "time": time_channel
            })

        return playoff_games

    except Exception as e:
        print("⚠️ Error fetching today's games:", e)
        return []

# ============================ #
#     COMPOSE TWEET TEXT       #
# ============================ #

def compose_tweet(games):
    today_str = datetime.now().strftime("%A, %B %-d")

    tweet = f"👑 Today’s NBA Playoff Schedule\n📅 {today_str}\n\n"

    for game in games:
        tweet += f"🏀 {game['matchup']} – {game['time']}\n"

    tweet += "\n#NBAPlayoffs #CourtKingsHQ"
    return tweet

# ============================ #
#         MAIN LOGIC           #
# ============================ #

def run_bot():
    print("📅 Checking Today's NBA Playoff Games...\n")

    games = fetch_todays_playoff_games()

    if not games:
        print("😴 No playoff games scheduled today.")
        return

    tweet = compose_tweet(games)

    print("\n📢 Tweeting:\n")
    print(tweet)
    
    # Post the tweet
    client.create_tweet(text=tweet)
    print("\n✅ Tweet posted!")

if __name__ == "__main__":
    run_bot()
