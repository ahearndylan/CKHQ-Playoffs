# === bot.py ===

import tweepy
from nba_api.stats.endpoints import leaguegamefinder, boxscoretraditionalv2
from datetime import datetime, timedelta
import time
from supabase import create_client, Client
import os
from tweepy import API, OAuth1UserHandler


# ======================= #
#     SUPABASE SETUP      #
# ======================= #
supabase_url = "https://fjtxowbjnxclzcogostk.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZqdHhvd2JqbnhjbHpjb2dvc3RrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI2MDE5NTgsImV4cCI6MjA1ODE3Nzk1OH0.LPkFw-UX6io0F3j18Eefd1LmeAGGXnxL4VcCLOR_c1Q"
supabase: Client = create_client(supabase_url, supabase_key)

def load_posted_series():
    res = supabase.table("seriesposted").select("series_id").execute()
    if res.data:
        return [item["series_id"] for item in res.data]
    return []

def save_posted_series(series_id):
    supabase.table("seriesposted").insert({"series_id": series_id}).execute()

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

# Auth for v1.1 media upload
auth = OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
api_v1 = API(auth)

# ======================= #
#     MAIN BOT LOGIC      #
# ======================= #

def get_recent_playoff_games():
    start_date = "04/19/2025"
    print(f"\n🗕 Checking playoff games from {start_date} onward...\n")

    gamefinder = leaguegamefinder.LeagueGameFinder(
        season_type_nullable="Playoffs",
        date_from_nullable=start_date
    )

    games = gamefinder.get_normalized_dict()["LeagueGameFinderResults"]

    print("🧪 DEBUG: Raw playoff games returned:\n")
    for g in games:
        print(f"{g['GAME_ID']} | {g['TEAM_ABBREVIATION']} | {g['MATCHUP']} | {g['PTS']} pts")
    print("\n")

    return games

def find_matching_image(player_names):
    folder = "img"
    for name in player_names:
        first = name.split()[0].lower()
        filename = f"{first}.png"
        path = os.path.join(folder, filename)
        if os.path.exists(path):
            return path  # Return first match
    return None  # No image found

def track_series(games):
    series = {}
    games_by_id = {}

    for game in games:
        game_id = game["GAME_ID"]
        if game_id not in games_by_id:
            games_by_id[game_id] = []
        games_by_id[game_id].append(game)

    for game_id, entries in games_by_id.items():
        if len(entries) != 2:
            continue

        g1, g2 = entries[0], entries[1]
        team1 = g1["TEAM_ABBREVIATION"]
        team2 = g2["TEAM_ABBREVIATION"]
        matchup = g1["MATCHUP"] if "@" in g1["MATCHUP"] else g2["MATCHUP"]

        opponents = matchup.replace("@", "vs.").split("vs.")
        t1 = opponents[0].strip()
        t2 = opponents[1].strip()
        matchup_key = f"{t1} vs {t2}" if t1 < t2 else f"{t2} vs {t1}"

        if matchup_key not in series:
            series[matchup_key] = {"teams": (t1, t2), "games": [], t1: 0, t2: 0}

        score1 = g1["PTS"]
        score2 = g2["PTS"]

        if score1 is None or score2 is None:
            continue

        winner = g1["TEAM_ABBREVIATION"] if score1 > score2 else g2["TEAM_ABBREVIATION"]
        series[matchup_key][winner] += 1
        series[matchup_key]["games"].append(game_id)

    return series

