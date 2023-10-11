import os
import logging

from pyot.conf.model import activate_model, ModelConf
from pyot.conf.pipeline import activate_pipeline, PipelineConf
from pyot.utils.logging import LazyLogger

from dotenv import load_dotenv


# Load env variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))
RIOT_API_KEY = os.getenv('RIOT_API_KEY')


# Subclass LazyLogger to add the add_file_handler method
class MyLazyLogger(LazyLogger):
    def add_file_handler(self, log_file_path):
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.addHandler(file_handler)

# Logger config (with MyLazyLogger)
logger = MyLazyLogger(__name__)
logger.setLevel(logging.INFO)
log_file_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'tracker.log')
logger.add_file_handler(log_file_path)


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