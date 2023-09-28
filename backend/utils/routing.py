platform2regions = {
    "br1": "americas",
    "eun1": "europe",
    "euw1": "europe",
    "jp1": "asia",
    "kr": "asia",
    "la1": "americas",
    "la2": "americas",
    "na1": "americas",
    "oc1": "sea",
    "tr1": "europe",
    "ru": "europe",
    "ph2": "sea",
    "sg2": "sea",
    "th2": "sea",
    "tw2": "sea",
    "vn2": "sea",
}

queueId2queueType = {
    440: 'RANKED_FLEX_SR',
    420: 'RANKED_SOLO_5x5',
    # TODO: Add more queue types
}


def platform_to_region(platform: str) -> str:
    '''Return the region correspondent to a given platform'''
    return platform2regions[platform]


def queueId_to_queueType(queueId: int) -> str:
    '''Return the queueType correspondent to a given queueId'''
    return queueId2queueType[queueId]
