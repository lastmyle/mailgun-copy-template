## mailgun-copy-template

copy a mailgun email template from one name to another within an account

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

### Command:
```bash
python3 mailgun-copy-template.py [src] [dest]
```
