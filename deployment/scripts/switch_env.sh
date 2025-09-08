#!/bin/bash
# Environment switcher for Unix/Linux systems (EC2)

set -e

ENVIRONMENT=$1

if [ -z "$ENVIRONMENT" ]; then
    echo "❌ Usage: ./switch_env.sh [local|test|production]"
    exit 1
fi

if [ ! -f "deployment/environments/.env.$ENVIRONMENT" ]; then
    echo "❌ Environment file deployment/environments/.env.$ENVIRONMENT not found!"
    exit 1
fi

echo "🔄 Switching to $ENVIRONMENT environment..."

# Copy environment file
cp "deployment/environments/.env.$ENVIRONMENT" ".env"

# Create logs directory if needed
if [ "$ENVIRONMENT" != "local" ]; then
    sudo mkdir -p /var/log/precatorios
    sudo mkdir -p /var/www/precatorios/media
    sudo mkdir -p /var/www/precatorios/static
    sudo chown -R $USER:$USER /var/www/precatorios
fi

# Install/update requirements
#if [ -f "venv/bin/activate" ]; then
#    source venv/bin/activate
#else
#    python3 -m venv venv
#    source venv/bin/activate
#fi

pip install -r requirements.txt

# Run migrations
python manage.py migrate

echo "✅ Successfully switched to $ENVIRONMENT environment!"
echo "🚀 Current settings:"
python manage.py shell -c "
from django.conf import settings
print(f'Environment: {settings.ENVIRONMENT}')
print(f'Debug: {settings.DEBUG}')
print(f'Database: {settings.DATABASES[\"default\"][\"ENGINE\"]}')
print(f'Use S3: {getattr(settings, \"USE_S3\", False)}')
"
