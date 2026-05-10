import flask
from flask import request, jsonify, make_response
import requests
from dotenv import load_dotenv
import os
from data.users import User

from . import db_session

load_dotenv()
# Api ключ, ссылка на апи ресурс и возможные моедли
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_URL = "https://openrouter.ai/api/v1/responses"
AI_MODELS = ["nvidia/nemotron-3-super-120b-a12b:free",
             "poolside/laguna-xs.2:free",
             "z-ai/glm-4.5-air:free"
             ]

blueprint = flask.Blueprint(
    'neuro_api',
    __name__,
    template_folder='templates'
)


@blueprint.route('/api/neuro', methods=['POST'])
def api_neuro():
    if not request.json:  # Проверка правильности запроса
        return make_response(jsonify({'error': 'Empty request'}), 400)
    elif not all(key in request.json for key in
                 ['user_mail', 'model', 'prompt']):
        return make_response(jsonify({'error': 'Bad request'}), 400)
    data = request.json
    user_prompt = data.get('prompt', '')
    model = data.get('model', '')
    user_mail = data.get('user_mail', '')

    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.email == user_mail).first()
    if not user:
        return jsonify({'error': 'There is no such user'}), 400 #Проверка на существование пользователя

    if not (user_prompt):
        return jsonify({'error': 'No prompt provided'}), 400
    if not (model):
        return jsonify({'error': 'No model provided'}), 400
    if model not in AI_MODELS:
        return jsonify({'error': 'Invalid model'}), 400  # Проверка на существование модели ии

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "X-OpenRouter-Experimental-Metadata": "enabled"
    }
    # Тело запроса
    json = {
        "input": f"{user_prompt}",
        "model": f"{model}",
    }

    # Запрос и получение ответа
    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=json)
        response.raise_for_status()
        result = response.json()

        ai_message = result['output'][1]['content'][0]['text']
        return jsonify({'message': ai_message})

    except Exception as e:
        print(str(e))
        return jsonify({'error': str(e)}), 500
