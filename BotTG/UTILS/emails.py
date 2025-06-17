import json
import smtplib
from email.message import EmailMessage
from datetime import datetime

def load_email_config():
    with open('email_config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def pick_smtp_config(email):
    domain = email.split('@')[-1].lower()
    configs = load_email_config()
    for conf in configs:
        if domain in conf['smtp_user']:
            return conf
    return configs[0]  # fallback

def send_confirmation_code(email, code):
    try:
        conf = pick_smtp_config(email)
        msg = EmailMessage()
        msg['Subject'] = 'Код подтверждения для регистрации'
        msg['From'] = conf['smtp_user']
        msg['To'] = email
        msg.set_content(f'Ваш код подтверждения: {code}')
        with smtplib.SMTP_SSL(conf['smtp_server'], conf['smtp_port']) as server:
            server.login(conf['smtp_user'], conf['smtp_password'])
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"[send_confirmation_code] Ошибка отправки email: {e}")
        return False

def send_documents_to_admin(admin_email, user_email, specialty, files):
    try:
        conf = pick_smtp_config(admin_email)
        msg = EmailMessage()
        msg['Subject'] = f'Новая заявка от {user_email} на специальность {specialty}'
        msg['From'] = conf['smtp_user']
        msg['To'] = admin_email
        msg.set_content(f'Поступила новая заявка от {user_email} на специальность {specialty}. Документы во вложении.')
        for file_path, file_name in files:
            with open(file_path, 'rb') as f:
                file_data = f.read()
                msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)
        with smtplib.SMTP_SSL(conf['smtp_server'], conf['smtp_port']) as server:
            server.login(conf['smtp_user'], conf['smtp_password'])
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"[send_documents_to_admin] Ошибка отправки email: {e}")
        return False

def send_documents_to_admin_with_user_data(admin_email, user_data, specialty_title, specialty_code, files):
    try:
        conf = pick_smtp_config(admin_email)
        msg = EmailMessage()
        msg['Subject'] = f'Новая заявка на поступление - {specialty_title}'
        msg['From'] = conf['smtp_user']
        msg['To'] = admin_email
        
        # Формируем тело письма с данными пользователя
        body = f"""
Новая заявка на поступление

ДАННЫЕ АБИТУРИЕНТА:
👤 ФИО: {user_data['name']}
📧 Email: {user_data['email']}
🎂 Возраст: {user_data['age']} лет
♂️♀️ Пол: {user_data['gender']}
🆔 Telegram ID: {user_data['telegram_id']}
👤 Username: @{user_data['username']}

СПЕЦИАЛЬНОСТЬ:
🎓 Название: {specialty_title}
📋 Код: {specialty_code}

Документы прикреплены к письму.

Для ответа используйте формат:
1. Статус заявки: одобрено/отклонено
2. Пояснение: [ваш комментарий]
        """
        
        msg.set_content(body)
        
        # Прикрепляем файлы
        for file_path, file_name in files:
            try:
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                    msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)
            except Exception as e:
                print(f"Ошибка прикрепления файла {file_name}: {e}")
        
        with smtplib.SMTP_SSL(conf['smtp_server'], conf['smtp_port']) as server:
            server.login(conf['smtp_user'], conf['smtp_password'])
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"[send_documents_to_admin_with_user_data] Ошибка отправки email: {e}")
        return False

def send_admin_response_to_user(user_email, application_id, admin_response):
    try:
        conf = pick_smtp_config(user_email)
        msg = EmailMessage()
        msg['Subject'] = f'Ответ по заявке #{application_id}'
        msg['From'] = conf['smtp_user']
        msg['To'] = user_email
        
        body = f"""
Ответ по вашей заявке на поступление

📋 ID заявки: {application_id}
📅 Дата ответа: {datetime.now().strftime('%d.%m.%Y %H:%M')}

{admin_response}

С уважением,
Администрация учебного заведения
        """
        
        msg.set_content(body)
        
        with smtplib.SMTP_SSL(conf['smtp_server'], conf['smtp_port']) as server:
            server.login(conf['smtp_user'], conf['smtp_password'])
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"[send_admin_response_to_user] Ошибка отправки email: {e}")
        return False