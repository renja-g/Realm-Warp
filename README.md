# Realm-Warp
Realm-Warp is a project designed to track and collect summoner, match, and league data from the Riot API. It aims to enhance this data and store it in a MongoDB database for further use. Additionally, it provides an API for adding and deleting summoners as well as retrieving a list of currently tracked summoners.

## Components
All components are packaged using Docker


### Ratelimiter
A proxy ratelimiter implemnted using Pulsfire that is used by all parts of the porject that interact with the Riot API.

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
   <br>Tipp: to generate a secret key or password run `python -c 'import secrets; print(secrets.token_urlsafe(32))'`

4. Run `docker compose up -d` to start everything.

6. Add summoners that should be tracked using the api `localhost:8000/docs`


## FAQ
<details>
  <summary>FAQ</summary>

  No questions till now...
</details>
