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
NHL_TEAM_ID_SEATTLE_KRAKEN = 55

# Known issue where home shots on goal do not match expected 33 shots (from NHL link below)
NHL_GAME_ID = 2022020711  # 2023.01.17 => SEA @ EDM - https://www.nhl.com/gamecenter/sea-vs-edm/2023/01/17/2022020711#game=2022020711,game_state=final,lock_state=final,game_tab=stats
# Expected 31 SOG for SEA / 33 SOG for EDM; actual data from the NHL API shows 31 SOG for SEA / 34 SOG for EDM

# NHL_GAME_ID = 2022020728  # 2023.01.19 => NJD @ SEA - https://www.nhl.com/gamecenter/njd-vs-sea/2023/01/19/2022020728/recap/stats#game=2022020728,game_state=final,lock_state=final,game_tab=stats
# Expected 30 SOG for NJD / 40 SOG for SEA

# NHL_GAME_ID = 2022020743  # 2023.01.21 => COL @ SEA - https://www.nhl.com/gamecenter/col-vs-sea/2023/01/21/2022020743/recap/stats#game=2022020743,game_state=final,lock_state=final,game_tab=stats
# Expected 27 SOG for COL / 27 SOG for SEA

# Date and time
START_DATE = "2023-01-19"
END_DATE = "2023-01-21"
LOCAL_DATE_TIME_FORMAT_STRING = "YYYY-MM-DD h:mma"  # '2023-01-19 7:00pm'
OUTPUT_SEPARATOR = "\n\n*****\n\n"
OUTPUT_SHOT_CHART_DIRECTORY_AND_FILENAME_PREFIX = './images/shot-chart-'


# Utility method to either log or pretty print JSON data
def printJSON(data, indent=0):
    if indent == 0:
        print(OUTPUT_SEPARATOR + data + OUTPUT_SEPARATOR)
    else:
        print(OUTPUT_SEPARATOR + json.dumps(data,
                                            indent=indent) + OUTPUT_SEPARATOR)


