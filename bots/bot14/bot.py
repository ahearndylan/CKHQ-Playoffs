# bot.py — Game Final + Game Number Auto-Tweeter (Supabase + 1-Day Lookback)

import os
from nba_api.stats.endpoints import scoreboardv2, boxscoresummaryv2, leaguegamefinder
from datetime import datetime, timedelta
import tweepy
from supabase import create_client, Client

# === SUPABASE CONFIG ===
supabase_url = "https://fjtxowbjnxclzcogostk.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZqdHhvd2JqbnhjbHpjb2dvc3RrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI2MDE5NTgsImV4cCI6MjA1ODE3Nzk1OH0.LPkFw-UX6io0F3j18Eefd1LmeAGGXnxL4VcCLOR_c1Q"  # keep full key here
supabase: Client = create_client(supabase_url, supabase_key)

def load_posted_games():
    res = supabase.table("postedgames").select("game_id").execute()
    if res.data:
        return [item["game_id"] for item in res.data]
    return []

def save_posted_game(game_id):
    supabase.table("postedgames").insert({"game_id": game_id}).execute()

# === TWITTER AUTH ===
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

def get_series_game_number(team1, team2, current_game_id):
    finder = leaguegamefinder.LeagueGameFinder(season_type_nullable="Playoffs")
    all_games = finder.get_normalized_dict()["LeagueGameFinderResults"]

    series_games = [
        g for g in all_games
        if current_game_id.startswith(g["GAME_ID"][:8])
        and (g["MATCHUP"] == f"{team1} @ {team2}" or g["MATCHUP"] == f"{team2} @ {team1}")
        and g["GAME_ID"] <= current_game_id
    ]

    return len(series_games)

def run_bot():
    print("🤖 Running Game Final Score Bot...\n")

    today = datetime.today()
    yesterday = today - timedelta(days=1)
    today_str = today.strftime('%m/%d/%Y')
    yesterday_str = yesterday.strftime('%m/%d/%Y')

    games_today = scoreboardv2.ScoreboardV2(game_date=today_str).get_normalized_dict()["GameHeader"]
    games_yesterday = scoreboardv2.ScoreboardV2(game_date=yesterday_str).get_normalized_dict()["GameHeader"]
    games = games_today + games_yesterday

    posted = load_posted_games()

    for g in games:
        game_id = g["GAME_ID"]
        status = g.get("GAME_STATUS_TEXT", "").lower()
        if game_id in posted or "final" not in status:
            continue

        print(f"📦 Fetching summary for game ID: {game_id}...")
        summary = boxscoresummaryv2.BoxScoreSummaryV2(game_id=game_id)
        linescore = summary.get_normalized_dict()["LineScore"]

        if len(linescore) < 2:
            print(f"⚠️ Incomplete linescore for game {game_id}, skipping.")
            continue

        t1, t2 = linescore[0], linescore[1]
        t1_abbr, t1_pts = t1["TEAM_ABBREVIATION"], t1["PTS"]
        t2_abbr, t2_pts = t2["TEAM_ABBREVIATION"], t2["PTS"]

        if t1_pts > t2_pts:
            winner, loser = t1_abbr, t2_abbr
            win_pts, lose_pts = t1_pts, t2_pts
        else:
            winner, loser = t2_abbr, t1_abbr
            win_pts, lose_pts = t2_pts, t1_pts

        game_number = get_series_game_number(t1_abbr, t2_abbr, game_id)

        tweet = f"""👑 NBA Playoffs – Game {game_number} Final 🏀

{winner} def. {loser} {win_pts}-{lose_pts}  

#NBAPlayoffs #CourtKingsHQ"""

        print("📝 TWEET:\n" + tweet + "\n")

        try:
            client.create_tweet(text=tweet)
            save_posted_game(game_id)
        except Exception as e:
            print(f"❌ Failed to tweet game {game_id}: {e}")
            continue

    print("✅ Done.\n")

if __name__ == "__main__":
    run_bot()
