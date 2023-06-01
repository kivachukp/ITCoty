import asyncio
from helper_functions.cities_and_countries.cities_parser import CitiesAndCountries
from helper_functions.parser_find_add_parameters.parser_find_add_parameters import FinderAddParameters
from helper_functions.database_update_data.database_update_data import DatabaseUpdateData
from sites.scraping_hh import HHGetInformation
from sites.scraping_hhkz import HHKzGetInformation
from sites.scraping_praca import PracaGetInformation
from sites.scraping_dev import DevGetInformation
from sites.scraping_remotehub import RemotehubGetInformation
# from sites.scraping_remotejob import RemoteJobGetInformation
from sites.scraping_superjob import SuperJobGetInformation
from sites.scraping_habr import HabrGetInformation
from sites.scrapping_finder import FinderGetInformation
from sites.scraping_geekjob import GeekGetInformation
from sites.scraping_designer import DesignerGetInformation
from sites.scraping_svyazi import SvyaziGetInformation
from sites.scraping_ingamejob import IngameJobGetInformation
from sites.scraping_remotejob_upgrade import RemoteJobGetInformation

# fap = FinderAddParameters()
# result = asyncio.run(fap.find_city_country(text='Беларусь, Могилёв, улица Белинского, 28'))
# print(result)
#
# salary = fap.salary_to_set_form(text='от 40 000 до 60 000 руб. на руки')
# result = asyncio.run(fap.compose_salary_dict_from_salary_list(salary))
# print(result)



# parser = RemotehubGetInformation()
# asyncio.run(parser.get_content())

# parser = RemoteJobGetInformation()
# asyncio.run(parser.get_content())

# parser = HHGetInformation()
# asyncio.run(parser.get_content())

# parser = HHKzGetInformation()
# asyncio.run(parser.get_content())

# parser = PracaGetInformation()
# asyncio.run(parser.get_content())

# parser = DevGetInformation()
# asyncio.run(parser.get_content())

# parser = FinderGetInformation()
# asyncio.run(parser.get_content())

# parser = GeekGetInformation()
# asyncio.run(parser.get_content())

# parser = DesignerGetInformation()
# asyncio.run(parser.get_content())

# parser = SvyaziGetInformation()
# asyncio.run(parser.get_content())

# parser = IngameJobGetInformation()
# asyncio.run(parser.get_content())




