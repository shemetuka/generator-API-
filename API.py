import requests
import time

API_KEY = 'ab4810b56emsh0392ae177f6ae4ep1d263djsn2d76017a8003'
API_HOST = 'tempmail-so.p.rapidapi.com'
BASE_URL = f'https://{API_HOST}'

HEADERS = {
    'x-rapidapi-host': API_HOST,
    'x-rapidapi-key': API_KEY,
    'Content-Type': 'application/json'
}

# Постав False для тесту, True для продакшену з валідними сертифікатами
VERIFY_SSL = False


def create_temp_email(name='tempuser', domain='example.com', lifespan=0):
    url = f"{BASE_URL}/inboxes"
    data = {
        "name": name,
        "domain": domain,
        "lifespan": lifespan
    }
    try:
        response = requests.post(url, headers=HEADERS, json=data, verify=VERIFY_SSL)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        response.raise_for_status()

        resp_json = response.json()

        # Перевіряємо чи є 'data' зі списком інбоксів
        inboxes = resp_json.get('data')
        if isinstance(inboxes, list) and len(inboxes) > 0:
            inbox = inboxes[0]
        elif isinstance(resp_json, dict) and 'name' in resp_json:
            inbox = resp_json
        else:
            print("Неочікуваний формат відповіді від API")
            return None, None

        email = f"{inbox.get('name', 'unknown')}@{inbox.get('domain', 'example.com')}"
        inbox_id = inbox.get('id')
        print(f"Тимчасова пошта створена: {email}, Inbox ID: {inbox_id}")
        return email, inbox_id

    except requests.exceptions.RequestException as e:
        print(f"Помилка створення тимчасової пошти: {e}")
        return None, None


def register_elevenlabs_account(email, password):
    url = "https://elevenlabs.io/app/sign-up"
    payload = {
        'email': email,
        'password': password
    }
    try:
        response = requests.post(url, data=payload, verify=VERIFY_SSL)
        if response.status_code == 200:
            print(f"Реєстрація акаунта для {email} успішна!")
            return True
        else:
            print(f"Помилка при реєстрації акаунта для {email}: {response.status_code} {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Помилка при реєстрації акаунта: {e}")
        return False


def get_messages(inbox_id):
    url = f"{BASE_URL}/inboxes/{inbox_id}/mails"
    try:
        response = requests.get(url, headers=HEADERS, verify=VERIFY_SSL)
        response.raise_for_status()
        mails = response.json()
        return mails
    except requests.exceptions.RequestException as e:
        print(f"Помилка отримання листів: {e}")
        return []


def get_message_by_id(inbox_id, mail_id):
    url = f"{BASE_URL}/inboxes/{inbox_id}/mails/{mail_id}"
    try:
        response = requests.get(url, headers=HEADERS, verify=VERIFY_SSL)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Помилка отримання листа: {e}")
        return None


def extract_confirmation_link(message):
    if 'body_html' in message:
        body = message['body_html']
        start = body.find('https://elevenlabs.io/confirm?')
        if start != -1:
            end = body.find('"', start)
            if end == -1:
                end = len(body)
            return body[start:end]
    return None


def confirm_account(confirmation_link):
    try:
        response = requests.get(confirmation_link, verify=VERIFY_SSL)
        response.raise_for_status()
        print(f"Акаунт підтверджено за посиланням: {confirmation_link}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Помилка при підтвердженні акаунта: {e}")
        return False


def register_and_confirm_account():
    email, inbox_id = create_temp_email()
    if not email or not inbox_id:
        print("Не вдалося створити тимчасову пошту")
        return

    password = 'your_password_here'  # Заміни на свій пароль
    if not register_elevenlabs_account(email, password):
        return

    print("Чекаємо 10 секунд, щоб прийшов лист...")
    time.sleep(10)

    mails = get_messages(inbox_id)
    if not mails:
        print("Листи не отримано")
        return

    for mail in mails:
        subject = mail.get('subject', '').lower()
        if 'confirmation' in subject:
            mail_id = mail['id']
            full_mail = get_message_by_id(inbox_id, mail_id)
            if full_mail:
                link = extract_confirmation_link(full_mail)
                if link:
                    confirm_account(link)
                    return

    print(f"Підтверджувальне посилання не знайдено для {email}")


if __name__ == "__main__":
    register_and_confirm_account()