# Generate a shot chart for a specific game ID from the NHL API
def generate_shot_chart_for_game(gameId):
    # --------------------------------------------------------------------------------------------------------
    # TODO - Write a function that parses content and returns values for generating a shot chart
    # --------------------------------------------------------------------------------------------------------
    # What might this look like - starting from a single NHL game ID?
    #
    # - Parse game information and plays
    #
    #   - Return objects to plot on our graph
    #       - Goal - plt.plot(x, y, 'd', color="#4bad53", markersize=20)
    #       - Shot on goal - plt.plot(x, y, 'o', color="#f0a911", markersize=15)
    #       - Shot attempt (missed or blocked) - plt.plot(x, y, 'x', color="#000000", markersize=15)
    #
    #   - Return details to display on our chart which may include
    #       - Away team
    #       - Away shot attempts
    #       - Away shots on goal
    #       - Away goals
    #       - Home team
    #       - Home shot attempts
    #       - Home shots on goal
    #       - Home goals
    #       - Local date and time for the game start
    #       - Current period time remaining
    #       - Current period ordinal (3rd, OT, SO)
    #
    # - What might our chart drawing function look like?
    #   - Define the initial scatter plot
    #   - Define title(s) for the chart
    #   - Process the objects for plotting and draw them on our graph
    #   - Overlay the NHL rink
    # --------------------------------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------------------------------
    # Load data for a specific game ID from the NHL API
    # --------------------------------------------------------------------------------------------------------
    content = load_live_data_for_game(gameId)

    # Contains details about the game, status, teams, players, and venue
    game_data = content["gameData"]

    # Contains plays, linescore, box score, and decisions from the game
    eventDescription = content["liveData"]
    # --------------------------------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------------------------------
    # Contains current period information, shootout details if applicable, and more
    linescore = eventDescription["linescore"]

    # Use the linescore object to determine
    # - If the game is complete
    currentPeriodTimeRemaining = linescore["currentPeriodTimeRemaining"]
    # - The current period, or Final / OT where applicable
    currentPeriodOrdinal = linescore["currentPeriodOrdinal"]
    # --------------------------------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------------------------------
    # Contains the start and end time for the game
    date = game_data["datetime"]
    # --------------------------------------------------------------------------------------------------------
    # Convert '2023-01-20T03:00:00Z' to '2023-01-19 7:00pm'
    # TODO - Write a function to convert the NHL API date time format to our local date time format
    gameStartLocalDateTime = arrow.get(dt.strptime(
        date["dateTime"], NHL_API_DATE_TIME_FORMAT_STRING)).to('local').format(LOCAL_DATE_TIME_FORMAT_STRING)
    # --------------------------------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------------------------------
    # Team details
    # --------------------------------------------------------------------------------------------------------
    teams = game_data["teams"]
    away = teams["away"]
    home = teams["home"]
    away_team = away["abbreviation"]
    home_team = home["abbreviation"]
    print(teams)
    # --------------------------------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------------------------------
    # Plays
    # --------------------------------------------------------------------------------------------------------
    plays = eventDescription["plays"]
    all_plays = plays["allPlays"]
    # --------------------------------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------------------------------
    # Initialize counters for processing all plays from the game
    # --------------------------------------------------------------------------------------------------------
    home_shot_attempts = 0
    home_sog = 0
    home_goals = 0
    away_shot_attempts = 0
    away_sog = 0
    away_goals = 0

    # Define our scatter plot
    fig = plt.figure(figsize=(10, 10))
    plt.xlim([0, 100])
    plt.ylim([-42.5, 42.5])
    # --------------------------------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------------------------------
    # Process all event data
    # --------------------------------------------------------------------------------------------------------
    for event in all_plays:

        # --------------------------------------------------------------------------------------------------------
        # TODO - Parse event details
        # --------------------------------------------------------------------------------------------------------
        result = event["result"]  # Details for the event

        # Description of the event (e.g. Game Scheduled, Goal, Shot, Missed Shot, etc.)
        eventDescription = result["event"]

        if eventDescription == "Goal" or eventDescription == "Shot" or eventDescription == "Missed Shot":
            team_info = event["team"]
            team = team_info["triCode"]
            if team == home_team:
                home_shot_attempts += 1
                print(team)
                print(eventDescription)
                coords = (event["coordinates"])
                print(coords)
                x = int(coords["x"])
                y = int(coords["y"])
                if x < 0:
                    x = abs(x)
                    y = y*-1
                else:
                    x = x
                    y = y
                print(event)
                if eventDescription == "Goal":
                    try:
                        print(event["about"]["periodType"])
                        if event["about"]["periodType"] != 'SHOOTOUT':
                            home_sog += 1

                        home_goals += 1
                        empty_net = result["emptyNet"]
                        if empty_net != False:
                            continue
                        else:
                            plt.plot(x, y, 'd', color="#4bad53", markersize=20)
                    except:
                        plt.plot(x, y, 'd', color="#4bad53", markersize=20)
                elif eventDescription == "Shot":
                    home_sog += 1
                    plt.plot(x, y, 'o', color="#f0a911", markersize=15)
                else:
                    plt.plot(x, y, 'x', color="#000000", markersize=15)
            else:
                away_shot_attempts += 1
                print(team)
                print(eventDescription)
                coords = (event["coordinates"])
                print(coords)
                x = int(coords["x"])
                y = int(coords["y"])
                if x > 0:
                    x = -x
                    y = -y
                else:
                    x = x
                    y = y
                print(event)
                if eventDescription == "Goal":
                    try:
                        print(event["about"]["periodType"])
                        if event["about"]["periodType"] != 'SHOOTOUT':
                            away_sog += 1

                        away_goals += 1
                        empty_net = result["emptyNet"]
                        if empty_net != False:
                            continue
                        else:
                            plt.plot(x, y, 'd', color="#4bad53", markersize=20)
                    except:
                        plt.plot(x, y, 'd', color="#4bad53", markersize=20)
                elif eventDescription == "Shot":
                    away_sog += 1
                    plt.plot(x, y, 'o', color="#f0a911", markersize=15)
                else:
                    plt.plot(x, y, 'x', color="#000000", markersize=15)
        else:
            continue
        # --------------------------------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------------------------------
    # Use a predefined NHL rink with markings to overlay our scatter plot
    rink = NHLRink()
    ax = rink.draw()

    # --------------------------------------------------------------------------------------------------------
    # TODO: Generate a title for our shot chart
    # --------------------------------------------------------------------------------------------------------
    # Build our title
    title_line1 = away_team + " (" + str(away_goals) + ")" + \
        " vs. " + home_team + " (" + str(home_goals) + ")" + "\n"
    title_line2 = gameStartLocalDateTime + "\n"
    title_line3 = currentPeriodTimeRemaining + "/" + currentPeriodOrdinal + "\n\n"
    title_line4 = away_team + ": " + str(away_sog) + " SOG (" + str(away_shot_attempts) + " Total Shot Attempts)\n" + \
        home_team + ": " + str(home_sog) + " SOG (" + \
        str(home_shot_attempts) + " Total Shot Attempts)"
    title = title_line1 + title_line2 + title_line3 + title_line4
    # --------------------------------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------------------------------
    # TODO: Add the title, save our chart as a PNG, and display it to the user
    # --------------------------------------------------------------------------------------------------------
    # Add title
    plt.title(title)

    # OPTIONAL: Save our plot to a PNG file
    plt.savefig(OUTPUT_SHOT_CHART_DIRECTORY_AND_FILENAME_PREFIX + str(gameId) + '-' + gameStartLocalDateTime.replace(' ', '_') + '-' +
                away_team + '-vs-' + home_team + '.png')  # Example - ./images/shot-chart-2022020711-2023-01-17_6:00pm-SEA-vs-EDM.png

    # Display chart
    plt.show()
    # --------------------------------------------------------------------------------------------------------


# Load live data for a specific game ID from the NHL API
def load_live_data_for_game(gameId):
    # https://statsapi.web.nhl.com/api/v1/game/2022020728/feed/live
    NHL_API_LIVE_GAME_DATA_URL = NHL_API_BASE_URL + \
        "/game/" + str(gameId) + "/feed/live"
    live_data = requests.get(NHL_API_LIVE_GAME_DATA_URL).json()
    printJSON(live_data, 1)
    return live_data


# Load schedule data for a specific season and team ID from the NHL API
def load_schedule_for_season_and_team(season, teamId):
    # Build our schedule URL using team information from above
    NHL_API_SCHEDULE_URL = NHL_API_BASE_URL + \
        "/schedule?season=" + str(season) + \
        "&teamId=" + str(teamId)
    kraken_schedule = requests.get(NHL_API_SCHEDULE_URL).json()
    printJSON(kraken_schedule, 1)


# Load schedule data using a specified start and end date for a specific team ID with an optional hydrate CSV string from the NHL API
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
