.PHONY: help install copy publish list-templates-src list-templates-dst list-versions-src list-versions-dst

# Templates to publish (space-separated list)
TEMPLATES ?=

# Default target
help:
	@echo "Mailgun Template Copy - Available targets:"
	@echo ""
	@echo "  make install             - Install uv and dependencies"
	@echo "  make list-templates-src  - List all templates in source domain"
	@echo "  make list-templates-dst  - List all templates in target domain"
	@echo "  make copy                - Copy a single template with different names"
	@echo "  make publish             - Publish templates from source to target domain (same names)"
	@echo "  make list-versions-src   - List versions for specific templates in source domain"
	@echo "  make list-versions-dst   - List versions for specific templates in target domain"
	@echo ""
	@echo "Environment variables:"
	@echo "  MG_API_KEY         - Mailgun API Key (required)"
	@echo "  SRC_MG_DOMAIN      - Source Mailgun domain (required for cross-domain)"
	@echo "  TGT_MG_DOMAIN      - Target Mailgun domain (required for cross-domain)"
	@echo "  MG_MAIL_DOMAIN     - Domain for same-domain operations (required for copy)"
	@echo ""
	@echo "Template selection:"
	@echo "  TEMPLATES          - Space-separated list for publish/list-versions"
	@echo "  SRC_TEMPLATE       - Source template name for copy"
	@echo "  DST_TEMPLATE       - Destination template name for copy"
	@echo ""
	@echo "Examples:"
	@echo "  # List available templates"
	@echo "  make list-templates-src"
	@echo ""
	@echo "  # Copy template with different name (same domain)"
	@echo "  make copy SRC_TEMPLATE='remittance' DST_TEMPLATE='remittance-low'"
	@echo ""
	@echo "  # Copy template with different name (cross domain)"
	@echo "  make copy SRC_TEMPLATE='remittance' DST_TEMPLATE='remittance-v2'"
	@echo ""
	@echo "  # Publish template(s) with same names across domains"
	@echo "  make publish TEMPLATES='remittance'"
	@echo "  make publish TEMPLATES='remittance remittance-low'"
	@echo ""
	@echo "  # List versions for specific templates"
	@echo "  make list-versions-src TEMPLATES='remittance'"

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

# List templates in source domain
list-templates-src: check-env
	@echo "Templates in $(SRC_MG_DOMAIN):"
	@export MG_MAIL_DOMAIN="$(SRC_MG_DOMAIN)" && \
	uv run mailgun-list-templates.py

# List templates in target domain
list-templates-dst: check-env
	@echo "Templates in $(TGT_MG_DOMAIN):"
	@export MG_MAIL_DOMAIN="$(TGT_MG_DOMAIN)" && \
	uv run mailgun-list-templates.py

# Copy a single template with different names (same or cross domain)
copy:
	@test -n "$(MG_API_KEY)" || (echo "Error: MG_API_KEY not set" && exit 1)
	@test -n "$(SRC_TEMPLATE)" || (echo "Error: SRC_TEMPLATE not set" && exit 1)
	@test -n "$(DST_TEMPLATE)" || (echo "Error: DST_TEMPLATE not set" && exit 1)
	@if [ -n "$(SRC_MG_DOMAIN)" ] && [ -n "$(TGT_MG_DOMAIN)" ]; then \
		echo "Copying '$(SRC_TEMPLATE)' from $(SRC_MG_DOMAIN) to '$(DST_TEMPLATE)' in $(TGT_MG_DOMAIN)..."; \
		uv run mailgun-copy-template-cross-domain.py \
			"$(SRC_MG_DOMAIN)" "$(SRC_TEMPLATE)" \
			"$(TGT_MG_DOMAIN)" "$(DST_TEMPLATE)"; \
	elif [ -n "$(MG_MAIL_DOMAIN)" ]; then \
		echo "Copying '$(SRC_TEMPLATE)' to '$(DST_TEMPLATE)' in $(MG_MAIL_DOMAIN)..."; \
		uv run mailgun-copy-template.py "$(SRC_TEMPLATE)" "$(DST_TEMPLATE)"; \
	else \
		echo "Error: Either MG_MAIL_DOMAIN or both SRC_MG_DOMAIN and TGT_MG_DOMAIN must be set"; \
		exit 1; \
	fi

# Publish templates from source to target domain (same names)
publish: check-env
	@test -n "$(TEMPLATES)" || (echo "Error: TEMPLATES not set. Specify template names to publish." && exit 1)
	@echo "Publishing templates from $(SRC_MG_DOMAIN) to $(TGT_MG_DOMAIN)..."
	@echo ""
	@for template in $(TEMPLATES); do \
		echo "Publishing $$template..."; \
		uv run mailgun-copy-template-cross-domain.py \
			"$(SRC_MG_DOMAIN)" "$$template" \
			"$(TGT_MG_DOMAIN)" "$$template" || exit 1; \
		echo ""; \
	done
	@echo "✓ All templates published successfully"

# List versions in source domain
list-versions-src: check-env
	@test -n "$(TEMPLATES)" || (echo "Error: TEMPLATES not set. Specify template names." && exit 1)
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
	@test -n "$(TEMPLATES)" || (echo "Error: TEMPLATES not set. Specify template names." && exit 1)
	@echo "Listing versions in $(TGT_MG_DOMAIN)..."
	@echo ""
	@for template in $(TEMPLATES); do \
		echo "Template: $$template"; \
		export MG_MAIL_DOMAIN="$(TGT_MG_DOMAIN)" && \
		uv run mailgun-copy-template.py list-versions "$$template"; \
		echo ""; \
	done
