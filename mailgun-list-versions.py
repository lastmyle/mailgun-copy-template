import requests
import sys
import os
import json

MG_BASE_URL = os.environ.get('MG_BASE_URL', 'https://api.mailgun.net/v3')
MG_MAIL_DOMAIN = os.environ.get('MG_MAIL_DOMAIN', None)
MG_API_KEY = os.environ.get('MG_API_KEY', None)

def get_template_versions(name):
    url = f'{MG_BASE_URL}/{MG_MAIL_DOMAIN}/templates/{name}/versions'
    print(f"curl -u 'api:{MG_API_KEY}' '{url}'")
    r = requests.get(url, auth=('api', MG_API_KEY))
    if r.status_code == 200:
        data = r.json()
        if 'template' in data and 'versions' in data['template']:
            return data['template']['versions']
        elif 'versions' in data:
            return data['versions']
        else:
            print(f"Unexpected response structure: {json.dumps(data)}")
            return None
    else:
        print(f"Failed to fetch template versions for '{name}': {r.text}")
        return None

def print_template_versions_json(versions):
    print("versions:")
    for v in versions:
        #print(json.dumps(v, separators=(',', ':')))
        print(f"- tag: \"{v['tag']}\"")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage: python3 mailgun-list-versions.py <template_name>')
        exit(1)
    if MG_MAIL_DOMAIN is None or MG_API_KEY is None:
        print('Environment variables MG_MAIL_DOMAIN and MG_API_KEY are required. Current values:\nMG_MAIL_DOMAIN: {}\nMG_API_KEY: {}'.format(MG_MAIL_DOMAIN, MG_API_KEY))
        exit(1)
    template_name = sys.argv[1]
    versions = get_template_versions(template_name)
    if versions:
        print_template_versions_json(versions)
    else:
        print("No versions found.")
