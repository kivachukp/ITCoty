import openai
import requests

# openai.organization = "YOUR_ORG_ID"
openai.api_key = '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'
token = 'org-CWaeprmWEWoPJGnzS5Yx7kXA'
openai.Model.list()

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer org-CWaeprmWEWoPJGnzS5Yx7kXA",
}
data = {
    "model": "text-davinci-002",
    "prompt": "Hello my name is John!",
    "max_tokens": 5,
   }

response = requests.post('https://api.openai.com/v1/chat/completions', json=data, headers=headers)
print(response.text)
