from enum import Enum
from typing import Optional, Union

import pymongo
from beanie import Document
from bson import ObjectId
from pydantic import BaseModel, Field, model_validator


class PlatformEnum(str, Enum):
    EUW1 = 'euw1'
    EUN1 = 'eun1'
    NA1 = 'na1'
    KR = 'kr'
    BR1 = 'br1'
    LA1 = 'la1'
    LA2 = 'la2'
    OC1 = 'oc1'
    TR1 = 'tr1'
    RU = 'ru'
    JP1 = 'jp1'
    PH2 = 'ph2'
    SG2 = 'sg2'
    TH2 = 'th2'
    TW2 = 'tw2'
    VN2 = 'vn2'


class TierEnum(str, Enum):
    IRON = 'IRON'
    BRONZE = 'BRONZE'
    SILVER = 'SILVER'
    GOLD = 'GOLD'
    EMERALD = 'EMERALD'
    PLATINUM = 'PLATINUM'
    DIAMOND = 'DIAMOND'
    MASTER = 'MASTER'
    GRANDMASTER = 'GRANDMASTER'
    CHALLENGER = 'CHALLENGER'


class RankEnum(str, Enum):
    I = 'I'
    II = 'II'
    III = 'III'
    IV = 'IV'


class TimelineEventEnum(str, Enum):
    ASCENDED_EVENT = 'ASCENDED_EVENT'
    BUILDING_KILL = 'BUILDING_KILL'
    CAPTURE_POINT = 'CAPTURE_POINT'
    CHAMPION_KILL = 'CHAMPION_KILL'
    CHAMPION_SPECIAL_KILL = 'CHAMPION_SPECIAL_KILL'
    CHAMPION_TRANSFORM = 'CHAMPION_TRANSFORM'
    DRAGON_SOUL_GIVEN = 'DRAGON_SOUL_GIVEN'
    ELITE_MONSTER_KILL = 'ELITE_MONSTER_KILL'
    GAME_END = 'GAME_END'
    ITEM_DESTROYED = 'ITEM_DESTROYED'
    ITEM_PURCHASED = 'ITEM_PURCHASED'
    ITEM_SOLD = 'ITEM_SOLD'
    ITEM_UNDO = 'ITEM_UNDO'
    LEVEL_UP = 'LEVEL_UP'
    OBJECTIVE_BOUNTY_FINISH = 'OBJECTIVE_BOUNTY_FINISH'
    OBJECTIVE_BOUNTY_PRESTART = 'OBJECTIVE_BOUNTY_PRESTART'
    PAUSE_END = 'PAUSE_END'
    PAUSE_START = 'PAUSE_START'
    SKILL_LEVEL_UP = 'SKILL_LEVEL_UP'
    TURRET_PLATE_DESTROYED = 'TURRET_PLATE_DESTROYED'
    WARD_KILL = 'WARD_KILL'
    WARD_PLACED = 'WARD_PLACED'


class TeamIdEnum(int, Enum):
    BLUE = 100
    RED = 200
    ARENA = 0 # to support arena empty team


class User(Document):
    username: str = Field(..., unique=True)
    hashed_password: str

    class Settings:
        name = 'user'
        indexes = [
            ('username'),
        ]


class Summoner(Document):
    gameName: str
    platform: PlatformEnum
    profileIconId: int
    puuid: str
    summonerId: str
    summonerLevel: int
    tagLine: str

    @model_validator(mode='before')
    def rename_id(cls, values: dict[str, any]) -> dict[str, any]:
        id_value = values.pop('id', None)
        if id_value:
            values['summonerId'] = id_value
        return values

    class Settings:
        name = 'summoners'
        indexes = [
            ('puuid', pymongo.TEXT),
            [
                ('game_name'),
                ('tag_line'),
                ('platform'),
            ],
        ]


class LeagueEntry(Document):
    leagueId: str
    queueType: str
    tier: TierEnum
    rank: RankEnum
    summonerId: str
    leaguePoints: int
    wins: int
    losses: int
    hotStreak: bool
    veteran: bool
    freshBlood: bool
    inactive: bool
    miniSeries: Optional['miniSeriesDTO'] = None
    ref_summoner: ObjectId

    class Settings:
        name = 'leagueEntries'
        indexes = [
            ('ref_summoner'),
        ]

    class Config:
        arbitrary_types_allowed = True


