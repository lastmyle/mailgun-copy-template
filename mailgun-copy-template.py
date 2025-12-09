import requests
import sys
import os
import json

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

def create_template(name, description, template, engine=None, mjml=None):
    # Step 1: Create empty template
    data = {
        'name': name,
        'description': description
    }
    r = requests.post('{}/{}/templates'.format(MG_BASE_URL, MG_MAIL_DOMAIN), auth=('api', MG_API_KEY), data=data)
    if r.status_code != 200 or r.json().get('message') != 'template has been stored':
        print(f"Failed to create template '{name}': {r.text}")
        return None

    # Step 2: Create initial version with template content
    version_data = {
        'tag': 'initial'
    }
    if engine:
        version_data['engine'] = engine

    version_files = {
        'template': (None, template)
    }
    if mjml:
        # For Visual Builder templates, include both template and mjml
        version_files['mjml'] = (None, mjml)

    r2 = requests.post('{}/{}/templates/{}/versions'.format(MG_BASE_URL, MG_MAIL_DOMAIN, name),
                       auth=('api', MG_API_KEY), data=version_data, files=version_files)
    if r2.status_code == 200:
        return r2.json()['template']
    else:
        print(f"Failed to create template version for '{name}': {r2.text}")
        return None

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
    if len(sys.argv) == 3 and sys.argv[1] == "list-versions":
        if MG_MAIL_DOMAIN is None or MG_API_KEY is None:
            print('Environment variables MG_MAIL_DOMAIN and MG_API_KEY are required. Current values:\nMG_MAIL_DOMAIN: {}\nMG_API_KEY: {}'.format(MG_MAIL_DOMAIN, MG_API_KEY))
            exit(1)
        src_name = sys.argv[2]
        versions = get_template_versions(src_name)
        if versions:
            print_template_versions_json(versions)
        else:
            print("No versions found.")
    elif len(sys.argv) == 3:
        if MG_MAIL_DOMAIN is None or MG_API_KEY is None:
            print('Environment variables MG_MAIL_DOMAIN and MG_API_KEY are required. Current values:\nMG_MAIL_DOMAIN: {}\nMG_API_KEY: {}'.format(MG_MAIL_DOMAIN, MG_API_KEY))
            exit(1)
        src_name = sys.argv[1]
        dst_name = sys.argv[2]
        template = get_template(src_name)
        if template:
            engine = template['version'].get('engine')
            mjml = template['version'].get('mjml')

            # Check if destination template already exists
            dst_template = get_template(dst_name)
            if dst_template:
                # Template exists, update the initial version
                print(f"Template '{dst_name}' already exists, updating initial version...")
                version_data = {
                    'template': template['version']['template'],
                    'active': 'yes'
                }
                if engine:
                    version_data['engine'] = engine
                if mjml:
                    version_data['mjml'] = mjml

                r = requests.put('{}/{}/templates/{}/versions/initial'.format(MG_BASE_URL, MG_MAIL_DOMAIN, dst_name),
                                 auth=('api', MG_API_KEY), data=version_data)
                if r.status_code == 200:
                    print(f"Template '{src_name}' copied to '{dst_name}' successfully.")
                else:
                    print(f"Failed to update version for '{dst_name}': {r.text}")
            else:
                # Template doesn't exist, create it
                created = create_template(dst_name, template.get('description', ''), template['version']['template'], engine, mjml)
                if created:
                    print(f"Template '{src_name}' copied to '{dst_name}' successfully.")
                else:
                    print(f"Failed to copy template '{src_name}' to '{dst_name}'.")
        else:
            print(f"Source template '{src_name}' not found.")
    else:
        print('Usage:\n  python3 mailgun-copy-template.py <source_template_name> <destination_template_name>\n  python3 mailgun-copy-template.py list-versions <source_template_name>')
        exit(1)
