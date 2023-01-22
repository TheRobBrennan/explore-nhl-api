# SOURCE - https://github.com/ztandrews/NHLShotCharts/blob/main/NHLGameShotChart.py

import arrow
import json
import matplotlib.pyplot as plt
import requests

from datetime import datetime as dt
from hockey_rink import NHLRink
from PIL import Image

from matplotlib import image
from matplotlib import cm
from matplotlib.patches import Circle, Rectangle, Arc, ConnectionPatch
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
from matplotlib.path import Path
from matplotlib.patches import PathPatch


# NHL API
NHL_API_BASE_URL = "https://statsapi.web.nhl.com/api/v1"
NHL_API_DATE_TIME_FORMAT_STRING = "%Y-%m-%dT%H:%M:%SZ"  # '2023-01-20T03:00:00Z'

# NHL settings and configuration
NHL_SEASON = 20222023
NHL_TEAM_ID = 55  # Seattle Kraken

NHL_GAME_ID = 2022020728  # 2023.01.19 => NJD @ SEA
# NHL_GAME_ID = 2022020743  # 2023.01.21 => COL @ SEA

# Date and time
START_DATE = "2023-01-19"
END_DATE = "2023-01-21"
LOCAL_DATE_TIME_FORMAT_STRING = "YYYY-MM-DD h:mma"  # '2023-01-19 7:00pm'
OUTPUT_SEPARATOR = "\n\n*****\n\n"


def printJSON(data, indent=0):
    if indent == 0:
        print(OUTPUT_SEPARATOR + data + OUTPUT_SEPARATOR)
    else:
        print(OUTPUT_SEPARATOR + json.dumps(data,
              indent=indent) + OUTPUT_SEPARATOR)


def generate_shot_chart_for_game(gameId):
    content = load_live_data_for_game(gameId)

    game_data = content["gameData"]
    event = content["liveData"]
    date = game_data["datetime"]

    linescore = event["linescore"]
    currentPeriodTimeRemaining = linescore["currentPeriodTimeRemaining"]
    currentPeriodOrdinal = linescore["currentPeriodOrdinal"]

    # Convert '2023-01-20T03:00:00Z' to '2023-01-19 7:00pm'
    datetime = arrow.get(dt.strptime(
        date["dateTime"], NHL_API_DATE_TIME_FORMAT_STRING)).to('local').format(LOCAL_DATE_TIME_FORMAT_STRING)
    teams = game_data["teams"]
    away = teams["away"]
    home = teams["home"]
    away_team = away["abbreviation"]
    home_team = home["abbreviation"]
    print(teams)
    plays = event["plays"]
    all_plays = plays["allPlays"]

    fig = plt.figure(figsize=(10, 10))
    plt.xlim([0, 100])
    plt.ylim([-42.5, 42.5])

    home_shot_attempts = 0
    home_sog = 0
    home_goals = 0
    away_shot_attempts = 0
    away_sog = 0
    away_goals = 0
    for i in all_plays:
        result = i["result"]
        event = result["event"]
        if event == "Goal" or event == "Shot" or event == "Missed Shot":
            team_info = i["team"]
            team = team_info["triCode"]
            if team == home_team:
                home_shot_attempts += 1
                print(team)
                print(event)
                coords = (i["coordinates"])
                print(coords)
                x = int(coords["x"])
                y = int(coords["y"])
                if x < 0:
                    x = abs(x)
                    y = y*-1
                else:
                    x = x
                    y = y
                print(i)
                if event == "Goal":
                    home_goals += 1
                    empty_net = result["emptyNet"]
                    if empty_net != False:
                        continue
                    else:
                        plt.plot(x, y, 'd', color="#4bad53", markersize=20)
                elif event == "Shot":
                    home_sog += 1
                    plt.plot(x, y, 'o', color="#f0a911", markersize=15)
                else:
                    plt.plot(x, y, 'x', color="#000000", markersize=15)
            else:
                away_shot_attempts += 1
                print(team)
                print(event)
                coords = (i["coordinates"])
                print(coords)
                x = int(coords["x"])
                y = int(coords["y"])
                if x > 0:
                    x = -x
                    y = -y
                else:
                    x = x
                    y = y
                print(i)
                if event == "Goal":
                    away_goals += 1
                    empty_net = result["emptyNet"]
                    if empty_net != False:
                        continue
                    else:
                        plt.plot(x, y, 'd', color="#4bad53", markersize=20)
                elif event == "Shot":
                    away_sog += 1
                    plt.plot(x, y, 'o', color="#f0a911", markersize=15)
                else:
                    plt.plot(x, y, 'x', color="#000000", markersize=15)
        else:
            continue

    rink = NHLRink()
    ax = rink.draw()

    # Build our title
    title_line1 = away_team + " (" + str(away_goals) + ")" + \
        " vs. " + home_team + " (" + str(home_goals) + ")" + "\n"
    title_line2 = datetime + "\n"
    title_line3 = currentPeriodTimeRemaining + "/" + currentPeriodOrdinal + "\n\n"
    title_line4 = away_team + ": " + str(away_sog) + " SOG (" + str(away_shot_attempts) + " Total Shot Attempts " + ")\n" + \
        home_team + ": " + str(home_sog) + " SOG (" + \
        str(home_shot_attempts) + " Total Shot Attempts)"
    title = title_line1 + title_line2 + title_line3 + title_line4

    # Add title and display chart
    plt.title(title)

    # OPTIONAL: Save our plot to a PNG file
    plt.savefig('./charts/shot-chart-' + str(gameId) + '-' + datetime.replace(' ', '_') + '-' +
                away_team + '-vs-' + home_team + '.png')

    plt.show()


