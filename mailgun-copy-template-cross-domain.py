import requests
import sys
import os
import json

MG_BASE_URL = os.environ.get('MG_BASE_URL', 'https://api.mailgun.net/v3')
MG_API_KEY = os.environ.get('MG_API_KEY', None)

def get_template(domain, name):
    r = requests.get('{}/{}/templates/{}'.format(MG_BASE_URL, domain, name), auth=('api', MG_API_KEY), params={'active': 'yes'})
    if r.status_code == 200:
        return r.json()['template']
    else:
        print(f"Failed to fetch template '{name}' from domain '{domain}': {r.text}")
        return None

def create_template_version(domain, name, template_html, engine=None, mjml=None):
    """Create or update the initial version of an existing template"""
    version_data = {
        'template': template_html,
        'active': 'yes'
    }
    if engine:
        version_data['engine'] = engine
    if mjml:
        version_data['mjml'] = mjml

    r = requests.put('{}/{}/templates/{}/versions/initial'.format(MG_BASE_URL, domain, name),
                     auth=('api', MG_API_KEY), data=version_data)
    if r.status_code == 200:
        return r.json()['template']
    else:
        print(f"Failed to update version for '{name}' in domain '{domain}': {r.text}")
        return None

def copy_template_cross_domain(src_domain, src_name, dst_domain, dst_name):
    """Copy a template from one domain to another"""
    # Get source template
    print(f"Fetching template '{src_name}' from '{src_domain}'...")
    src_template = get_template(src_domain, src_name)
    if not src_template:
        print(f"Source template '{src_name}' not found in domain '{src_domain}'.")
        return False

    # Extract data
    engine = src_template['version'].get('engine')
    mjml = src_template['version'].get('mjml')
    template_html = src_template['version']['template']

    print(f"  Engine: {engine if engine else 'none'}")
    print(f"  MJML: {len(mjml) if mjml else 0} chars")
    print(f"  HTML: {len(template_html)} chars")

    # Check if destination template exists
    print(f"\nChecking if template '{dst_name}' exists in '{dst_domain}'...")
    dst_template = get_template(dst_domain, dst_name)

    if dst_template:
        src_is_dnd = src_template.get('createdBy') == 'dnd'
        dst_is_dnd = dst_template.get('createdBy') == 'dnd'

        print(f"  Template exists (createdBy: {dst_template.get('createdBy', 'NOT SET')})")

        # Warn if source is Visual Builder but destination is not
        if src_is_dnd and not dst_is_dnd:
            print(f"\n⚠️  WARNING: Source template is a Visual Builder template, but destination is not!")
            print(f"  The copied template will show as 'HTML editor' type in the Mailgun UI.")
            print(f"  To preserve Visual Builder type, delete '{dst_name}' and recreate it as Visual Builder.")
            response = input("\n  Continue anyway? (y/N): ")
            if response.lower() != 'y':
                print("  Aborted.")
                return False

        print(f"  Updating initial version...")
        result = create_template_version(dst_domain, dst_name, template_html, engine, mjml)
        if result:
            print(f"\n✓ Successfully copied '{src_name}' from '{src_domain}' to '{dst_name}' in '{dst_domain}'")
            return True
        else:
            return False
    else:
        src_is_dnd = src_template.get('createdBy') == 'dnd'
        print(f"  Template does NOT exist in destination domain.")

        if src_is_dnd:
            print(f"\n⚠️  Source template is a VISUAL BUILDER template!")
            print(f"  You MUST create '{dst_name}' as a Visual Builder template to preserve its type.")

        print(f"\nPlease create an empty template named '{dst_name}' in the Mailgun UI for domain '{dst_domain}' first:")
        print(f"  1. Go to Mailgun dashboard")
        print(f"  2. Select domain '{dst_domain}'")
        print(f"  3. Navigate to Templates")
        print(f"  4. Click 'Create message template'")

        if src_is_dnd:
            print(f"  5. Select 'Visual builder' ⚠️  IMPORTANT for Visual Builder templates!")
        else:
            print(f"  5. Select 'Visual builder' (recommended) or 'HTML editor'")

        print(f"  6. Name it '{dst_name}'")
        print(f"  7. Save the empty template")
        print(f"  8. Run this script again")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print('Usage:')
        print('  python3 mailgun-copy-template-cross-domain.py <src_domain> <src_template> <dst_domain> <dst_template>')
        print('')
        print('Example:')
        print('  python3 mailgun-copy-template-cross-domain.py \\')
        print('    sandbox647641198e804fa69bdaccdeb73f5e46.mailgun.org remittance \\')
        print('    mg.maestropower.co.nz remittance')
        print('')
        print('Environment variables required:')
        print('  MG_API_KEY - Mailgun API Key (must have access to both domains)')
        print('  MG_BASE_URL - Mailgun API base URL (defaults to https://api.mailgun.net/v3)')
        exit(1)

    if MG_API_KEY is None:
        print('Environment variable MG_API_KEY is required.')
        print(f'Current value: {MG_API_KEY}')
        exit(1)

    src_domain = sys.argv[1]
    src_name = sys.argv[2]
    dst_domain = sys.argv[3]
    dst_name = sys.argv[4]

    print(f"Cross-domain template copy:")
    print(f"  Source: {src_name} @ {src_domain}")
    print(f"  Destination: {dst_name} @ {dst_domain}")
    print()

    success = copy_template_cross_domain(src_domain, src_name, dst_domain, dst_name)
    exit(0 if success else 1)