class miniSeriesDTO(BaseModel):
    losses: int
    progress: str
    target: int
    wins: int


class Match(Document):
    metadata: 'MetadataDTO'
    info: 'MatchInfoDTO'
    ref_summoners: list[ObjectId]

    class Settings:
        name = 'matches'
        indexes = [
            ('metadata.matchId'),
            ('ref_summoners'),
        ]

    class Config:
        arbitrary_types_allowed = True


class MetadataDTO(BaseModel):
    dataVersion: str
    matchId: str
    participants: list[str]


class MatchInfoDTO(BaseModel):
    endOfGameResult: Optional[str] = None
    gameCreation: int
    gameDuration: int
    gameEndTimestamp: int
    gameId: int
    gameMode: str
    gameName: str
    gameStartTimestamp: int
    gameType: str
    gameVersion: str
    mapId: int
    participants: list['ParticipantDTO']
    platformId: str
    queueId: int
    teams: list['TeamDTO']
    tournamentCode: str


class ParticipantDTO(BaseModel):
    allInPings: int
    assistMePings: int
    assists: int
    baronKills: int
    basicPings: int
    bountyLevel: int
    challenges: 'ChallengesDTO'
    champExperience: int
    champLevel: int
    championId: int
    championName: str
    championTransform: int
    commandPings: int
    consumablesPurchased: int
    damageDealtToBuildings: int
    damageDealtToObjectives: int
    damageDealtToTurrets: int
    damageSelfMitigated: int
    dangerPings: int
    deaths: int
    detectorWardsPlaced: int
    doubleKills: int
    dragonKills: int
    eligibleForProgression: int
    enemyMissingPings: int
    enemyVisionPings: int
    firstBloodAssist: int
    firstBloodKill: int
    firstTowerAssist: int
    firstTowerKill: int
    gameEndedInEarlySurrender: int
    gameEndedInSurrender: int
    getBackPings: int
    goldEarned: int
    goldSpent: int
    holdPings: int
    individualPosition: str
    inhibitorKills: int
    inhibitorTakedowns: int
    inhibitorsLost: int
    item0: int
    item1: int
    item2: int
    item3: int
    item4: int
    item5: int
    item6: int
    itemsPurchased: int
    killingSprees: int
    kills: int
    lane: str
    largestCriticalStrike: int
    largestKillingSpree: int
    largestMultiKill: int
    longestTimeSpentLiving: int
    magicDamageDealt: int
    magicDamageDealtToChampions: int
    magicDamageTaken: int
    missions: Optional['MissionsDTO'] = None
    needVisionPings: int
    neutralMinionsKilled: int
    nexusKills: int
    nexusLost: int
    nexusTakedowns: int
    objectivesStolen: int
    objectivesStolenAssists: int
    onMyWayPings: int
    participantId: int
    pentaKills: int
    perks: 'PerksDTO'
    physicalDamageDealt: int
    physicalDamageDealtToChampions: int
    physicalDamageTaken: int
    placement: int
    playerAugment1: int
    playerAugment2: int
    playerAugment3: int
    playerAugment4: int
    playerScore0: Optional[int] = None
    playerScore1: Optional[int] = None
    playerScore10: Optional[int] = None
    playerScore11: Optional[int] = None
    playerScore2: Optional[int] = None
    playerScore3: Optional[int] = None
    playerScore4: Optional[int] = None
    playerScore5: Optional[int] = None
    playerScore6: Optional[int] = None
    playerScore7: Optional[int] = None
    playerScore8: Optional[int] = None
    playerScore9: Optional[int] = None
    playerSubteamId: int
    profileIcon: int
    pushPings: int
    puuid: str
    quadraKills: int
    league: Optional['MacthLeagueDTO'] = None
    riotIdGameName: str
    riotIdTagline: str
    role: str
    sightWardsBoughtInGame: int
    spell1Casts: int
    spell2Casts: int
    spell3Casts: int
    spell4Casts: int
    subteamPlacement: int
    summoner1Casts: int
    summoner1Id: int
    summoner2Casts: int
    summoner2Id: int
    summonerId: str
    summonerLevel: int
    summonerName: str
    teamEarlySurrendered: int
    teamId: TeamIdEnum
    teamPosition: str
    timeCCingOthers: int
    timePlayed: int
    totalAllyJungleMinionsKilled: int
    totalDamageDealt: int
    totalDamageDealtToChampions: int
    totalDamageShieldedOnTeammates: int
    totalDamageTaken: int
    totalEnemyJungleMinionsKilled: int
    totalHeal: int
    totalHealsOnTeammates: int
    totalMinionsKilled: int
    totalTimeCCDealt: int
    totalTimeSpentDead: int
    totalUnitsHealed: int
    tripleKills: int
    trueDamageDealt: int
    trueDamageDealtToChampions: int
    trueDamageTaken: int
    turretKills: int
    turretTakedowns: int
    turretsLost: int
    unrealKills: int
    visionClearedPings: int
    visionScore: int
    visionWardsBoughtInGame: int
    wardsKilled: int
    wardsPlaced: int
    win: int