def load_live_data_for_game(gameId):
    # https://statsapi.web.nhl.com/api/v1/game/2022020728/feed/live
    NHL_API_LIVE_GAME_DATA_URL = NHL_API_BASE_URL + \
        "/game/" + str(gameId) + "/feed/live"
    live_data = requests.get(NHL_API_LIVE_GAME_DATA_URL).json()
    printJSON(live_data, 1)
    return live_data


def load_schedule_for_season_and_team(season, teamId):
    # Build our schedule URL using team information from above
    NHL_API_SCHEDULE_URL = NHL_API_BASE_URL + \
        "/schedule?season=" + str(season) + \
        "&teamId=" + str(teamId)
    kraken_schedule = requests.get(NHL_API_SCHEDULE_URL).json()
    printJSON(kraken_schedule, 1)


def load_schedule_for_team_with_start_and_end_dates(teamId, startDate, endDate, hydrateCSVString=""):
    # https://statsapi.web.nhl.com/api/v1/schedule?startDate=2023-01-19&endDate=2023-01-21&hydrate=team,linescore,metadata,seriesSummary(series)&teamId=55
    # Build our partial schedule URL using team information from above
    NHL_API_PARTIAL_SCHEDULE_URL = NHL_API_BASE_URL + \
        "/schedule?" + \
        "&startDate=" + startDate + \
        "&endDate=" + endDate + \
        "&teamId=" + str(teamId) + \
        "&hydrate=" + hydrateCSVString
    kraken_partial_schedule = requests.get(NHL_API_PARTIAL_SCHEDULE_URL).json()
    printJSON(kraken_partial_schedule, 1)


# ------------------------------------------------------------------------------------------------
# Examples
# ------------------------------------------------------------------------------------------------
# # - Load the Seattle Kraken schedule for the 2022-23 season
# load_schedule_for_season_and_team(NHL_SEASON, NHL_TEAM_ID)
# ------------------------------------------------------------------------------------------------
# # - Load a subset of Seattle Kraken games and hydrate our response with additional details
# hydrateWithCSVString = "team,linescore,metadata,seriesSummary(series)"
# load_schedule_for_team_with_start_and_end_dates(
#     NHL_TEAM_ID, START_DATE, END_DATE, hydrateWithCSVString)
# ------------------------------------------------------------------------------------------------
# Load live data for the game held on 2023.01.19 between the New Jersey Devils and Seattle Kraken
# content = load_live_data_for_game(NHL_GAME_ID)
# ------------------------------------------------------------------------------------------------

# Generate our shot chart (using the original example code as a reference)
generate_shot_chart_for_game(NHL_GAME_ID)
