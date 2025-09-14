# GitHub Copilot Instructions for Precatórios Management System

## Project Overview

A Django-based Brazilian legal document management system for precatórios (court-ordered payments from government entities). The system handles complex relationships between Precatórios, Clientes, Alvarás, and Requerimentos with multi-environment deployment and AWS S3 integration.

## Key Architecture Concepts

### Multi-Environment Configuration
- **Local**: Windows + SQLite + local file storage (hardcoded settings)
- **Test**: EC2 Ubuntu + PostgreSQL + AWS S3 (env variables)
- **Production**: EC2 Ubuntu + PostgreSQL + AWS S3 + SSL (env variables)

Environment detection via `ENVIRONMENT` variable in `settings.py`. Local environment uses hardcoded values for zero-config development. Always use `deployment/scripts/switch_env.bat local` for local development.

### Core Domain Models
- **Precatorio**: Primary legal document (PK: CNJ number). Contains financial values and payment statuses
- **Cliente**: Individual/company with rights to payments (PK: CPF/CNPJ)
- **Alvara**: Payment authorization linking Cliente to Precatorio
- **Requerimento**: Legal requests for special processing

**Critical Validation**: Clientes must be linked to Precatórios via many-to-many relationship before creating Alvarás/Requerimentos. Both models validate this in `clean()`.

### Visual Type System
- **Tipo**: Categorizes Precatórios with color coding
- **TipoDiligencia**: Categorizes diligence tasks with visual styling
- **PedidoRequerimento**: Defines request types for Requerimentos
- **Fase/FaseHonorariosContratuais**: Track document phases with color coding

All type models follow pattern: nome (unique), cor (hex), ordem (sorting), ativa/ativo (soft delete).

### File Storage Architecture
Custom storage package in `precapp/storage/` handles large files (50MB limit):
- Local: Regular Django file handling
- Production: AWS S3 with multipart upload for files >25MB
- Signed URLs for secure downloads with 1-hour expiration
- Environment-specific S3 folder structure (`media/test/`, `media/production/`)

## Development Conventions

### Form Patterns
All forms inherit Bootstrap styling and use Brazilian number formatting. Key patterns:
```python
# Brazilian monetary formatting (always in views/templates, never in models)
valor_formatado = f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# Choice fields with empty option
field = forms.ModelChoiceField(queryset=Model.objects.filter(ativa=True), empty_label="Selecione...")

# Date widgets with Brazilian format
data = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
```

### Validation Strategy
- Model `clean()` methods for business rules (especially relationship validation)
- Form validation for user input formatting
- `full_clean()` called in model `save()` to ensure validation runs
- ValidationError with field-specific error dictionaries

### Template System
Base template uses Bootstrap 5.3 with custom CSS. Key patterns:
- Breadcrumb navigation in all detail pages
- Color-coded badges using model.cor field
- Modal confirmations for delete operations
- Toast notifications for user feedback

### Testing Structure
Comprehensive test suite in `precapp/tests/`:
```
tests/
├── test_models.py           # Model validation, business logic (4000+ lines)
├── test_forms.py           # Form validation, widgets
├── test_edge_cases.py      # Boundary conditions, error cases  
├── views/                  # Specialized view testing
│   └── test_tipo_views.py  # CRUD operations, permissions
└── test_s3_storage.py      # Storage backend testing
```

Always run `python manage.py test` before committing. Tests use factories for data creation.

## Critical Development Commands

### Environment Management
```bash
# Switch to local (Windows)
deployment\scripts\switch_env.bat local

# Validate storage configuration
python manage.py validate_storage

# Create admin user
python manage.py create_admin

# Import Excel data
python manage.py import_excel path/to/file.xlsx
```

### Database Operations
```bash
# Make migrations (always review before applying)
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Check for issues
python manage.py check
```

### File Upload Testing
```bash
# Test S3 configuration
python manage.py validate_storage --show-config

# Run storage tests
python manage.py test precapp.tests.test_s3_storage -v 2
```

## Common Patterns

### Model Creation
1. Add model to `models.py` with comprehensive docstring
2. Create/update forms in `forms.py` with Bootstrap styling
3. Add views (list, create, detail, edit, delete) following existing patterns
4. Create templates using base template inheritance
5. Add URL patterns to `urls.py`
6. Write comprehensive tests in appropriate test file
7. Create migration and test in clean database

### File Handling
- Always validate file size (50MB limit) and type in forms
- Use `precapp.storage.utils.handle_large_file_download()` for downloads
- Never store files during testing (use cleanup in test tearDown)

### Error Handling
- Use Django messages framework for user feedback
- Log errors to `django.log` in production environments
- Return meaningful HTTP status codes (404, 403, etc.)
- Validate user permissions with `@login_required` decorator

## Deployment Notes

### Local Development
- No environment variables needed
- SQLite database auto-created
- Files stored in `media/` directory
- Debug mode always enabled

### Production Deployment
- Use `deployment/scripts/deploy_production.sh` for full setup
- Requires PostgreSQL database and S3 bucket configuration
- SSL/HTTPS enforced with Let's Encrypt
- Static files served by Nginx, media files by S3
- Comprehensive logging and monitoring setup

## Important: Never hardcode credentials or modify the environment-specific configuration logic in `settings.py`. The multi-environment system is carefully designed to work across Windows development and Linux production.