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

# Global settings - Set to False if you do not want to display certain visual elements
SHOW_GOALS = True
SHOW_SHOTS_ON_GOAL = True
SHOW_SHOT_ATTEMPTS = True
SHOW_SHOT_ATTEMPTS_ANNOTATION = False

# Charts and graphs
GOAL_COLOR = "#4bad53"
GOAL_MARKER_SIZE = 20
GOAL_MARKER_TYPE = '*'

SHOT_ON_GOAL_COLOR = "#f0a911"
SHOT_ON_GOAL_MARKER_SIZE = 7
SHOT_ON_GOAL_MARKER_TYPE = 'o'

SHOT_ATTEMPT_COLOR = "#000000"
SHOT_ATTEMPT_MARKER_SIZE = 7
SHOT_ATTEMPT_MARKER_TYPE = 'x'

OUTPUT_SEPARATOR = "\n\n*****\n\n"
OUTPUT_SHOT_CHART_DIRECTORY_AND_FILENAME_PREFIX = './images/shot-chart-'

# Date and time
START_DATE = "2023-01-19"
END_DATE = "2023-01-21"
LOCAL_DATE_TIME_FORMAT_STRING = "YYYY-MM-DD h:mma"  # '2023-01-19 7:00pm'

# NHL API
NHL_API_BASE_URL = "https://statsapi.web.nhl.com/api/v1"
NHL_API_DATE_TIME_FORMAT_STRING = "%Y-%m-%dT%H:%M:%SZ"  # '2023-01-20T03:00:00Z'

# NHL settings and configuration
NHL_SEASON = 20222023
NHL_TEAM_ID_SEATTLE_KRAKEN = 55

# 2023.02.09 => SEA @ NJD - https://www.nhl.com/gamecenter/sea-vs-njd/2023/02/09/2022020824#game=2022020824,game_state=live
NHL_GAME_ID = 2022020824


# Utility method to convert an API datetime string to a local format
def convertToLocalDateTimeString(dateTimeString):
    # Convert '2023-01-20T03:00:00Z' to '2023-01-19 7:00pm'
    return arrow.get(dt.strptime(
        dateTimeString, NHL_API_DATE_TIME_FORMAT_STRING)).to('local').format(LOCAL_DATE_TIME_FORMAT_STRING)


# Utility method to either log or pretty print JSON data
def printJSON(data, indent=0):
    if indent == 0:
        print(OUTPUT_SEPARATOR + data + OUTPUT_SEPARATOR)
    else:
        print(OUTPUT_SEPARATOR + json.dumps(data,
                                            indent=indent) + OUTPUT_SEPARATOR)


