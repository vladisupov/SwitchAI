import requests
from flask import Flask, render_template, redirect, request, make_response, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from data import db_session
from data.users import User
from forms.login_form import LoginForm
from forms.register_form import RegisterForm
import os
from data import neuro_api
from dotenv import load_dotenv
from flask import make_response
from data.ai_responses import Responses

load_dotenv()

# Берем ключ для приложения и api key из .env(так безопаснее)
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_URL = "https://openrouter.ai/api/v1/responses"

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

login_manager = LoginManager()
login_manager.init_app(app)


def main():
    db_session.global_init("db/switch.db")
    app.register_blueprint(neuro_api.blueprint)
    app.run(port=8080)


# ------------------------------------------------Главная страница сайта-------------------------------------------

@app.route("/")
def index():
    db_sess = db_session.create_session()
    users = db_sess.query(User).all()
    names = {name.id: (name.surname, name.name) for name in users}
    return render_template("index.html", names=names, title='Главная')
    # Загрузка пользователя


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


# -------------------------------------------Обработка страницы и формы входа. Вход---------------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', title='Авторизация', form=form)


# ------------------------------------------------Выход из аккаунта------------------------------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


# -----------------------------------------Обработка страницы регистрации. Регистрация---------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Register', form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Register', form=form,
                                   message="Пользователь с таким email уже существует")
        user = User(
            name=form.name.data,
            surname=form.surname.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


# --------------------------------------------Страница с нейросетями---------------------------------------
@app.route('/neuro')
def neuro():
    db_sess = db_session.create_session()
    return render_template('neuro.html', title='Нейросети')


# -------------------------------------------Работа с API-----------------------------------------------

# Здесь будет обрабатываться запрос с javascript,
# отправление запроса и получение ответа без обновления страницы
@app.route('/neuro_request', methods=['POST'])
def neuro_request():
    data = request.json
    user_prompt = data.get('prompt', '')
    model = data.get('model', '')

    if not (user_prompt):
        return jsonify({'error': 'No prompt provided'}), 400
    if not (model):
        return jsonify({'error': 'No model provided'}), 400

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

        try:
            ai_message = result['output'][-1]['content'][0]['text']
            ai_response = Responses(                    #Добавление запроса и ответа в таблицу
                user_id=current_user.id,
                model=model,
                prompt=user_prompt,
                response=ai_message,
            )
            db_sess = db_session.create_session()
            db_sess.add(ai_response)
            db_sess.commit()
            return jsonify({'message': ai_message})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    except Exception as e:
        print(str(e))
        return jsonify({'error': str(e)}), 500


# --------------------------------------Обработка ошибок при подключении к сайту по API

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(400)
def bad_request(_):
    return make_response(jsonify({'error': 'Bad Request'}), 400)


if __name__ == '__main__':
    main()
