async def get_structure(text):
    text = str(text)
    structure_list = []
    index_p = 1
    index_li = 1

    while index_p >0:
        index_li = text.find('<ul>')
        index_p = text.find('<p>')
        # print('UL', index_li)
        # print('P', index_p)

        if index_p < index_li and index_p != -1:
            structure_list.append('p')
            text = text[index_p + 2:]
            # print('**P**')
            # print('len', len(text))
        else:
            if index_li != -1:
                structure_list.append('ul')
                text = text[index_li + 2:]
                # print('**UL**')
                # print('len', len(text))
            else:
                structure_list.append('p')
                text = text[index_p + 2:]
                # print('**P**')
                # print('len', len(text))
    while index_li > 0:
        index_li = text.find('<ul>')
        structure_list.append('ul')
        text = text[index_li + 2:]

    # match = re.findall(r'\<li\>', str(text))
    # for i in range(0, len(match)):
    #     structure_list.append('li')

    print(structure_list)
    return structure_list

async def get_structure_advance(text):
    text = str(text)
    structure_list = []
    index_p = 1
    index_li = 1

    while index_p >0:
        index_li = text.find('<ul>')
        index_p = text.find('<strong>')
        # print('UL', index_li)
        # print('P', index_p)

        if index_p < index_li and index_p != -1:
            structure_list.append('p')
            text = text[index_p + 2:]
            # print('**P**')
            # print('len', len(text))
        else:
            if index_li != -1:
                structure_list.append('ul')
                text = text[index_li + 2:]
                # print('**UL**')
                # print('len', len(text))
            else:
                structure_list.append('p')
                text = text[index_p + 2:]
                # print('**P**')
                # print('len', len(text))
    while index_li > 0:
        index_li = text.find('<ul>')
        if index_li >0:
            structure_list.append('ul')
            text = text[index_li + 2:]
    # match = re.findall(r'\<li\>', str(text))
    # for i in range(0, len(match)):
    #     structure_list.append('li')

    # print(structure_list)
    return structure_list


async def get_structure_sviazi(content):
    structure_dict = {}
    structure_list = []
    p_numbers = content.find_all('p')
    h_numbers = content.find_all('h4')
    ul_numbers = content.find_all('ul')
    li_numbers = content.find_all('li')
    content = str(content)
    # # what is ul inside?
    # n = 0
    # for ul in ul_numbers:
    #     structure_dict[n] = {}
    #     ul_p = ul.find_all('p')
    #     if ul_p:
    #         if 'ul' not in structure_dict:
    #             structure_dict[n]['ul'] = {}
    #         if 'p' not in structure_dict[n]['ul']:
    #             structure_dict[n]['ul']['p'] = 0
    #         structure_dict[n]['ul']['p'] = len(ul_p)
    #     else:
    #         ul_li = ul.find_all('li')
    #         if ul_li:
    #             if 'ul' not in structure_dict:
    #                 structure_dict[n]['ul'] = {}
    #             if 'li' not in structure_dict[n]['ul']:
    #                 structure_dict[n]['ul']['li'] = len(ul_li)
    #             structure_dict[n]['ul']['li'] += 1
    #     n += 1
    if not structure_dict:
        content_list = []
        while True:
            content_list = []
            p_find = content.find('<p>')
            h_find = content.find('<h4>')
            li_find = content.find('<li>')

            for i in [p_find, h_find, li_find]:
                if i>-1:
                    content_list.append(i)
            if content_list:
                min_element = min(content_list)
                content = content[min_element+1:]
                structure_list.append(content[0:1])
                content = content[2:]

            else:
                break

    # print(structure_list)
    return structure_list




