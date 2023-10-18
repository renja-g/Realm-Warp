import os
import logging

from pyot.conf.model import activate_model, ModelConf
from pyot.conf.pipeline import activate_pipeline, PipelineConf
from pyot.utils.logging import LazyLogger

from dotenv import load_dotenv


# Load env variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))
RIOT_API_KEY = os.getenv('RIOT_API_KEY')


@activate_model('lol')
class LolModel(ModelConf):
    default_platform = 'euw1'
    default_region = 'europe'
    default_version = 'latest'
    default_locale = 'en_us'


@activate_pipeline('lol')
class LolPipeline(PipelineConf):
    name = 'lol_main'
    default = True
    stores = [
        {
            'backend': 'pyot.stores.riotapi.RiotAPI',
            'api_key': os.environ['RIOT_API_KEY'],
        }
    ]