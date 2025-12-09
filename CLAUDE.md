# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python utility for copying Mailgun email templates within the same domain or across different domains. It handles both HTML editor templates and Visual Builder templates (MJML-based), with special logic to preserve template types when possible.

## Core Scripts

The project consists of three main standalone Python scripts:

1. **mailgun-copy-template.py** - Same-domain template copying
2. **mailgun-copy-template-cross-domain.py** - Cross-domain template copying
3. **mailgun-list-versions.py** - List all versions of a template

Each script is self-contained and runnable via `uv run`.

## Running Scripts

All scripts use `uv` for Python dependency management:

```bash
# Same-domain copy
uv run mailgun-copy-template.py [source] [destination]
uv run mailgun-copy-template.py list-versions [template_name]

# Cross-domain copy
uv run mailgun-copy-template-cross-domain.py [src_domain] [src_template] [dst_domain] [dst_template]

# List versions
uv run mailgun-list-versions.py [template_name]
```

## Environment Variables

```bash
MG_API_KEY='xxx'           # Required for all scripts
MG_MAIL_DOMAIN='mg.x.com'  # Required for same-domain scripts only
MG_BASE_URL='...'          # Optional, defaults to https://api.mailgun.net/v3
```

## Visual Builder Templates Architecture

**Critical concept:** Mailgun templates have an internal `createdBy` field that determines their UI type:
- `createdBy: dnd` → Shows as "Visual Builder" in Mailgun UI
- Any other value or missing → Shows as "HTML editor" in Mailgun UI

**Key constraint:** The `createdBy` field CANNOT be set via the Mailgun API. Therefore:

1. Templates created programmatically via API will ALWAYS show as "HTML editor" type
2. To preserve Visual Builder type, destination templates MUST be created manually in Mailgun UI first
3. Scripts can then UPDATE the content of pre-existing templates via PUT to `/versions/initial`

### Script Logic for Visual Builder

Both copy scripts implement this workflow:

1. **Fetch source template** with `?active=yes` parameter
2. **Check if destination exists** by attempting to fetch it
3. **If destination exists:**
   - Check `createdBy` field on both source and destination
   - Warn user if copying Visual Builder to non-Visual Builder template
   - Update via PUT to `/templates/{name}/versions/initial` endpoint
   - Include `template` (HTML), `mjml` (MJML structure), and `engine` fields
4. **If destination doesn't exist:**
   - For same-domain script: Creates new template (will be "HTML editor" type)
   - For cross-domain script: Prompts user to create manually in UI first (preserves type)

### Data Being Copied

When copying templates, the scripts transfer:
- `template` - The rendered HTML output
- `mjml` - The MJML/Visual Builder structure (if present)
- `engine` - Template engine (e.g., "handlebars")
- NOT copied: `createdBy` field (cannot be set via API)

## Code Architecture

### Same-Domain Script (mailgun-copy-template.py)

Functions:
- `get_template(name)` - Fetch active template from MG_MAIL_DOMAIN
- `create_template(name, description, template, engine, mjml)` - Two-step creation: POST empty template, then POST initial version
- `get_template_versions(name)` - Fetch all versions of a template
- `print_template_versions_json(versions)` - Format version list output

Main logic at lines 74-127 handles both copy modes and list-versions command.

### Cross-Domain Script (mailgun-copy-template-cross-domain.py)

Functions:
- `get_template(domain, name)` - Fetch template from specified domain
- `create_template_version(domain, name, template_html, engine, mjml)` - Update existing template's initial version via PUT
- `copy_template_cross_domain(src_domain, src_name, dst_domain, dst_name)` - Main orchestration with Visual Builder detection and warnings

Key difference from same-domain script: Does NOT create new templates programmatically. Instead prompts user to create in UI first (lines 86-103).

### Visual Builder Detection

Both scripts check `template.get('createdBy') == 'dnd'` to detect Visual Builder templates and provide appropriate warnings/prompts to user.

Cross-domain script has more sophisticated handling:
- Lines 59-72: Warning when copying DND to non-DND existing template
- Lines 82-103: Detailed instructions when destination doesn't exist

## API Endpoints Used

- `GET /v3/{domain}/templates/{name}?active=yes` - Fetch active template version
- `POST /v3/{domain}/templates` - Create empty template
- `POST /v3/{domain}/templates/{name}/versions` - Create new version
- `PUT /v3/{domain}/templates/{name}/versions/initial` - Update existing version
- `GET /v3/{domain}/templates/{name}/versions` - List all versions

## Dependencies

Uses only `requests` library for HTTP calls. Project requires Python >=3.13.5 (per pyproject.toml).
