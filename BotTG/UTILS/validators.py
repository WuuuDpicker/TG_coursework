import re
import json

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def get_age_suffix(age):
    if age % 10 == 1 and age % 100 != 11:
        return 'год'
    elif 2 <= age % 10 <= 4 and age % 100 not in [12, 13, 14]:
        return 'года'
    else:
        return 'лет'

def is_valid_specialty_code(code):
    # Пример: 08.02.01
    return bool(re.match(r'^\d{2}\.\d{2}\.\d{2}$', code))

def specialty_exists(code):
    # Открываем specialties.json и ищем специальность по коду
    with open('specialties.json', 'r', encoding='utf-8') as f:
        specialties = json.load(f)
    for spec in specialties:
        if spec['code'] == code:
            return spec
    return None

def get_specialty_info_text(spec):
    return (
        f"Код: <b>{spec['code']}</b>\n"
        f"Наименование: <b>{spec['title']}</b>\n"
        f"Классификация: <b>{spec['category']}</b>\n"
        f"Срок обучения: <b>{spec.get('duration', 'уточняйте на сайте')}</b>"
    )