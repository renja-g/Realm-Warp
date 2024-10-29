import re
from typing import Dict

platform_to_regions = {
    'br1': 'americas',
    'eun1': 'europe',
    'euw1': 'europe',
    'jp1': 'asia',
    'kr': 'asia',
    'la1': 'americas',
    'la2': 'americas',
    'na1': 'americas',
    'oc1': 'sea',
    'tr1': 'europe',
    'ru': 'europe',
    'ph2': 'sea',
    'sg2': 'sea',
    'th2': 'sea',
    'tw2': 'sea',
    'vn2': 'sea',
}


def platform_to_region(platform: str) -> str:
    """Return the region correspondent to a given platform"""
    return platform_to_regions[platform]


def camel_to_snake(name: str) -> str:
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def convert_keys(dictionary: Dict[str, str]) -> Dict[str, str]:
    """Converts the keys of a dictionary from camelCase to snake_case"""
    new_dict = {}
    for key, value in dictionary.items():
        new_key = camel_to_snake(key)
        if key == 'id':
            new_key = 'summoner_id'
        new_dict[new_key] = value
    return new_dict
