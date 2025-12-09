## mailgun-copy-template

Copy Mailgun email templates within a domain or across domains. Supports both HTML editor and Visual Builder templates.

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for Python dependency management:

```bash
# Install uv
# Option 1: Using Homebrew (macOS/Linux)
brew install uv

# Option 2: Using the installer script
curl -LsSf https://astral.sh/uv/install.sh | sh

# Dependencies will be automatically managed when running scripts with 'uv run'
```

## Environment Variables

```bash
MG_API_KEY='xxxxxxxxxx'                     # Mailgun API Key (required)
MG_MAIL_DOMAIN='mg.sample.com'              # Domain for single-domain operations (optional)
SRC_MG_DOMAIN='sandbox.mailgun.org'         # Source domain for Makefile operations (optional)
TGT_MG_DOMAIN='mg.example.com'              # Target domain for Makefile operations (optional)
MG_BASE_URL='https://api.mailgun.net/v3'    # Mailgun API base URL (optional, defaults shown)
```

## Quick Start (Using Makefile)

The Makefile provides convenient commands for common operations:

```bash
# Set environment variables
export MG_API_KEY='your-api-key'
export SRC_MG_DOMAIN='sandbox647641198e804fa69bdaccdeb73f5e46.mailgun.org'
export TGT_MG_DOMAIN='mg.maestropower.co.nz'

# List available templates
make list-templates-src
make list-templates-dst

# Copy a single template with different names
make copy SRC_TEMPLATE='remittance' DST_TEMPLATE='remittance-low'

# Publish template(s) to another domain (same names)
make publish TEMPLATES='remittance'
make publish TEMPLATES='remittance remittance-low'

# List template versions
make list-versions-src TEMPLATES='remittance'
make list-versions-dst TEMPLATES='remittance remittance-low'

# See all available targets
make help
```

## Usage

### Same-Domain Copy

Copy templates within the same domain:

```bash
# Copy template within domain specified by MG_MAIL_DOMAIN
uv run mailgun-copy-template.py [source] [destination]

# Example
export MG_MAIL_DOMAIN='mg.maestropower.co.nz'
uv run mailgun-copy-template.py remittance remittance-low

# List template versions
uv run mailgun-copy-template.py list-versions [template_name]
```

### Cross-Domain Copy

Copy templates between different Mailgun domains:

```bash
uv run mailgun-copy-template-cross-domain.py [src_domain] [src_template] [dst_domain] [dst_template]

# Example
uv run mailgun-copy-template-cross-domain.py \
  sandbox647641198e804fa69bdaccdeb73f5e46.mailgun.org remittance \
  mg.maestropower.co.nz remittance
```

## Copying Visual Builder Templates

**Important:** To maintain the "Visual Builder" type, you must create destination templates through the Mailgun UI first.

### Why?

Mailgun uses an internal `createdBy: dnd` field to mark templates created with the Visual Builder. This field cannot be set via the API, so templates created programmatically will always show as "HTML editor" type in the UI, even if they contain all the Visual Builder (MJML) data.

### Workflow:

1. **Create empty template(s) in Mailgun UI:**
   - Go to Mailgun dashboard
   - Select the destination domain
   - Navigate to Templates
   - Click "Create message template"
   - Select **"Visual builder"** (critical for preserving type)
   - Give it the destination name (e.g., `remittance-low`)
   - Save the empty template

2. **Run the copy script:**
   ```bash
   # Same domain
   uv run mailgun-copy-template.py remittance remittance-low

   # Cross domain
   uv run mailgun-copy-template-cross-domain.py \
     sandbox.mailgun.org remittance \
     mg.example.com remittance
   ```

### Script Behavior:

- **Detects Visual Builder templates:** Checks for `createdBy: dnd` in source template
- **Warns if mismatch:** Prompts you if copying DND to non-DND template
- **Copies all data:** Includes `template` (HTML), `mjml` (Visual Builder structure), and `engine` fields
- **Updates existing:** Uses PUT to `/versions/initial` to overwrite existing templates
- **Creates new:** Uses POST if destination template doesn't exist (will be "HTML editor" type)

## How It Works

### Same-Domain Script (`mailgun-copy-template.py`)

1. Fetches source template from `MG_MAIL_DOMAIN`
2. Checks if destination exists
3. If exists: Updates the `initial` version via PUT
4. If not: Creates new template + initial version via POST

### Cross-Domain Script (`mailgun-copy-template-cross-domain.py`)

1. Fetches source template from source domain
2. Checks if destination exists in destination domain
3. If exists: Updates the `initial` version via PUT
4. If not: Prompts you to create it in Mailgun UI first (preserves Visual Builder type)

### What Gets Copied:

- **HTML template:** The rendered email HTML
- **MJML structure:** The Visual Builder JSON structure (if present)
- **Engine:** Template engine (e.g., `handlebars`)
- **NOT copied:** `createdBy` field (cannot be set via API)

## Notes

- The cross-domain script requires your API key to have access to both domains
- Templates created via API will show as "HTML editor" type regardless of MJML content
- Visual Builder templates require the two-step process (UI creation + script copy) to preserve type
- The `initial` version tag is always used/updated when copying