class MacthLeagueDTO(BaseModel):
    leaguePoints: int
    rank: str
    tier: str


class ChallengesDTO(BaseModel):
    def __init__(self, **data):
        super().__init__(**data)

        incoming_keys = set(data.keys())
        incoming_keys.discard('12AssistStreakCount')
        model_keys = set(self.model_fields.keys())

        extra_keys = incoming_keys - model_keys
        if extra_keys:
            print('-------- Extra keys --------')
            for key in extra_keys:
                print(key, data[key])
            print('----------------------------')

    abilityUses: Optional[int] = None
    acesBefore15Minutes: Optional[int] = None
    alliedJungleMonsterKills: Optional[int] = None
    baronBuffGoldAdvantageOverThreshold: Optional[int] = None
    baronTakedowns: Optional[int] = None
    blastConeOppositeOpponentCount: Optional[int] = None
    bountyGold: Optional[int] = None
    buffsStolen: Optional[int] = None
    completeSupportQuestInTime: Optional[int] = None
    controlWardsPlaced: Optional[int] = None
    controlWardTimeCoverageInRiverOrEnemyHalf: Optional[float] = None
    damagePerMinute: Optional[float] = None
    damageTakenOnTeamPercentage: Optional[float] = None
    dancedWithRiftHerald: Optional[int] = None
    deathsByEnemyChamps: Optional[int] = None
    dodgeSkillShotsSmallWindow: Optional[int] = None
    doubleAces: Optional[int] = None
    dragonTakedowns: Optional[int] = None
    earliestBaron: Optional[float] = None
    earliestDragonTakedown: Optional[float] = None
    earliestElderDragon: Optional[float] = None
    earlyLaningPhaseGoldExpAdvantage: Optional[int] = None
    effectiveHealAndShielding: Optional[float] = None
    elderDragonKillsWithOpposingSoul: Optional[int] = None
    elderDragonMultikills: Optional[int] = None
    enemyChampionImmobilizations: Optional[int] = None
    enemyJungleMonsterKills: Optional[int] = None
    epicMonsterKillsNearEnemyJungler: Optional[int] = None
    epicMonsterKillsWithin30SecondsOfSpawn: Optional[int] = None
    epicMonsterSteals: Optional[int] = None
    epicMonsterStolenWithoutSmite: Optional[int] = None
    fasterSupportQuestCompletion: Optional[int] = None
    fastestLegendary: Optional[float] = None
    firstTurretKilled: Optional[int] = None
    firstTurretKilledTime: Optional[float] = None
    fistBumpParticipation: Optional[int] = None
    flawlessAces: Optional[int] = None
    fullTeamTakedown: Optional[int] = None
    gameLength: Optional[float] = None
    getTakedownsInAllLanesEarlyJungleAsLaner: Optional[int] = None
    goldPerMinute: Optional[float] = None
    hadAfkTeammate: Optional[int] = None
    hadOpenNexus: Optional[int] = None
    highestChampionDamage: Optional[int] = None
    highestCrowdControlScore: Optional[int] = None
    highestWardKills: Optional[int] = None
    immobilizeAndKillWithAlly: Optional[int] = None
    InfernalScalePickup : Optional[int] = None
    initialBuffCount: Optional[int] = None
    initialCrabCount: Optional[int] = None
    jungleCsBefore10Minutes: Optional[float] = None
    junglerKillsEarlyJungle: Optional[int] = None
    junglerTakedownsNearDamagedEpicMonster: Optional[int] = None
    kda: Optional[float] = None
    killAfterHiddenWithAlly: Optional[int] = None
    killedChampTookFullTeamDamageSurvived: Optional[int] = None
    killingSprees: Optional[int] = None
    killParticipation: Optional[float] = None
    killsNearEnemyTurret: Optional[int] = None
    killsOnLanersEarlyJungleAsJungler: Optional[int] = None
    killsOnOtherLanesEarlyJungleAsLaner: Optional[int] = None
    killsOnRecentlyHealedByAramPack: Optional[int] = None
    killsUnderOwnTurret: Optional[int] = None
    killsWithHelpFromEpicMonster: Optional[int] = None
    knockEnemyIntoTeamAndKill: Optional[int] = None
    kTurretsDestroyedBeforePlatesFall: Optional[int] = None
    landSkillShotsEarlyGame: Optional[int] = None
    laneMinionsFirst10Minutes: Optional[int] = None
    laningPhaseGoldExpAdvantage: Optional[int] = None
    legendaryCount: Optional[int] = None
    legendaryItemUsed: Optional[list[int]]
    lostAnInhibitor: Optional[int] = None
    maxCsAdvantageOnLaneOpponent: Optional[float] = None
    maxKillDeficit: Optional[int] = None
    maxLevelLeadLaneOpponent: Optional[int] = None
    mejaisFullStackInTime: Optional[int] = None
    moreEnemyJungleThanOpponent: Optional[float] = None
    multiKillOneSpell: Optional[int] = None
    multikills: Optional[int] = None
    multikillsAfterAggressiveFlash: Optional[int] = None
    multiTurretRiftHeraldCount: Optional[int] = None
    outerTurretExecutesBefore10Minutes: Optional[int] = None
    outnumberedKills: Optional[int] = None
    outnumberedNexusKill: Optional[int] = None
    perfectDragonSoulsTaken: Optional[int] = None
    perfectGame: Optional[int] = None
    pickKillWithAlly: Optional[int] = None
    playedChampSelectPosition: Optional[int] = None
    poroExplosions: Optional[int] = None
    quickCleanse: Optional[int] = None
    quickFirstTurret: Optional[int] = None
    quickSoloKills: Optional[int] = None
    riftHeraldTakedowns: Optional[int] = None
    saveAllyFromDeath: Optional[int] = None
    scuttleCrabKills: Optional[int] = None
    shortestTimeToAceFromFirstTakedown: Optional[float] = None
    skillshotsDodged: Optional[int] = None
    skillshotsHit: Optional[int] = None
    snowballsHit: Optional[int] = None
    soloBaronKills: Optional[int] = None
    soloKills: Optional[int] = None
    soloTurretsLategame: Optional[int] = None
    stealthWardsPlaced: Optional[int] = None
    survivedSingleDigitHpCount: Optional[int] = None
    survivedThreeImmobilizesInFight: Optional[int] = None
    takedownOnFirstTurret: Optional[int] = None
    takedowns: Optional[int] = None
    takedownsAfterGainingLevelAdvantage: Optional[int] = None
    takedownsBeforeJungleMinionSpawn: Optional[int] = None
    takedownsFirstXMinutes: Optional[int] = None
    takedownsInAlcove: Optional[int] = None
    takedownsInEnemyFountain: Optional[int] = None
    teamBaronKills: Optional[int] = None
    teamDamagePercentage: Optional[float] = None
    teamElderDragonKills: Optional[int] = None
    teamRiftHeraldKills: Optional[int] = None
    teleportTakedowns: Optional[int] = None
    thirdInhibitorDestroyedTime: Optional[float] = None
    tookLargeDamageSurvived: Optional[int] = None
    turretPlatesTaken: Optional[int] = None
    turretsTakenWithRiftHerald: Optional[int] = None
    turretTakedowns: Optional[int] = None
    twelveAssistStreakCount: Optional[int] = Field(alias='12AssistStreakCount', default=None)
    twentyMinionsIn3SecondsCount: Optional[int] = None
    twoWardsOneSweeperCount: Optional[int] = None
    unseenRecalls: Optional[int] = None
    visionScoreAdvantageLaneOpponent: Optional[float] = None
    visionScorePerMinute: Optional[float] = None
    voidMonsterKill: Optional[int] = None
    wardsGuarded: Optional[int] = None
    wardTakedowns: Optional[int] = None
    wardTakedownsBefore20M: Optional[int] = None

    class Config:
        extra = 'allow'


