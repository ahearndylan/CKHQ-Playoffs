# bot.py — Game Final + Game Number Auto-Tweeter

import json
import os
from nba_api.stats.endpoints import scoreboardv2, boxscoresummaryv2, leaguegamefinder
from datetime import datetime
import tweepy

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

POSTED_FILE = "posted_games.json"

def load_posted_games():
    if not os.path.exists(POSTED_FILE):
        return []
    with open(POSTED_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_posted_games(posted):
    with open(POSTED_FILE, "w") as f:
        json.dump(posted, f, indent=2)

def get_series_game_number(team1, team2, current_game_id):
    finder = leaguegamefinder.LeagueGameFinder(season_type_nullable="Playoffs")
    all_games = finder.get_normalized_dict()["LeagueGameFinderResults"]

    series_games = [
        g for g in all_games
        if current_game_id.startswith(g["GAME_ID"][:8])  # only same playoff year
        and (g["MATCHUP"] == f"{team1} @ {team2}" or g["MATCHUP"] == f"{team2} @ {team1}")
        and g["GAME_ID"] <= current_game_id  # include current or earlier
    ]

    return len(series_games)


def run_bot():
    print("🤖 Running Game Final Score Bot...\n")

    today = datetime.today().strftime('%m/%d/%Y')
    sb = scoreboardv2.ScoreboardV2(game_date=today)
    games = sb.get_normalized_dict()["GameHeader"]

    posted = load_posted_games()
    new_posted = list(posted)

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
        client.create_tweet(text=tweet)
        new_posted.append(game_id)

    save_posted_games(new_posted)
    print("✅ Done.\n")

if __name__ == "__main__":
    run_bot()