# Generate a shot chart for a specific game ID from the NHL API
def generate_shot_chart_for_game(gameId):
    data = parse_game_details(gameId)

    # Title elements
    result = data['game']

    gameStartLocalDateTime = result['gameStart']
    currentPeriodTimeRemaining = result['currentPeriodTimeRemaining']
    currentPeriodOrdinal = result['currentPeriodOrdinal']

    if currentPeriodOrdinal == 'OT' or currentPeriodOrdinal == 'SO':
        gameStatus = currentPeriodTimeRemaining + "/" + currentPeriodOrdinal
    elif currentPeriodTimeRemaining == 'Final':
        gameStatus = currentPeriodTimeRemaining
    else:
        gameStatus = currentPeriodTimeRemaining + \
            " " + currentPeriodOrdinal

    away_team = result['awayTeam']
    away_goals = result['awayGoals']
    away_sog = result['awayShotsOnGoal']
    away_shot_attempts = result['awayShotAttempts']

    home_team = result['homeTeam']
    home_goals = result['homeGoals']
    home_sog = result['homeShotsOnGoal']
    home_shot_attempts = result['homeShotAttempts']

    # Build our title
    title = away_team + " " + \
        str(away_goals) + " vs. " + home_team + \
        " " + str(home_goals) + "\n" + gameStatus
    detail_line = gameStartLocalDateTime + "\n" + away_team + " - " + str(away_sog) + " SOG (" + str(away_shot_attempts) + " Total Shot Attempts) " + \
        " " + home_team + " - " + str(home_sog) + " SOG (" + \
        str(home_shot_attempts) + " Total Shot Attempts)"
    # --------------------------------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------------------------------
    # Define our scatter plot
    # --------------------------------------------------------------------------------------------------------
    fig = plt.figure(figsize=(10, 10))
    plt.xlim([0, 100])
    plt.ylim([-42.5, 42.5])

    # Use a predefined NHL rink with markings to overlay our scatter plot
    rink = NHLRink()
    ax = rink.draw()

    # Log
    eventLog = "-- BEGIN GAME --"

    # Plot our elements on the chart
    elements = data['game']['charts']['shotChart']['data']
    for e in elements:
        eventDescription = e['event_description']
        eventDetails = e['event_details']
        eventLog = "Period {0} - {1} ({2} remaining) -> {4} {3}".format(
            eventDetails['period'], eventDetails['periodTime'], eventDetails['periodTimeRemaining'], eventDescription, e['team'])
        print(eventLog)

        plt.plot(e['x_calculated_shot_chart'], e['y_calculated_shot_chart'], e['markertype'], color=e['color'],
                 markersize=int(e['markersize']))

        if SHOW_SHOT_ATTEMPTS_ANNOTATION:
            plt.text(e['x_calculated_shot_chart']-1.2, e['y_calculated_shot_chart']-1, e['shot_attempts'], horizontalalignment='left',
                     size='medium', color='black', weight='normal')

    # Add title
    plt.title(title)
    # CAPTION
    plt.text(0, -53, detail_line,
             ha='center', fontsize=11, alpha=0.9)

    # OPTIONAL: Save our plot to a PNG file
    saveToFile = OUTPUT_SHOT_CHART_DIRECTORY_AND_FILENAME_PREFIX + str(gameId) + '-' + gameStartLocalDateTime.replace(' ', '_') + '-' + \
        away_team + '-vs-' + home_team + \
        '.png'  # Example - ./images/shot-chart-2022020711-2023-01-17_6:00pm-SEA-vs-EDM.png
    plt.savefig(saveToFile)

    # Display chart
    plt.show()
    # --------------------------------------------------------------------------------------------------------


# Load live data for a specific game ID from the NHL API
def load_live_data_for_game(gameId):
    # https://statsapi.web.nhl.com/api/v1/game/2022020728/feed/live
    NHL_API_LIVE_GAME_DATA_URL = NHL_API_BASE_URL + \
        "/game/" + str(gameId) + "/feed/live"
    live_data = requests.get(NHL_API_LIVE_GAME_DATA_URL).json()
    return live_data


# Load schedule data for a specific season and team ID from the NHL API
def load_schedule_for_season_and_team(season, teamId):
    # Build our schedule URL using team information from above
    NHL_API_SCHEDULE_URL = NHL_API_BASE_URL + \
        "/schedule?season=" + str(season) + \
        "&teamId=" + str(teamId)
    season_schedule = requests.get(NHL_API_SCHEDULE_URL).json()
    printJSON(season_schedule, 1)
    return season_schedule


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
    partial_schedule = requests.get(NHL_API_PARTIAL_SCHEDULE_URL).json()
    printJSON(partial_schedule, 1)
    return partial_schedule