def calculate_series_leaders(game_ids):
    player_stats = {}

    for game_id in game_ids:
        try:
            time.sleep(0.5)
            boxscore = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
            players = boxscore.get_normalized_dict()["PlayerStats"]

            for p in players:
                name = p["PLAYER_NAME"]
                pts = p["PTS"] or 0
                reb = p["REB"] or 0
                ast = p["AST"] or 0
                stl = p["STL"] or 0
                blk = p["BLK"] or 0

                if name not in player_stats:
                    player_stats[name] = {"points": 0, "rebounds": 0, "assists": 0, "stocks": 0, "games": 0}

                player_stats[name]["points"] += pts
                player_stats[name]["rebounds"] += reb
                player_stats[name]["assists"] += ast
                player_stats[name]["stocks"] += (stl + blk)
                player_stats[name]["games"] += 1

        except Exception as e:
            print(f"⚠️ Error pulling boxscore for {game_id}: {e}")

    leaders = {
        "scoring": {"name": "", "stat": 0},
        "rebounding": {"name": "", "stat": 0},
        "assists": {"name": "", "stat": 0},
        "defense": {"name": "", "stat": 0}
    }

    for player, stats in player_stats.items():
        games_played = stats["games"]
        if games_played == 0:
            continue

        ppg = stats["points"] / games_played
        rpg = stats["rebounds"] / games_played
        apg = stats["assists"] / games_played
        spg = stats["stocks"] / games_played

        if ppg > leaders["scoring"]["stat"]:
            leaders["scoring"] = {"name": player, "stat": round(ppg, 1)}
        if rpg > leaders["rebounding"]["stat"]:
            leaders["rebounding"] = {"name": player, "stat": round(rpg, 1)}
        if apg > leaders["assists"]["stat"]:
            leaders["assists"] = {"name": player, "stat": round(apg, 1)}
        if spg > leaders["defense"]["stat"]:
            leaders["defense"] = {"name": player, "stat": round(spg, 1)}

    return leaders

def compose_tweet(team_name, opponent, top_players, winner_wins, loser_wins):
    tweet = f"""\U0001f3c6 {team_name} defeat {opponent} {winner_wins}-{loser_wins} to advance! 👑

🔥 Scoring King: {top_players['scoring']['name']} – {top_players['scoring']['stat']} PPG
💪 Rebounding Beast: {top_players['rebounding']['name']} – {top_players['rebounding']['stat']} RPG
🎯 Assist Maestro: {top_players['assists']['name']} – {top_players['assists']['stat']} APG
🛡️ Defensive Anchor: {top_players['defense']['name']} – {top_players['defense']['stat']} STL+BLK

#NBAPlayoffs #CourtKingsHQ"""
    return tweet

def run_bot():
    print("🤖 Running Series Royalty Bot...")

    games = get_recent_playoff_games()
    series = track_series(games)
    posted = load_posted_series()

    for matchup_key, info in series.items():
        team1, team2 = info["teams"]
        team1_wins = info[team1]
        team2_wins = info[team2]
        game_ids = info["games"]

        print(f"🧶 {matchup_key} — {team1} {team1_wins} vs {team2} {team2_wins}")

        if matchup_key in posted:
            print(f"✅ Already posted: {matchup_key}")
            continue

        if team1_wins == 4:
            winner, loser = team1, team2
        elif team2_wins == 4:
            winner, loser = team2, team1
        else:
            print(f"⏳ Series still in progress: {matchup_key}")
            continue

        print(f"🎉 {winner} has won the series over {loser}!")

        top_players = calculate_series_leaders(game_ids)
        tweet = compose_tweet(winner, loser, top_players, info[winner], info[loser])

        print("\n🖍️ Final tweet to post:\n")
        print(tweet + "\n")

        # Try to attach a headshot image
        player_names = [
            top_players["scoring"]["name"],
            top_players["rebounding"]["name"],
            top_players["assists"]["name"],
            top_players["defense"]["name"]
        ]
        image_path = find_matching_image(player_names)

        try:
            if image_path:
                media = api_v1.media_upload(image_path)
                client.create_tweet(text=tweet, media_ids=[media.media_id])
            else:
                client.create_tweet(text=tweet)
        except Exception as e:
            print(f"❌ Error posting tweet: {e}")

        save_posted_series(matchup_key)

if __name__ == "__main__":
    run_bot()
