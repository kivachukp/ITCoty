import configparser
import random
import re
import time

from telegraph import Telegraph
from utils.pictures.pictures_urls.pictures_urls import pictures_urls

class TelegraphPoster:

    def __init__(self, account_name=None):
        self.account_name = account_name if account_name else 'ITCoty'
        self.telegraph = Telegraph()
        self.telegraph.create_account(short_name=self.account_name)


    def telegraph_post(self, title, text):
        while True:
            try:
                telegraph_article_url = self.telegraph.create_page(title=title,html_content=text, author_name="ITCoty.ru")
                time.sleep(random.randrange(1, 3))
                return telegraph_article_url['url']
            except Exception as ex:
                if 'Flood control exceeded' in str(ex):
                    print(str(ex))
                    time_sleep = re.findall(r'[0-9]+', str(ex))
                    if time_sleep and time_sleep[0]:
                        time_sleep = int(time_sleep[0])
                    else:
                        time_sleep = 15
                    time.sleep(time_sleep+2)
            break


    def telegraph_post_digests(self, shorts_dict, profession):

        config = configparser.ConfigParser()
        config.read("./settings/config.ini")
        try:
            profession_channel_link = config['Channel_links'][f'{profession}_channel']
        except:
            profession_channel_link = ''

        telegraph_links_dict = {}
        numbers_vacancies_dict = {}
        for sub in shorts_dict:
            body = f"<img src={pictures_urls[sub.lower()]}>" if sub.lower() in pictures_urls else f"<img src={pictures_urls['common']}><br>"
            body += f"Ещё больше вакансий и стажировок в <a href='{profession_channel_link}'><b>телеграм канале {profession.title()}</b></a><br><br>"
            body += shorts_dict[sub].split('\n\n', 1)[1].replace('\n\n', '<br><br>')

            numbers_vacancies_dict[sub] = len(re.findall(r"a href", body)) - 1
            title = shorts_dict[sub].split('\n\n', 1)[0].replace("#", '')
            telegraph_links_dict[sub] = self.telegraph_post(title, body)
            print(telegraph_links_dict[sub])
        return {'telegraph_links_dict': telegraph_links_dict, 'numbers_vacancies_dict': numbers_vacancies_dict}


if '__main__' == __name__:

    shorts_dict = {
        'game': 'Дайджест вакансий для #Game за 26.06.2023\n\n'
                '<a href="https://t.me/agrerator_channel_fake/5482"><b>Lead Game Designer</b></a> в My.Games (eng: B1, Remote, 3 300 $)\n\n'
                '<a href="https://t.me/agrerator_channel_fake/5489"><b>I want a game developer.</b></a> в Shahroz mian12 (eng: a0)\n\n'
                '<a href="https://t.me/agrerator_channel_fake/5490"><b>I wanted a game developer.</b></a> в Shahroz mian12 (eng: b1, 1,000 - $)\n\n'
                '<a href="https://t.me/agrerator_channel_fake/5487"><b>2D artist (Marketing)</b></a> в ООО Прайм Геймс (eng: B1, Remote, fulltime, 30 000 - 50 000 руб)\n\n'
                '<a href="https://t.me/agrerator_channel_fake/5488"><b>Визуализатор</b></a> в Capital Group (eng: B1, Fulltime)\n\n'
                '<a href="https://t.me/agrerator_channel_fake/5492"><b>Преподаватель по программированию Unity</b></a> в Brainhub (eng: B1, Remote, 45 000 - 100 000 ₽)\n\n'
                '<a href="https://t.me/agrerator_channel_fake/5493"><b>Game Designer</b></a> в ООО Фандог (eng: B1, Remote, fulltime, 2016 года. Проекты, с которыми мы работа)\n\n'
                '<a href="https://t.me/agrerator_channel_fake/5491"><b>Game designer</b></a> в Azur Games (eng: B1, Remote)',
        'support': 'Дайджест вакансий для #Support за 26.06.2023\n\n'
                   '<a href="https://t.me/agrerator_channel_fake/5482"><b>Lead Game Designer</b></a> в My.Games (eng: B1, Remote, 3 300 $)\n\n'
                   '<a href="https://t.me/agrerator_channel_fake/5489"><b>I want a game developer.</b></a> в Shahroz mian12 (eng: a0)\n\n'
                   '<a href="https://t.me/agrerator_channel_fake/5490"><b>I wanted a game developer.</b></a> в Shahroz mian12 (eng: b1, 1,000 - $)\n\n'
                   '<a href="https://t.me/agrerator_channel_fake/5487"><b>2D artist (Marketing)</b></a> в ООО Прайм Геймс (eng: B1, Remote, fulltime, 30 000 - 50 000 руб)\n\n'
                   '<a href="https://t.me/agrerator_channel_fake/5488"><b>Визуализатор</b></a> в Capital Group (eng: B1, Fulltime)\n\n'
                   '<a href="https://t.me/agrerator_channel_fake/5492"><b>Преподаватель по программированию Unity</b></a> в Brainhub (eng: B1, Remote, 45 000 - 100 000 ₽)\n\n'
                   '<a href="https://t.me/agrerator_channel_fake/5493"><b>Game Designer</b></a> в ООО Фандог (eng: B1, Remote, fulltime, 2016 года. Проекты, с которыми мы работа)\n\n'
                   '<a href="https://t.me/agrerator_channel_fake/5491"><b>Game designer</b></a> в Azur Games (eng: B1, Remote)'
    }

    t = TelegraphPoster()
    t.telegraph_post_digests(shorts_dict)

