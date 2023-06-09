import re

with open('./test.txt', 'r', encoding='utf=8') as file:
    text = file.read()
    text = re.sub(r'\n{2,}', '\n\n', text)
print(text)

