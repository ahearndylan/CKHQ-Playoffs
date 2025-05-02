import tweepy
from nba_api.stats.endpoints import leaguegamefinder, boxscoretraditionalv2
from datetime import datetime, timedelta
import json
import os
import time

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

POSTED_FILE = "posted_series.json"

# ======================= #
#    LOAD/SAVE HELPERS    #
# ======================= #

def load_posted_series():
    if not os.path.exists(POSTED_FILE):
        return []
    with open(POSTED_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_posted_series(posted):
    with open(POSTED_FILE, "w") as f:
        json.dump(posted, f, indent=2)

# ======================= #
#     MAIN BOT LOGIC      #
# ======================= #

def get_recent_playoff_games(days_back=14):  # ✅ increased from 7 to 14
    today = datetime.today()
    start_date = (today - timedelta(days=days_back)).strftime("%m/%d/%Y")

    print(f"\n📅 Checking playoff games from the last {days_back} days (since {start_date})...\n")

    gamefinder = leaguegamefinder.LeagueGameFinder(
        season_type_nullable="Playoffs",
        date_from_nullable=start_date
    )

    games = gamefinder.get_normalized_dict()["LeagueGameFinderResults"]

    return games

def track_series(games):
    series = {}

    for game in games:
        team = game["TEAM_ABBREVIATION"]
        matchup = game["MATCHUP"]
        result = game["WL"]

        opponents = matchup.replace("@", "vs.").split("vs.")
        team1 = opponents[0].strip()
        team2 = opponents[1].strip()
        matchup_key = f"{team1} vs {team2}" if team1 < team2 else f"{team2} vs {team1}"

        if matchup_key not in series:
            series[matchup_key] = {"teams": (team1, team2), "games": [], team1: 0, team2: 0}

        if result == "W":
            series[matchup_key][team] += 1

        # Save game ID for later boxscore pulling
        series[matchup_key]["games"].append(game["GAME_ID"])

    return series

def calculate_series_leaders(game_ids):
    player_stats = {}

    for game_id in game_ids:
        try:
            time.sleep(0.5)  # Be nice to NBA API
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
    tweet = f"""🏆 {team_name} defeat {opponent} {winner_wins}-{loser_wins} to advance! 👑

🔥 Scoring King: {top_players['scoring']['name']} – {top_players['scoring']['stat']} PPG
💪 Rebounding Beast: {top_players['rebounding']['name']} – {top_players['rebounding']['stat']} RPG
🎯 Assist Maestro: {top_players['assists']['name']} – {top_players['assists']['stat']} APG
🛡️ Defensive Anchor: {top_players['defense']['name']} – {top_players['defense']['stat']} STL+BLK

#NBAPlayoffs #CourtKingsHQ"""
    return tweet


# ======================= #
#         MAIN RUN        #
# ======================= #

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

        print(f"🧮 {matchup_key} — {team1} {team1_wins} vs {team2} {team2_wins}")

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
        winner_wins = info[winner]
        loser_wins = info[loser]
        tweet = compose_tweet(winner, loser, top_players, winner_wins, loser_wins)

        print("\n📝 Final tweet to post:\n")
        print(tweet + "\n")

        client.create_tweet(text=tweet)

        posted.append(matchup_key)
        save_posted_series(posted)


if __name__ == "__main__":
    run_bot()
