import requests
import os
from dotenv import load_dotenv
from requests import post

load_dotenv()
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')


"""Работающий запрос к странице сайта"""
response = post('http://127.0.0.1:8080/neuro_request',
           json={
               'prompt': 'Расскажи шутку на русском языке, не основанную на игре слов',
               'model' : 'nvidia/nemotron-3-super-120b-a12b:free'
           })
print(response.json()['message'])

# import requests
# # Create a response (POST /responses)
# response = requests.post(
#   "https://openrouter.ai/api/v1/responses",
#   headers={
#     "Authorization": f"Bearer {OPENROUTER_API_KEY}",
#     "X-OpenRouter-Experimental-Metadata": "enabled"
#   },
#   json={
#     "input": "Tell me a joke",
#     "model": "nvidia/nemotron-3-super-120b-a12b:free"
#   },
# )
# print(response.json())

#--------API запрос к сайту--------
# response = post('http://127.0.0.1:8080/api/neuro',
#                 json={
#                     'model': 'nvidia/nemotron-3-super-120b-a12b:free',
#                     'prompt': 'Расскажи шутку',
#                     'user_mail': 'vlad.isupov.09@mail.ru'
#                 })
# print(response.json())
