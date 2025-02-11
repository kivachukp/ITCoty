import configparser
from db_operations.scraping_db import DataBaseOperations
from logs.logs import Logs
from sites.scraping_careerjet import СareerjetGetInformation
from sites.scraping_careerspace import CareerSpaceGetInformation
from sites.scraping_designer import DesignerGetInformation
from sites.scraping_dev import DevGetInformation
from sites.scraping_epam_anywhere import EpamGetInformation
from sites.scraping_geekjob import GeekGetInformation
from sites.scraping_habr import HabrGetInformation
from sites.scraping_hh import HHGetInformation
from sites.scraping_hhkz import HHKzGetInformation
from sites.scraping_praca import PracaGetInformation
from sites.scraping_rabota import RabotaGetInformation
from sites.scraping_remocate import RemocateGetInformation
from sites.scraping_remotehub import RemotehubGetInformation
# from sites.scraping_remotejob import RemoteJobGetInformation
from sites.scraping_superjob import SuperJobGetInformation
from sites.scraping_svyazi import SvyaziGetInformation
from sites.scrapping_finder import FinderGetInformation
from sites.scraping_ingamejob import IngameJobGetInformation
from sites.scraping_remotejob_upgrade import RemoteJobGetInformation
from helper_functions import helper_functions as helper

logs = Logs()

config = configparser.ConfigParser()
config.read("./settings_/config.ini")

parser_sites = {'nn.hh.ru': HHGetInformation, 'spb.hh.ru': HHGetInformation, 'hh.ru': HHGetInformation,
                'hh.kz': HHKzGetInformation, 'rabota.by': RabotaGetInformation, 'praca.by': PracaGetInformation,
                'remotehub.com': RemotehubGetInformation, 'remote-job.ru': RemoteJobGetInformation,
                'jobs.devby.io' : DevGetInformation, 'russia.superjob.ru': SuperJobGetInformation,
                'superjob.ru': SuperJobGetInformation, 'career.habr.com': HabrGetInformation,
                'u.habr.com': HabrGetInformation,'finder.vc': FinderGetInformation, 'geekjob.ru' : GeekGetInformation,
                'gkjb.ru': GeekGetInformation, 'designer.ru': DesignerGetInformation,
                'www.vseti.app': SvyaziGetInformation, 'ru.ingamejob.com': IngameJobGetInformation}


class SitesParser:

    def __init__(self, client, bot_dict, **kwargs):
        self.report = kwargs['report'] if 'report' in kwargs else None
        self.client = client
        self.current_session = ''
        self.bot = bot_dict['bot']
        self.chat_id = bot_dict['chat_id']
        self.db = DataBaseOperations(report=self.report)
        self.helper = helper



    async def call_sites(self):

        bot_dict = {'bot': self.bot, 'chat_id': self.chat_id}

        # await RemocateGetInformation(bot_dict=bot_dict, report=self.report, db=self.db, helper=self.helper).get_content()

        # await CareerSpaceGetInformation(bot_dict=bot_dict, report=self.report, db=self.db, helper=self.helper).get_content()
        await EpamGetInformation(bot_dict=bot_dict, report=self.report, db=self.db, helper=self.helper).get_content()
        await СareerjetGetInformation(bot_dict=bot_dict, report=self.report, db=self.db, helper=self.helper).get_content()

        await RemotehubGetInformation(bot_dict=bot_dict, report=self.report).get_content()
        await RemoteJobGetInformation(bot_dict=bot_dict, report=self.report).get_content()
        await HHGetInformation(bot_dict=bot_dict, report=self.report).get_content()
        await HHKzGetInformation(bot_dict=bot_dict, report=self.report).get_content()
        await RabotaGetInformation(bot_dict=bot_dict, report=self.report).get_content()
        await PracaGetInformation(bot_dict=bot_dict, report=self.report).get_content()
        await DevGetInformation(bot_dict=bot_dict, report=self.report).get_content()
        await HabrGetInformation(bot_dict=bot_dict, report=self.report).get_content()
        await FinderGetInformation(bot_dict=bot_dict, report=self.report).get_content()
        await GeekGetInformation(bot_dict=bot_dict, report=self.report).get_content()
        await DesignerGetInformation(bot_dict=bot_dict, report=self.report).get_content()
        await SvyaziGetInformation(bot_dict=bot_dict, report=self.report).get_content()
        await IngameJobGetInformation(bot_dict=bot_dict, report=self.report).get_content()

        # await SuperJobGetInformation(bot_dict=bot_dict, report=self.report).get_content()

        print(' -----------------------FINAL -------------------------------')

