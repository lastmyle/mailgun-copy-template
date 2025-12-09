import requests
import sys
import os

MG_BASE_URL = os.environ.get('MG_BASE_URL', 'https://api.mailgun.net/v3')
MG_MAIL_DOMAIN = os.environ.get('MG_MAIL_DOMAIN', None)
MG_API_KEY = os.environ.get('MG_API_KEY', None)

def list_templates():
    url = f'{MG_BASE_URL}/{MG_MAIL_DOMAIN}/templates'
    r = requests.get(url, auth=('api', MG_API_KEY))
    if r.status_code == 200:
        data = r.json()
        if 'items' in data:
            return [item['name'] for item in data['items']]
        else:
            print(f"Unexpected response structure: {data}")
            return None
    else:
        print(f"Failed to list templates: {r.text}")
        return None

if __name__ == "__main__":
    if MG_MAIL_DOMAIN is None or MG_API_KEY is None:
        print('Environment variables MG_MAIL_DOMAIN and MG_API_KEY are required.')
        print(f'Current values:\nMG_MAIL_DOMAIN: {MG_MAIL_DOMAIN}\nMG_API_KEY: {MG_API_KEY}')
        exit(1)

    templates = list_templates()
    if templates:
        for name in templates:
            print(name)
    else:
        print("No templates found or error occurred.")
