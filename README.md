# Realm-Warp
Is a project, that aims to track and collect summoner, match and league data.
And make enhancements to it. Everything will be saved in a MongoDB Database ready to be used.
This project also provides a small API to add and delete summoners that are being tracked as well as getting a list of currently tracked summoners.

## Components

### Ratelimiter
A proxy ratelimiter implemnted using Pulsfire that is used by all parts of the porject that interact with the Riot API.

### Watcher
The Watcher is the core of this project. It tracks all summoner info league data and matches played.
- Track summoner info
- Track league entries
- Track match history
- Enhance watcher match data with league data

## API
The API is fully typed and documented using the OpenAPI specification.
- POST /summoner (`gameName`, `tagLine`, `platform`)
- DELTE /summoner{`puuid`}
- GET /summoner /summoner/{`puuid`}
- POST /access-token /refresh-token