class MissionsDTO(BaseModel):
    playerScore0: int
    playerScore1: int
    playerScore10: int
    playerScore11: int
    playerScore2: int
    playerScore3: int
    playerScore4: int
    playerScore5: int
    playerScore6: int
    playerScore7: int
    playerScore8: int
    playerScore9: int

    @model_validator(mode='before')
    def validate_keys(cls, values: dict[str, any]) -> dict[str, any]:
        new_values = {}
        for key, value in values.items():
            if key.startswith('PlayerScore'):
                new_values[key.replace('PlayerScore', 'playerScore')] = value
            else:
                new_values[key] = value
        return new_values


class PerksDTO(BaseModel):
    statPerks: 'StatPerksDTO'
    styles: list['StyleDTO']


class StatPerksDTO(BaseModel):
    defense: int
    flex: int
    offense: int


class StyleDTO(BaseModel):
    description: str
    selections: list['SelectionDTO']
    style: int


class SelectionDTO(BaseModel):
    perk: int
    var1: int
    var2: int
    var3: int


class TeamDTO(BaseModel):
    bans: list['BannedChampionDTO']
    objectives: 'ObjectivesDTO'
    teamId: TeamIdEnum
    win: bool


class BannedChampionDTO(BaseModel):
    championId: int
    pickTurn: int