def parse_game_details(gameId):
    # Initialize counters for processing all plays from the game
    home_shot_attempts = 0
    home_sog = 0
    home_goals = 0
    away_shot_attempts = 0
    away_sog = 0
    away_goals = 0

    # --------------------------------------------------------------------------------------------------------
    # Load data for a specific game ID from the NHL API
    # --------------------------------------------------------------------------------------------------------
    content = load_live_data_for_game(gameId)

    # --------------------------------------------------------------------------------------------------------
    # Game details
    # --------------------------------------------------------------------------------------------------------
    # Contains details about the game, status, teams, players, and venue
    game_data = content["gameData"]

    # Contains plays, linescore, box score, and decisions from the game
    eventDescription = content["liveData"]

    # Contains current period information, shootout details if applicable, and more
    linescore = eventDescription["linescore"]
    currentPeriodTimeRemaining = linescore["currentPeriodTimeRemaining"]
    currentPeriodOrdinal = linescore["currentPeriodOrdinal"]

    # Contains the start and end time for the game
    date = game_data["datetime"]
    gameStartLocalDateTime = convertToLocalDateTimeString(date["dateTime"])

    # Team details
    teams = game_data["teams"]
    away = teams["away"]
    home = teams["home"]
    away_team = away["abbreviation"]
    home_team = home["abbreviation"]

    # Build our result dictionary
    response = dict()
    response['game'] = dict()

    # Capture raw data returned from the NHL API
    response['source_data'] = content

    # Build our customized summary object
    gameData = response['game']

    # Game details
    gameData['gameStart'] = gameStartLocalDateTime
    gameData['currentPeriodTimeRemaining'] = currentPeriodTimeRemaining
    gameData['currentPeriodOrdinal'] = currentPeriodOrdinal

    # Charts and graphs
    gameData['charts'] = dict()
    charts = gameData['charts']

    # Shot chart
    charts['shotChart'] = dict()
    shotChart = charts['shotChart']
    shotChart['data'] = []
    chartElements = shotChart['data']

    # --------------------------------------------------------------------------------------------------------
    # Process all event data
    # --------------------------------------------------------------------------------------------------------
    plays = eventDescription["plays"]
    all_plays = plays["allPlays"]

    for event in all_plays:

        result = event["result"]  # Details for the event

        # Description of the event (e.g. Game Scheduled, Goal, Shot, Missed Shot, etc.)
        eventDescription = result["event"]

        if eventDescription == "Goal" or eventDescription == "Shot" or eventDescription == "Missed Shot":
            datapoint = dict()
            eventDetails = event["about"]

            # Which team fired this shot?
            team_info = event["team"]
            team = team_info["triCode"]

            # Let's determine what counters we need to update at the end of our processing
            isHomeTeam = (team == home_team)
            isGoal = False
            isShotAttempt = False
            isShotOnGoal = False

            # Where did this event take place?
            coords = (event["coordinates"])

            # Fix bug where "Shot" event type was received in the data without any coordinates
            if 'x' not in coords:
                continue

            if 'y' not in coords:
                continue

            x = int(coords["x"])
            y = int(coords["y"])

            # For shot charts, we need to adjust the (x,y) location when both teams switch ends
            if isHomeTeam:
                if x < 0:
                    x_calculated_shot_chart = abs(x)
                    y_calculated_shot_chart = y*-1
                else:
                    x_calculated_shot_chart = x
                    y_calculated_shot_chart = y
            else:
                if x > 0:
                    x_calculated_shot_chart = -x
                    y_calculated_shot_chart = -y
                else:
                    x_calculated_shot_chart = x
                    y_calculated_shot_chart = y

            # Is this a goal?
            if eventDescription == "Goal":
                isGoal = True

                try:
                    # Shootout adjustments
                    if event["about"]["periodType"] != 'SHOOTOUT':
                        isShotOnGoal = True
                        # FUTURE - Should isShotAttempt be set to False here? 🤔
                        isShotAttempt = True

                        datapoint['event_description'] = eventDescription
                        datapoint['x'] = x
                        datapoint['y'] = y
                        datapoint['x_calculated_shot_chart'] = x_calculated_shot_chart
                        datapoint['y_calculated_shot_chart'] = y_calculated_shot_chart
                        datapoint['markertype'] = GOAL_MARKER_TYPE
                        datapoint['color'] = GOAL_COLOR
                        datapoint['markersize'] = GOAL_MARKER_SIZE
                        datapoint['event_details'] = eventDetails
                        datapoint['team'] = team

                        if isHomeTeam:
                            datapoint['shot_attempts'] = home_shot_attempts
                        else:
                            datapoint['shot_attempts'] = away_shot_attempts

                        if SHOW_GOALS:
                            chartElements.append(datapoint)

                except:
                    datapoint['event_description'] = eventDescription
                    datapoint['x'] = x
                    datapoint['y'] = y
                    datapoint['x_calculated_shot_chart'] = x_calculated_shot_chart
                    datapoint['y_calculated_shot_chart'] = y_calculated_shot_chart
                    datapoint['markertype'] = GOAL_MARKER_TYPE
                    datapoint['color'] = GOAL_COLOR
                    datapoint['markersize'] = GOAL_MARKER_SIZE
                    datapoint['event_details'] = eventDetails
                    datapoint['team'] = team

                    if isHomeTeam:
                        datapoint['shot_attempts'] = home_shot_attempts
                    else:
                        datapoint['shot_attempts'] = away_shot_attempts

                    if SHOW_GOALS:
                        chartElements.append(datapoint)
            elif eventDescription == "Shot":
                # Is this a shot on goal?
                isShotAttempt = True
                isShotOnGoal = True

                datapoint['event_description'] = eventDescription
                datapoint['x'] = x
                datapoint['y'] = y
                datapoint['x_calculated_shot_chart'] = x_calculated_shot_chart
                datapoint['y_calculated_shot_chart'] = y_calculated_shot_chart
                datapoint['markertype'] = SHOT_ON_GOAL_MARKER_TYPE
                datapoint['color'] = SHOT_ON_GOAL_COLOR
                datapoint['markersize'] = SHOT_ON_GOAL_MARKER_SIZE
                datapoint['event_details'] = eventDetails
                datapoint['team'] = team

                if isHomeTeam:
                    datapoint['shot_attempts'] = home_shot_attempts
                else:
                    datapoint['shot_attempts'] = away_shot_attempts

                if SHOW_SHOTS_ON_GOAL:
                    chartElements.append(datapoint)
            else:
                # Is this a missed shot?
                isShotAttempt = True
                isShotOnGoal = False

                datapoint['event_description'] = eventDescription
                datapoint['x'] = x
                datapoint['y'] = y
                datapoint['x_calculated_shot_chart'] = x_calculated_shot_chart
                datapoint['y_calculated_shot_chart'] = y_calculated_shot_chart
                datapoint['markertype'] = SHOT_ATTEMPT_MARKER_TYPE
                datapoint['color'] = SHOT_ATTEMPT_COLOR
                datapoint['markersize'] = SHOT_ATTEMPT_MARKER_SIZE
                datapoint['event_details'] = eventDetails
                datapoint['team'] = team

                if isHomeTeam:
                    datapoint['shot_attempts'] = home_shot_attempts
                else:
                    datapoint['shot_attempts'] = away_shot_attempts

                if SHOW_SHOT_ATTEMPTS:
                    chartElements.append(datapoint)
        else:
            continue

        # Increment the appropriate counters
        if isHomeTeam:
            if isShotAttempt:
                home_shot_attempts += 1

            if isGoal:
                home_goals += 1

            if isShotOnGoal:
                home_sog += 1
        else:
            if isShotAttempt:
                away_shot_attempts += 1

            if isGoal:
                away_goals += 1

            if isShotOnGoal:
                away_sog += 1

        # Reset our booleans
        isShotAttempt = False
        isShotOnGoal = False
        isGoal = False

    # Add away and home team information to our response
    # Away team stats and information
    gameData['awayTeam'] = away_team
    gameData['awayShotAttempts'] = away_shot_attempts
    gameData['awayShotsOnGoal'] = away_sog
    gameData['awayGoals'] = away_goals

    # Home team stats and information
    gameData['homeTeam'] = home_team
    gameData['homeShotAttempts'] = home_shot_attempts
    gameData['homeShotsOnGoal'] = home_sog
    gameData['homeGoals'] = home_goals

    return response


# ------------------------------------------------------------------------------------------------
# Examples
# ------------------------------------------------------------------------------------------------
# # - Load the Seattle Kraken schedule for the 2022-23 season
# load_schedule_for_season_and_team(NHL_SEASON, NHL_TEAM_ID_SEATTLE_KRAKEN)
# ------------------------------------------------------------------------------------------------
# # - Load a subset of Seattle Kraken games and hydrate our response with additional details
# hydrateWithCSVString = "team,linescore,metadata,seriesSummary(series)"
# load_schedule_for_team_with_start_and_end_dates(
#     NHL_TEAM_ID_SEATTLE_KRAKEN, START_DATE, END_DATE, hydrateWithCSVString)
# ------------------------------------------------------------------------------------------------
# Load live data for the game held on 2023.01.19 between the New Jersey Devils and Seattle Kraken
# content = load_live_data_for_game(NHL_GAME_ID)
# ------------------------------------------------------------------------------------------------


# Generate our shot chart (using the original example code as a reference)
generate_shot_chart_for_game(NHL_GAME_ID)
