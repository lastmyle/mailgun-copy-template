.PHONY: help install copy-remittance copy-remittance-low copy-all list-versions-src list-versions-dst

# Default target
help:
	@echo "Mailgun Template Copy - Available targets:"
	@echo ""
	@echo "  make install              - Install uv and dependencies"
	@echo "  make copy-remittance      - Copy remittance template from source to target domain"
	@echo "  make copy-remittance-low  - Copy remittance-low template from source to target domain"
	@echo "  make copy-all             - Copy both templates"
	@echo "  make list-versions-src    - List versions in source domain"
	@echo "  make list-versions-dst    - List versions in target domain"
	@echo ""
	@echo "Environment variables required:"
	@echo "  MG_API_KEY         - Mailgun API Key"
	@echo "  SRC_MG_DOMAIN      - Source Mailgun domain"
	@echo "  TGT_MG_DOMAIN      - Target Mailgun domain"
	@echo ""
	@echo "Example:"
	@echo "  export MG_API_KEY='your-api-key'"
	@echo "  export SRC_MG_DOMAIN='sandbox647641198e804fa69bdaccdeb73f5e46.mailgun.org'"
	@echo "  export TGT_MG_DOMAIN='mg.maestropower.co.nz'"
	@echo "  make copy-all"

# Install uv if not present
install:
	@command -v uv >/dev/null 2>&1 || { \
		echo "Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	}
	@echo "✓ uv is installed"

# Check required environment variables
check-env:
	@test -n "$(MG_API_KEY)" || (echo "Error: MG_API_KEY not set" && exit 1)
	@test -n "$(SRC_MG_DOMAIN)" || (echo "Error: SRC_MG_DOMAIN not set" && exit 1)
	@test -n "$(TGT_MG_DOMAIN)" || (echo "Error: TGT_MG_DOMAIN not set" && exit 1)
	@echo "✓ Environment variables verified"

# Copy remittance template
copy-remittance: check-env
	@echo "Copying remittance template..."
	@echo "  From: $(SRC_MG_DOMAIN)"
	@echo "  To:   $(TGT_MG_DOMAIN)"
	@uv run mailgun-copy-template-cross-domain.py \
		"$(SRC_MG_DOMAIN)" remittance \
		"$(TGT_MG_DOMAIN)" remittance

# Copy remittance-low template
copy-remittance-low: check-env
	@echo "Copying remittance-low template..."
	@echo "  From: $(SRC_MG_DOMAIN)"
	@echo "  To:   $(TGT_MG_DOMAIN)"
	@uv run mailgun-copy-template-cross-domain.py \
		"$(SRC_MG_DOMAIN)" remittance-low \
		"$(TGT_MG_DOMAIN)" remittance-low

# Copy all templates
copy-all: check-env copy-remittance copy-remittance-low
	@echo ""
	@echo "✓ All templates copied successfully"

# List versions in source domain
list-versions-src: check-env
	@echo "Listing versions in $(SRC_MG_DOMAIN)..."
	@export MG_MAIL_DOMAIN="$(SRC_MG_DOMAIN)" && \
	uv run mailgun-copy-template.py list-versions remittance
	@echo ""
	@export MG_MAIL_DOMAIN="$(SRC_MG_DOMAIN)" && \
	uv run mailgun-copy-template.py list-versions remittance-low

# List versions in target domain
list-versions-dst: check-env
	@echo "Listing versions in $(TGT_MG_DOMAIN)..."
	@export MG_MAIL_DOMAIN="$(TGT_MG_DOMAIN)" && \
	uv run mailgun-copy-template.py list-versions remittance
	@echo ""
	@export MG_MAIL_DOMAIN="$(TGT_MG_DOMAIN)" && \
	uv run mailgun-copy-template.py list-versions remittance-low