class ObjectivesDTO(BaseModel):
    baron: 'ObjectiveDTO'
    champion: 'ObjectiveDTO'
    dragon: 'ObjectiveDTO'
    horde: 'ObjectiveDTO'
    inhibitor: 'ObjectiveDTO'
    riftHerald: 'ObjectiveDTO'
    tower: 'ObjectiveDTO'


class ObjectiveDTO(BaseModel):
    first: bool
    kills: int


class Timeline(Document):
    metadata: 'MetadataDTO'
    info: 'TimelineInfoDTO'
    ref_match: ObjectId

    class Settings:
        name = 'timelines'
        indexes = [
            ('ref_match'),
        ]

    class Config:
        arbitrary_types_allowed = True


class TimelineInfoDTO(BaseModel):
    endOfGameResult: str
    frameInterval: int
    frames: list['FrameDTO']
    gameId: int
    participants: list['TimelineParticipantDTO']


class FrameDTO(BaseModel):
    events: list[
        Union[
            'AscendedEvent',
            'BuildingKill',
            'CapturePoint',
            'ChampionKill',
            'ChampionSpecialKill',
            'ChampionTransform',
            'DragonSoulGiven',
            'EliteMonsterKill',
            'GameEnd',
            'ItemDestroyed',
            'ItemPurchased',
            'ItemSold',
            'ItemUndo',
            'LevelUp',
            'ObjectiveBountyPrestart',
            'PauseEnd',
            'PauseStart',
            'SkillLevelUp',
            'TurretPlateDestroyed',
            'WardKill',
            'WardPlaced',
        ]
    ]
    participantFrames: dict[str, 'ParticipantFrameDTO']
    timestamp: int


class VictimDamageDealtDTO(BaseModel):
    basic: bool
    magicDamage: int
    name: str
    participantId: int
    physicalDamage: int
    spellName: str
    spellSlot: int
    trueDamage: int
    type: str


