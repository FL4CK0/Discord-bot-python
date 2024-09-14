from typing import Final
import os
from dotenv import load_dotenv
from discord import Intents, Client, Message
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz


# Load token from .env file
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

#For google cloud declare token in the code
#TOKEN = 'PUT-TOKEN-HERE'

intents: Intents = Intents.default()
intents.message_content = True
client: Client = Client(intents=intents)

def fetch_premier_league_matches() -> str:
    url = 'https://fantasy.premierleague.com/api/fixtures/'
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        fixtures = response.json()
        
        # Get today's date in the format used by the API (YYYY-MM-DD)
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Timezone for Stockholm
        stockholm_tz = pytz.timezone('Europe/Stockholm')
        
        match_list = []
        for fixture in fixtures:
            # The `kickoff_time` contains the date and time of the match
            match_date = fixture['kickoff_time'][:10]  # Extract the date (YYYY-MM-DD)
            
            if match_date == today:
                # Get the kickoff time in UTC and convert it to Stockholm time
                kickoff_time_utc = fixture['kickoff_time']  # UTC time from API
                kickoff_time = datetime.strptime(kickoff_time_utc, '%Y-%m-%dT%H:%M:%SZ')
                
                # Convert to Stockholm time
                kickoff_time_stockholm = kickoff_time.replace(tzinfo=pytz.utc).astimezone(stockholm_tz)
                kickoff_time_formatted = kickoff_time_stockholm.strftime('%H:%M')  # Format as HH:MM
                
                # Get team IDs from the fixture
                home_team_id = fixture['team_h']
                away_team_id = fixture['team_a']
                
                # Fetch team names from the bootstrap-static endpoint
                teams_url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
                teams_response = requests.get(teams_url)
                teams_data = teams_response.json()
                
                # Find the team names based on their IDs
                home_team = next(team['name'] for team in teams_data['teams'] if team['id'] == home_team_id)
                away_team = next(team['name'] for team in teams_data['teams'] if team['id'] == away_team_id)
                
                # Format the match with time, home team, and away team
                match_list.append(f"{kickoff_time_formatted} - {home_team} vs {away_team}")
        
        if not match_list:
            return "No Premier League matches today."
        
        return "\n".join(match_list)
    
    except Exception as e:
        print(f"Error fetching matches: {e}")
        return "Failed to retrieve matches."

async def send_message(message: Message, user_message: str) -> None:
    if user_message.startswith('!matches'):
        response = fetch_premier_league_matches()
        try:
            await message.channel.send(response)
        except Exception as e:
            print(e)

@client.event
async def on_ready() -> None:
    print(f'{client.user} is now running!')

@client.event
async def on_message(message: Message) -> None:
    if message.author == client.user:
        return
    
    user_message: str = message.content

    if user_message.startswith('!matches'):
        await send_message(message, user_message)

def main() -> None:
    client.run(TOKEN)

if __name__ == '__main__':
    main()