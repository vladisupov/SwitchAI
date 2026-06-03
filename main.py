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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

# Берем ключ для приложения и api key из .env(так безопаснее)
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_URL = "https://openrouter.ai/api/v1/responses"
MY_GMAIL = os.getenv('MY_GMAIL')
PASSWORD = os.getenv('GMAIL_PASSWORD')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

login_manager = LoginManager()
login_manager.init_app(app)


def main():
    db_session.global_init("db/switch.db")
    app.register_blueprint(neuro_api.blueprint)
    app.run(port=8080)
#Функция для отправки верификационного письма
def send_verification_email(user_email, token):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = MY_GMAIL
    smtp_password = PASSWORD

    verification_link = f"http://127.0.0.1:8080/verify?token={token}&email={user_email}"

    message = MIMEMultipart()
    message["From"] = smtp_user
    message["To"] = user_email
    message["Subject"] = "Подтверждение email"

    html = f"""
        <html>
        <body>
            <h2>Подтверждение email</h2>
            <p>Перейдите по ссылке для верификации:</p>
            <a href="{verification_link}">{verification_link}</a>
            <p>Ссылка действительна 24 часа</p>
        </body>
        </html>
        """

    message.attach(MIMEText(html, "html"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(message)
        server.quit()
        return True
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

#Функция для отправки инструкции по смене пароля
def send_password_reset_email(user_email, token):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = MY_GMAIL
    smtp_password = PASSWORD

    link = f"http://127.0.0.1:8080/forgot_password/{token}/{user_email}"

    message = MIMEMultipart()
    message["From"] = smtp_user
    message["To"] = user_email
    message["Subject"] = "Сброс пароля"

    html = f"""
    <html>
    <body>
        <h2>Сброс пароля от аккаунта на сайте SwitchAI</h2>
        <p>Вы сделали запрос на сброс пароля</p>
        <a href="{link}">Нажмите здесь для продолжения</a>
        <p>Ссылка действительна 24 часа</p>
    </body>
    </html>
    """

    message.attach(MIMEText(html, "html"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(message)
        server.quit()
        return True
    except Exception as e:
        print(f"Ошибка: {e}")
        return False


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
        email = form.email.data
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            if user.is_verified:
                login_user(user, remember=form.remember_me.data)
                return redirect("/")
            return render_template('login.html', message="Email не подтвержден.", form=form, email=email)
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
def register():
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
        token = user.generate_verification_token()
        db_sess.commit()
        send_verification_email(form.email.data, token)

        return render_template('register.html', title='Register', form=form,
                               message="Регистрация прошла успешно. Проверьте почту для подтверждения.")
    return render_template('register.html', title='Регистрация', form=form)

#---------------------------------------------Страница для подтверждения почты-----------------------------

@app.route('/verify', methods=['GET'])
def verify_email():
    token = request.args.get('token')
    email = request.args.get('email')
    db_sess = db_session.create_session()

    # Передаем email в шаблон, чтобы JS мог использовать его для повторной отправки
    if db_sess.query(User).filter(User.email == email).first():
        if db_sess.query(User).filter(User.email == email).first().is_verified:
            message = "Ваш email уже подтвержден"
            return render_template('verify.html', title='Верификация',
                                   message=message, email=email)

    if not token:
        message = "Токен не предоставлен"
        return render_template('verify.html', title='Верификация',
                               message=message, email=email)

    user = db_sess.query(User).filter(User.verification_token == token).first()

    if not user:
        message = "Неверный или истекший токен"
        return render_template('verify.html', title='Верификация',
                           message=message, email=email)

    if user.verify_email(token):
        db_sess.commit()
        message = "Ваш email успешно подтвержден!"
    else:
        message = "Срок действия токена истек"

    return render_template('verify.html', title='Верификация',
                    message=message, email=email)

#----------------------------------------Повторная отправка верификационного письма---------------------------
@app.route('/resend_verification', methods=['POST'])
def resend_verification():
    db_sess = db_session.create_session()

    email = request.form.get('email')
    user = db_sess.query(User).filter(User.email == email).first()
    if not user:
        return jsonify({"error": "Пользователь не найден"}), 404

    if user.is_verified:
        return jsonify({"error": "Email уже подтвержден"}), 400

    token = user.generate_verification_token()
    db_sess.commit()
    send_verification_email(email, token)

    return jsonify({"message": "Письмо отправлено повторно"}), 200


#-----------------------------------------Отправка письма по сбросу пароля----------------------------------------
@app.route('/send_password_email', methods=['POST'])
def send_password_mail():
    db_sess = db_session.create_session()

    email = request.form.get('email')
    user = db_sess.query(User).filter(User.email == email).first()
    if not user:
        return jsonify({"error": "Пользователь не найден"}), 404

    token = user.generate_password_token()
    db_sess.commit()
    send_password_reset_email(email, token)

    return jsonify({"message": "Письмо отправлено"}), 200

#----------------------------------------------Страница забыли пароль-----------------------------------------
@app.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html', title="Забыли пароль")


#--------------------------------------------Страница сброса пароля----------------------------------
@app.route('/forgot_password/<token>/<email>')
def reset_password(token, email):
    if not token:
        message = "Токен не предоставлен"
        return render_template("reset_password.html", message=message, title="Сброс пароля", email=email)

    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.password_token == token).first()

    if not user:
        message = "Истекший или неверный токен"
        return render_template("reset_password.html", message=message, title="Сброс пароля", email=email)

    if user.check_for_reset_password(token):
        db_sess.commit()
        message = "OK"
    else:
        message = "Срок действия токена истек"

    return render_template("reset_password.html", message=message, title="Сброс пароля", email=email)

#--------------------------------------------Смена пароля------------------------------------------------------
@app.route('/change_password', methods=['POST'])
def change_password():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email:
        return jsonify({"error": "Email не предоставлен"})
    if not password:
        return jsonify({"error": "Пароль не предоставлен"})

    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.email == email).first()

    if not user:
        return jsonify({"error": "Пользователь не найден"})

    user.set_password(password)
    db_sess.commit()
    return jsonify({"message": "Пароль установлен"})


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
            ai_response = Responses(  # Добавление запроса и ответа в таблицу
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


# --------------------------------------Обработка ошибок на сайте-----------------------------

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(400)
def bad_request(_):
    return make_response(jsonify({'error': 'Bad Request'}), 400)


if __name__ == '__main__':
    main()
