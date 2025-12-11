import requests
import sys
import os
import json
from datetime import datetime
from pathlib import Path

MG_BASE_URL = os.environ.get('MG_BASE_URL', 'https://api.mailgun.net/v3')
MG_API_KEY = os.environ.get('MG_API_KEY', None)

def save_audit_trail(domain, template_name, version_tag, template_html, mjml=None):
    """Save template content to audit trail directory structure"""
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')

    # Create directory structure: logs/{timestamp}/{template}/
    audit_dir = Path('logs') / timestamp / template_name
    audit_dir.mkdir(parents=True, exist_ok=True)

    # Save HTML with domain prefix
    html_file = audit_dir / f'{domain}.html'
    with open(html_file, 'w') as f:
        f.write(template_html)
    print(f"  Saved HTML: {html_file}")

    # Save MJML if present with domain prefix
    if mjml:
        mjml_file = audit_dir / f'{domain}.mjml'
        with open(mjml_file, 'w') as f:
            f.write(mjml)
        print(f"  Saved MJML: {mjml_file}")

    return audit_dir

def get_template(domain, name):
    r = requests.get('{}/{}/templates/{}'.format(MG_BASE_URL, domain, name), auth=('api', MG_API_KEY), params={'active': 'yes'})
    if r.status_code == 200:
        return r.json()['template']
    else:
        print(f"Failed to fetch template '{name}' from domain '{domain}': {r.text}")
        return None

def create_backup_version(domain, name, template_html, engine=None, mjml=None):
    """Create a timestamped backup version before overwriting initial"""
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    backup_tag = f'backup-{timestamp}'

    version_data = {
        'template': template_html,
        'tag': backup_tag,
        'active': 'no'
    }
    if engine:
        version_data['engine'] = engine
    if mjml:
        version_data['mjml'] = mjml

    print(f"  Creating backup version '{backup_tag}'...")
    r = requests.post('{}/{}/templates/{}/versions'.format(MG_BASE_URL, domain, name),
                     auth=('api', MG_API_KEY), data=version_data)
    if r.status_code == 200:
        print(f"  ✓ Backup version created: {backup_tag}")
        return r.json()['template']
    else:
        print(f"  ⚠️  Warning: Failed to create backup version: {r.text}")
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

    # Try PUT first (update existing version)
    r = requests.put('{}/{}/templates/{}/versions/initial'.format(MG_BASE_URL, domain, name),
                     auth=('api', MG_API_KEY), data=version_data)
    if r.status_code == 200:
        return r.json()['template']

    # If PUT fails with "version not found", try POST to create it
    if 'version not found' in r.text.lower():
        print(f"  Initial version doesn't exist, creating it...")
        r = requests.post('{}/{}/templates/{}/versions'.format(MG_BASE_URL, domain, name),
                         auth=('api', MG_API_KEY), data={**version_data, 'tag': 'initial'})
        if r.status_code == 200:
            return r.json()['template']
        else:
            print(f"Failed to create version for '{name}' in domain '{domain}': {r.text}")
            return None
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
    src_version_tag = src_template['version'].get('tag', 'active')

    print(f"  Engine: {engine if engine else 'none'}")
    print(f"  MJML: {len(mjml) if mjml else 0} chars")
    print(f"  HTML: {len(template_html)} chars")

    # Save source to audit trail
    print(f"\nSaving source audit trail...")
    save_audit_trail(src_domain, src_name, src_version_tag, template_html, mjml)

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

        # Create backup version with current destination content
        dst_engine = dst_template['version'].get('engine')
        dst_mjml = dst_template['version'].get('mjml')
        dst_html = dst_template['version']['template']
        create_backup_version(dst_domain, dst_name, dst_html, dst_engine, dst_mjml)

        print(f"  Updating initial version...")
        result = create_template_version(dst_domain, dst_name, template_html, engine, mjml)
        if result:
            # Save destination to audit trail after successful copy
            print(f"\nSaving destination audit trail...")
            save_audit_trail(dst_domain, dst_name, 'initial', template_html, mjml)
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
    force_update = '--force' in sys.argv
    args = [arg for arg in sys.argv[1:] if arg != '--force']

    if len(args) != 4:
        print('Usage:')
        print('  python3 mailgun-copy-template-cross-domain.py <src_domain> <src_template> <dst_domain> <dst_template> [--force]')
        print('')
        print('Options:')
        print('  --force  Skip destination template existence check and attempt update anyway')
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

    src_domain = args[0]
    src_name = args[1]
    dst_domain = args[2]
    dst_name = args[3]

    print(f"Cross-domain template copy:")
    print(f"  Source: {src_name} @ {src_domain}")
    print(f"  Destination: {dst_name} @ {dst_domain}")
    if force_update:
        print(f"  Mode: FORCE (skipping destination existence check)")
    print()

    if force_update:
        # Skip the existence check and go straight to update
        print(f"Fetching template '{src_name}' from '{src_domain}'...")
        src_template = get_template(src_domain, src_name)
        if not src_template:
            print(f"Source template '{src_name}' not found in domain '{src_domain}'.")
            exit(1)

        engine = src_template['version'].get('engine')
        mjml = src_template['version'].get('mjml')
        template_html = src_template['version']['template']
        src_version_tag = src_template['version'].get('tag', 'active')

        print(f"  Engine: {engine if engine else 'none'}")
        print(f"  MJML: {len(mjml) if mjml else 0} chars")
        print(f"  HTML: {len(template_html)} chars")

        # Save source to audit trail
        print(f"\nSaving source audit trail...")
        save_audit_trail(src_domain, src_name, src_version_tag, template_html, mjml)

        print(f"\n⚠️  FORCE mode: Attempting to update '{dst_name}' without checking if it exists...")

        # Try to create backup of destination (may fail if template doesn't exist)
        print(f"\nAttempting to backup destination template...")
        dst_template = get_template(dst_domain, dst_name)
        if dst_template:
            dst_engine = dst_template['version'].get('engine')
            dst_mjml = dst_template['version'].get('mjml')
            dst_html = dst_template['version']['template']
            create_backup_version(dst_domain, dst_name, dst_html, dst_engine, dst_mjml)
        else:
            print(f"  No existing template to backup")

        result = create_template_version(dst_domain, dst_name, template_html, engine, mjml)
        if result:
            # Save destination to audit trail after successful copy
            print(f"\nSaving destination audit trail...")
            save_audit_trail(dst_domain, dst_name, 'initial', template_html, mjml)
            print(f"\n✓ Successfully copied '{src_name}' from '{src_domain}' to '{dst_name}' in '{dst_domain}'")
            success = True
        else:
            success = False
    else:
        success = copy_template_cross_domain(src_domain, src_name, dst_domain, dst_name)

    exit(0 if success else 1)