class ParticipantFrameDTO(BaseModel):
    championStats: 'ChampionStatsDTO'
    currentGold: int
    damageStats: 'DamageStatsDTO'
    goldPerSecond: int
    jungleMinionsKilled: int
    level: int
    minionsKilled: int
    participantId: int
    position: 'PositionDTO'
    timeEnemySpentControlled: int
    totalGold: int
    xp: int


class ChampionStatsDTO(BaseModel):
    abilityHaste: int
    abilityPower: int
    armor: int
    armorPen: int
    armorPenPercent: int
    attackDamage: int
    attackSpeed: int
    bonusArmorPenPercent: int
    bonusMagicPenPercent: int
    ccReduction: int
    cooldownReduction: int
    health: int
    healthMax: int
    healthRegen: int
    lifesteal: int
    magicPen: int
    magicPenPercent: int
    magicResist: int
    movementSpeed: int
    omnivamp: int
    physicalVamp: int
    power: int
    powerMax: int
    powerRegen: int
    spellVamp: int


class DamageStatsDTO(BaseModel):
    magicDamageDone: int
    magicDamageDoneToChampions: int
    magicDamageTaken: int
    physicalDamageDone: int
    physicalDamageDoneToChampions: int
    physicalDamageTaken: int
    totalDamageDone: int
    totalDamageDoneToChampions: int
    totalDamageTaken: int
    trueDamageDone: int
    trueDamageDoneToChampions: int
    trueDamageTaken: int


class PositionDTO(BaseModel):
    x: int
    y: int


class TimelineParticipantDTO(BaseModel):
    participantId: int
    puuid: str


class BaseEvent(BaseModel):
    type: TimelineEventEnum
    timestamp: int


class AscendedEvent(BaseEvent):
    pass  # TODO


class BuildingKill(BaseEvent):
    assistingParticipantIds: list[int]
    bounty: int
    buildingType: str
    killerId: int
    laneType: str
    position: PositionDTO
    teamId: TeamIdEnum
    towerType: str


class CapturePoint(BaseEvent):
    assistingParticipantIds: list[int]
    bounty: int
    killStreakLength: int
    killerId: int
    position: PositionDTO
    shutdownBounty: int
    victimDamageDealt: list[VictimDamageDealtDTO]
    victimDamageReceived: list[VictimDamageDealtDTO]
    victimId: int


class ChampionKill(BaseEvent):
    killType: str
    killerId: int
    position: PositionDTO


class ChampionSpecialKill(BaseEvent):
    killType: str
    killerId: int
    position: PositionDTO


class ChampionTransform(BaseEvent):
    participantId: int
    transformType: str


class DragonSoulGiven(BaseEvent):
    name: str
    teamId: TeamIdEnum


class EliteMonsterKill(BaseEvent):
    assistingParticipantIds: list[int]
    bounty: int
    killerId: int
    killerTeamId: TeamIdEnum
    monsterType: str
    position: PositionDTO


class GameEnd(BaseEvent):
    gameId: int
    realTimestamp: int
    winningTeam: int


class ItemDestroyed(BaseEvent):
    itemId: int
    participantId: int


class ItemPurchased(BaseEvent):
    itemId: int
    participantId: int


class ItemSold(BaseEvent):
    itemId: int
    participantId: int


class ItemUndo(BaseEvent):
    afterId: int
    beforeId: int
    goldGain: int
    participantId: int


class LevelUp(BaseEvent):
    level: int
    participantId: int


class ObjectiveBountyPrestart(BaseEvent):
    actualStartTime: int
    teamId: TeamIdEnum


class PauseEnd(BaseEvent):
    realTimestamp: int


class PauseStart(BaseEvent):
    realTimestamp: int


class SkillLevelUp(BaseEvent):
    levelUpType: str
    participantId: int
    skillSlot: int


class TurretPlateDestroyed(BaseEvent):
    killerId: int
    laneType: str
    position: PositionDTO
    teamId: TeamIdEnum


class WardKill(BaseEvent):
    killerId: int
    wardType: str


class WardPlaced(BaseEvent):
    creatorId: int
    wardType: int


__all_models__ = [
    User,
    Summoner,
    LeagueEntry,
    Match,
    Timeline,
]
