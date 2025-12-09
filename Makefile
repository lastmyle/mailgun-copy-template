.PHONY: help install copy list-versions-src list-versions-dst

# Templates to copy (space-separated list)
TEMPLATES ?= remittance remittance-low

# Default target
help:
	@echo "Mailgun Template Copy - Available targets:"
	@echo ""
	@echo "  make install           - Install uv and dependencies"
	@echo "  make copy              - Copy templates from source to target domain"
	@echo "  make list-versions-src - List versions in source domain"
	@echo "  make list-versions-dst - List versions in target domain"
	@echo ""
	@echo "Environment variables required:"
	@echo "  MG_API_KEY         - Mailgun API Key"
	@echo "  SRC_MG_DOMAIN      - Source Mailgun domain"
	@echo "  TGT_MG_DOMAIN      - Target Mailgun domain"
	@echo ""
	@echo "Template selection (optional):"
	@echo "  TEMPLATES          - Space-separated list of templates to copy"
	@echo "                       Default: remittance remittance-low"
	@echo ""
	@echo "Examples:"
	@echo "  # Copy all templates (default)"
	@echo "  make copy"
	@echo ""
	@echo "  # Copy specific template(s)"
	@echo "  make copy TEMPLATES='remittance'"
	@echo "  make copy TEMPLATES='remittance remittance-low'"
	@echo ""
	@echo "  # Full example with env vars"
	@echo "  export MG_API_KEY='your-api-key'"
	@echo "  export SRC_MG_DOMAIN='sandbox.mailgun.org'"
	@echo "  export TGT_MG_DOMAIN='mg.maestropower.co.nz'"
	@echo "  make copy"

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

# Copy templates
copy: check-env
	@echo "Copying templates from $(SRC_MG_DOMAIN) to $(TGT_MG_DOMAIN)..."
	@echo ""
	@for template in $(TEMPLATES); do \
		echo "Copying $$template..."; \
		uv run mailgun-copy-template-cross-domain.py \
			"$(SRC_MG_DOMAIN)" "$$template" \
			"$(TGT_MG_DOMAIN)" "$$template" || exit 1; \
		echo ""; \
	done
	@echo "✓ All templates copied successfully"

# List versions in source domain
list-versions-src: check-env
	@echo "Listing versions in $(SRC_MG_DOMAIN)..."
	@echo ""
	@for template in $(TEMPLATES); do \
		echo "Template: $$template"; \
		export MG_MAIL_DOMAIN="$(SRC_MG_DOMAIN)" && \
		uv run mailgun-copy-template.py list-versions "$$template"; \
		echo ""; \
	done

# List versions in target domain
list-versions-dst: check-env
	@echo "Listing versions in $(TGT_MG_DOMAIN)..."
	@echo ""
	@for template in $(TEMPLATES); do \
		echo "Template: $$template"; \
		export MG_MAIL_DOMAIN="$(TGT_MG_DOMAIN)" && \
		uv run mailgun-copy-template.py list-versions "$$template"; \
		echo ""; \
	done
