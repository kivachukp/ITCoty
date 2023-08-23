from _apps.amin_panel_tg_view.data.get_data import GetData
from _apps.amin_panel_tg_view.views.bot.show_details._data_pattern import pattern
get_data = GetData()

async def get_inline_menu(local):
    inline_menu = {}

    for key in pattern:
        inline_menu[key] = {
            'callback': f"**{key}",
            'output': await get_data.get_admin(profession=key, local=local)

        }
    return inline_menu

    # inline_menu = {
    #     'junior': {
    #         'callback': 'juniors',
    #         'output': get_data.get_admin(profession='junior')
    #     },
    #     'frontend': {
    #         'callback': 'frontend',
    #         'output': get_data.get_admin(profession='frontend')
    #     },
    #     'designer': {
    #         'callback': 'designer',
    #         'output': get_data.get_admin(profession='designer')
    #     },
    #     'mobile': {
    #         'callback': 'mobile',
    #         'output': get_data.get_admin(profession='designer')
    #     },
    #     'designer': {
    #         'callback': 'designer',
    #         'output': get_data.get_admin(profession='designer')
    #     },
    #     'designer': {
    #         'callback': 'designer',
    #         'output': get_data.get_admin(profession='designer')
    #     },
    #     'designer': {
    #         'callback': 'designer',
    #         'output': get_data.get_admin(profession='designer')
    #     },
    #
    #     # 'Мои работы': {
    #     #     'callback': 'i_suggest',
    #     #     'Аранжировки': {
    #     #         'callback': 'arragement',
    #     #         'output': [
    #     #             {
    #     #                 'text': 'Хованщина',
    #     #                 'picture_url': '',
    #     #                 'video_url': 'https://youtu.be/u5dzXnaSuMY',
    #     #                 'sticker': ''
    #     #             },
    #     #             {
    #     #                 'text': 'Мазурка',
    #     #                 'picture_url': '',
    #     #                 'video_url': 'https://youtu.be/Pp_jTs1ELvE',
    #     #                 'sticker': ''
    #     #             }
    #     #         ]
    #     #     },
    #     #     'Пиано Каверы': {
    #     #         'callback': 'piano',
    #     #         'output': [
    #     #             {
    #     #                 'text': 'piano piano piano',
    #     #                 'picture_url': '',
    #     #                 'video_url': '',
    #     #                 'sticker': ''
    #     #             }
    #     #         ]
    #     #
    #     #     }
    #     #
    #     # }
    # }