import requests
import sys
import os

MG_BASE_URL = os.environ.get('MG_BASE_URL', 'https://api.mailgun.net/v3')
MG_MAIL_DOMAIN = os.environ.get('MG_MAIL_DOMAIN', None)
MG_API_KEY = os.environ.get('MG_API_KEY', None)

def get_template(name):
    r = requests.get('{}/{}/templates/{}'.format(MG_BASE_URL, MG_MAIL_DOMAIN, name), auth=('api', MG_API_KEY), params={'active': 'yes'})
    if r.status_code == 200:
        return r.json()['template']
    else:
        print(f"Failed to fetch template '{name}': {r.text}")
        return None

def create_template(name, description, template):
    r = requests.post('{}/{}/templates'.format(MG_BASE_URL, MG_MAIL_DOMAIN), auth=('api', MG_API_KEY), data={
        'name': name,
        'description': description,
        'template': template
    })
    if r.status_code == 200 and r.json().get('message') == 'template has been stored':
        return r.json()['template']
    else:
        print(f"Failed to create template '{name}': {r.text}")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print('Usage: python3 mailgun-copy-template.py <source_template_name> <destination_template_name>')
        exit(1)
    elif MG_MAIL_DOMAIN is None or MG_API_KEY is None:
        print('Environment variables MG_MAIL_DOMAIN and MG_API_KEY are required. Current values:\nMG_MAIL_DOMAIN: {}\nMG_API_KEY: {}'.format(MG_MAIL_DOMAIN, MG_API_KEY))
        exit(1)
    else:
        src_name = sys.argv[1]
        dst_name = sys.argv[2]
        template = get_template(src_name)
        if template:
            created = create_template(dst_name, template.get('description', ''), template['version']['template'])
            if created:
                print(f"Template '{src_name}' copied to '{dst_name}' successfully.")
            else:
                print(f"Failed to copy template '{src_name}' to '{dst_name}'.")
        else:
            print(f"Source template '{src_name}' not found.")