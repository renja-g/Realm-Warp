# Realm-Warp
Realm-Warp is a project designed to track and collect summoner, match, and league data from the Riot API. It aims to enhance this data and store it in a MongoDB database for further use. Additionally, it provides an API for adding and deleting summoners, as well as retrieving a list of currently tracked summoners.
By focusing the full API limit on a few summoners, this project is able to provide league information per match.

## Components
All components are packaged using Docker.
![image](https://github.com/renja-g/Realm-Warp/assets/76645494/b0b26cee-cd27-4d18-b846-4a5a3a6aa5f3)


### Ratelimiter
A proxy ratelimiter implemented using Pulsfire that is used by all parts of the project that interact with the Riot API.

### Watcher
The Watcher serves as the core component of Realm-Warp. It tracks summoner information, league data, and match history. Key functionalities include:
- Tracking summoner information
- Tracking league entries
- Tracking match history
- Enhancing match data with league information

## API
The API is fully typed and documented using the OpenAPI specification. Available endpoints include:
- `POST /summoner` - Add a summoner to be tracked (`gameName`, `tagLine`, `platform`)
- `DELETE /summoner/{puuid}` - Delete a tracked summoner by their PUUID
- `GET /summoner` - Get a list of currently tracked summoners
- `GET /summoner/{puuid}` - Get detailed information about a tracked summoner
- `POST /access-token` - Obtain an access token
- `POST /refresh-token` - Refresh an access token


## Installation
1. Clone the repository `git clone https://github.com/renja-g/Realm-Warp`

2. `cd Realm-Warp`

3. Copy the `.env.example` and name it to `.env`. Fill out the .env
   <br>Tip: to generate a secret key or password, run `python -c 'import secrets; print(secrets.token_urlsafe(32))'`

4. Run `docker compose up -d` to start everything.

6. Add summoners that should be tracked using the API `localhost:8000/docs`


## Data schema
Collections:
`summoners`, `league_entries`, `matches`

summoner:
```json
{
  "_id": "6605de2491f4a6ad161486d2",
  "gameName": "Ayato",
  "name": "G5 Easy",
  "platform": "euw1",
  "profileIconId": 5641,
  "puuid": "qAlgGTtahafad2HMEnvMOYJjBteuqrTYjdLMyIEju82VW8-U6Ggwvkk8F8MIgUua0m_ExkzpYwQjVQ",
  "summonerId": "LqtoCvKonkHZI0nUN0FUhJ3aOaGMaU-qy5VpNUfUoUlceUI",
  "summonerLevel": 406,
  "tagLine": "11235"
}
```

league_entry:
```json
{
  "_id": "6605de3af37139da4fa483b5",
  "leagueId": "28fde316-4e41-4efe-8408-984ac7880861",
  "queueType": "RANKED_FLEX_SR",
  "tier": "PLATINUM",
  "rank": "II",
  "summonerId": "LqtoCvKonkHZI0nUN0FUhJ3aOaGMaU-qy5VpNUfUoUlceUI",
  "leaguePoints": 50,
  "wins": 12,
  "losses": 17,
  "hotStreak": false,
  "veteran": false,
  "freshBlood": false,
  "inactive": false,
  "miniSeries": null,
  "ref_summoner": "6605de2491f4a6ad161486d2"
}
```

match:
```json
{
  "_id": "6605de3af37139da4fa483b5",
  "metadata": {},
  "info": {
    "...",
    "participants": [
      {
        "league": {
          "leaguePoints": 50,
          "tier": "PLATINUM",
          "rank": "II",
        }
      },
      {}
    ]
  },
  "ref_summoners": ["6605de2491f4a6ad161486d2"],
}
```
The `league` object is added to ranked matches and filled with the league information of the summoner **after the match**.

## FAQ
<details>
  <summary>FAQ</summary>

  No questions till now...
</details>
