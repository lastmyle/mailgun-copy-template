## mailgun-copy-template

Copy a Mailgun email template from one name to another within an account. Supports both HTML editor and Visual Builder templates.

### Usage:
 - Install python dependencies
 - Set required environment variables
 - Execute python script

### Environment Variables:
```bash
MG_MAIL_DOMAIN='mg.sample.com'              # Domain name under which existing template exists
MG_API_KEY='xxxxxxxxxx'                     # Mailgun API Key
MG_BASE_URL='https://api.mailgun.net/v3'    # Mailgun API base URL; defaults to https://api.mailgun.net/v3
```

### Commands:

#### Copy template to a new name:
```bash
uv run mailgun-copy-template.py [src] [dest]
```

#### Copy template to an existing template:
```bash
uv run mailgun-copy-template.py [src] [dest]
```

#### List template versions:
```bash
uv run mailgun-copy-template.py list-versions [template_name]
```

### Copying Visual Builder Templates

To maintain the "Visual Builder" type when copying templates:

1. **Create an empty template in Mailgun UI:**
   - Go to Mailgun dashboard
   - Navigate to Templates
   - Click "Create message template"
   - Select "Visual builder"
   - Give it the destination name (e.g., `remittance-low`)
   - Save the empty template

2. **Copy content using the script:**
   ```bash
   uv run mailgun-copy-template.py remittance remittance-low
   ```

This preserves the Visual Builder type because the template was created through the Mailgun UI with the `createdBy: dnd` field. Templates created directly via API will show as "HTML editor" type even if they contain MJML data.

### How it works:

- **New templates:** Creates a new template with the copied content
- **Existing templates:** Updates the "initial" version of the existing template
- **Visual Builder:** Copies both the rendered HTML (`template`) and MJML structure (`mjml`)
- **Engine:** Preserves the template engine (e.g., `handlebars`)
