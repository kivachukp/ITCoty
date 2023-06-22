
with open('data.txt', 'r', encoding='utf-8') as file:
    text = file.read()

text = text.replace('\n', '|')
text_list = text.split('|')
text_str = ''
for i in text_list:
    text_str += f"'{i.strip()}', "

print(text_str[:-2])
