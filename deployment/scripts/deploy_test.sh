#!/bin/bash
# Comprehensive deployment script for TEST environment on EC2
# Based on django_build.sh logic with multi-environment support

set -e

echo "🚀 Deploying Django TEST environment on EC2 with Nginx + Gunicorn..."

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration variables
PROJECT_NAME="precatorios"
PROJECT_DIR="/var/www/${PROJECT_NAME}"
REPO_URL="https://github.com/thsteixeira/precatorios.git"
NGINX_SITE_NAME="${PROJECT_NAME}_test"
GUNICORN_SERVICE_NAME="gunicorn_${PROJECT_NAME}_test"
DOMAIN_OR_IP="${TEST_DOMAIN_OR_IP:-54.191.130.149}"  # Use environment variable or default

print_status "Starting TEST environment deployment..."

# 1. Update system packages
print_status "Updating system packages..."
sudo apt update -y
#sudo apt upgrade -y

# 2. Install required system packages
print_status "Installing system dependencies..."
sudo apt install -y \
    python3-pip \
    python3-dev \
    git \
    nginx \
    postgresql-client \
    awscli \
    supervisor \
    curl \
    software-properties-common

# 3. Create application directory structure
print_status "Setting up directory structure..."
sudo mkdir -p ${PROJECT_DIR}
sudo mkdir -p /var/log/${PROJECT_NAME}
sudo mkdir -p /var/www/${PROJECT_NAME}/static
# Create media directory as fallback (even if using S3)
sudo mkdir -p /var/www/${PROJECT_NAME}/media

# Set proper ownership
sudo chown -R $USER:www-data ${PROJECT_DIR}
sudo chown -R $USER:www-data /var/log/${PROJECT_NAME}
sudo chmod -R 775 ${PROJECT_DIR}
sudo chmod -R 775 /var/log/${PROJECT_NAME}

# 4. Clone or update repository
print_status "Setting up project repository..."
if [ -d "${PROJECT_DIR}/.git" ]; then
    print_status "Repository exists, updating..."
    cd ${PROJECT_DIR}
    git pull origin main
else
    print_status "Cloning repository..."
    sudo rm -rf ${PROJECT_DIR}/*
    git clone ${REPO_URL} ${PROJECT_DIR}
    cd ${PROJECT_DIR}
fi

# 5. Create and activate virtual environment
#print_status "Setting up Python virtual environment..."
#python3 -m venv venv
#source venv/bin/activate

# 6. Upgrade pip and install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install gunicorn
pip install -r requirements.txt

# 7. Setup environment configuration
print_status "Configuring environment settings..."
cp deployment/environments/.env.test .env

print_warning "Environment configuration copied. Please update .env with your actual credentials:"
echo "   - DATABASE_HOST (PostgreSQL EC2 private IP)"
echo "   - DATABASE_PASSWORD"
echo "   - SECRET_KEY"
echo "   - ALLOWED_HOSTS"
echo "   - AWS_ACCESS_KEY_ID (for S3)"
echo "   - AWS_SECRET_ACCESS_KEY (for S3)"
echo "   - AWS_STORAGE_BUCKET_NAME (test bucket name)"

# Wait for user confirmation
read -p "Press Enter after updating .env file with your credentials..."

# 8. Test environment configuration
print_status "Testing Django configuration..."
python manage.py check

# 9. Test database connection
print_status "Testing database connection..."
python manage.py check --database default

# 10. Test S3 connection (if configured)
print_status "Testing S3 bucket access..."
python manage.py shell -c "
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os

if getattr(settings, 'USE_S3', False):
    try:
        file = ContentFile(b'Test content from TEST environment')
        name = default_storage.save('test-file.txt', file)
        print(f'✅ S3 test successful: {name}')
        url = default_storage.url(name)
        print(f'✅ File URL: {url}')
        default_storage.delete(name)
        print('✅ File cleanup successful')
    except Exception as e:
        print(f'❌ S3 test failed: {e}')
        print('🔧 Continuing with local media storage as fallback')
else:
    print('📁 Using local filesystem for media storage')
"

# 11. Run database migrations
print_status "Running database migrations..."
python manage.py migrate

# 12. Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --noinput

# 13. Create superuser (if needed)
print_status "Setting up thiago user..."
echo "Creating superuser account..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='thiago').exists():
    print('Creating thiago user...')
    import os
    User.objects.create_superuser('thiago', 'thiago@test.com', os.environ.get('ADMIN_PASSWORD', 'admin123'))
    print('Thiago user created successfully')
else:
    print('Thiago user already exists')
"

# 14. Configure Gunicorn service
print_status "Configuring Gunicorn service..."
sudo tee /etc/systemd/system/${GUNICORN_SERVICE_NAME}.service > /dev/null << EOF
[Unit]
Description=Gunicorn daemon for Django ${PROJECT_NAME} TEST environment
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=${PROJECT_DIR}
Environment="PATH=${PROJECT_DIR}/venv/bin"
ExecStart=${PROJECT_DIR}/venv/bin/gunicorn \\
    --workers 3 \\
    --bind unix:/tmp/${PROJECT_NAME}_test.sock \\
    --timeout 120 \\
    --access-logfile /var/log/${PROJECT_NAME}/gunicorn_access.log \\
    --error-logfile /var/log/${PROJECT_NAME}/gunicorn_error.log \\
    --log-level info \\
    ${PROJECT_NAME}.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 15. Start and enable Gunicorn service
print_status "Starting Gunicorn service..."
sudo systemctl daemon-reload
sudo systemctl start ${GUNICORN_SERVICE_NAME}
sudo systemctl enable ${GUNICORN_SERVICE_NAME}

# Check Gunicorn status
if sudo systemctl is-active --quiet ${GUNICORN_SERVICE_NAME}; then
    print_success "Gunicorn service started successfully"
else
    print_error "Gunicorn service failed to start"
    sudo systemctl status ${GUNICORN_SERVICE_NAME}
    exit 1
fi

# 16. Configure Nginx
print_status "Configuring Nginx..."

# Add server_names_hash_bucket_size to main nginx.conf if not already present
print_status "Configuring Nginx main settings..."
if ! grep -q "server_names_hash_bucket_size" /etc/nginx/nginx.conf; then
    print_status "Adding server_names_hash_bucket_size configuration..."
    sudo sed -i '/http {/a\    server_names_hash_bucket_size 128;' /etc/nginx/nginx.conf
    print_success "Added server_names_hash_bucket_size 128 to nginx.conf"
else
    print_status "server_names_hash_bucket_size already configured"
fi

# Check if using S3 for media files
USE_S3=$(python manage.py shell -c "
from django.conf import settings
print(getattr(settings, 'USE_S3', False))
" | tail -1)

if [ "$USE_S3" = "True" ]; then
    print_status "Configuring Nginx for S3 media storage..."
    MEDIA_LOCATION_BLOCK=""
else
    print_status "Configuring Nginx for local media storage..."
    MEDIA_LOCATION_BLOCK="
    # Media files (local storage fallback)
    location /media/ {
        alias /var/www/${PROJECT_NAME}/media/;
        expires 1y;
        add_header Cache-Control \"public\";
    }"
fi

sudo tee /etc/nginx/sites-available/${NGINX_SITE_NAME} > /dev/null << EOF
server {
    listen 80;
    server_name ${DOMAIN_OR_IP};
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # Static files (always served locally by Nginx for performance)
    location /static/ {
        alias /var/www/${PROJECT_NAME}/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    ${MEDIA_LOCATION_BLOCK}
    
    # Main application
    location / {
        proxy_pass http://unix:/tmp/${PROJECT_NAME}_test.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
        proxy_buffering off;
    }
    
    # Health check endpoint
    location /health/ {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# 17. Enable Nginx site
print_status "Enabling Nginx site..."
sudo ln -sf /etc/nginx/sites-available/${NGINX_SITE_NAME} /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default  # Remove default site

# Test Nginx configuration
sudo nginx -t
if [ $? -eq 0 ]; then
    print_success "Nginx configuration is valid"
    sudo systemctl restart nginx
    sudo systemctl enable nginx
else
    print_error "Nginx configuration failed"
    exit 1
fi

# 18. Set up log rotation
print_status "Setting up log rotation..."
sudo tee /etc/logrotate.d/${PROJECT_NAME} > /dev/null << EOF
/var/log/${PROJECT_NAME}/*.log {
    daily
    missingok
    rotate 14
    compress
    notifempty
    create 0644 $USER www-data
    postrotate
        systemctl reload ${GUNICORN_SERVICE_NAME}
    endscript
}
EOF

# 19. Final system checks
print_status "Running final system checks..."

# Check services status
services=("nginx" "${GUNICORN_SERVICE_NAME}")
for service in "${services[@]}"; do
    if sudo systemctl is-active --quiet $service; then
        print_success "$service is running"
    else
        print_error "$service is not running"
        sudo systemctl status $service
    fi
done

# Test Django application
print_status "Testing Django application..."
python manage.py check

# Test HTTP response
print_status "Testing HTTP response..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/)
if [ "$response" = "200" ]; then
    print_success "Application is responding correctly (HTTP $response)"
else
    print_warning "Application response: HTTP $response"
fi

# 20. Display deployment summary
echo ""
print_success "🎉 TEST environment deployment completed successfully!"
echo ""
echo "📋 Deployment Summary:"
echo "   • Project Directory: ${PROJECT_DIR}"
echo "   • Log Directory: /var/log/${PROJECT_NAME}"
echo "   • Gunicorn Service: ${GUNICORN_SERVICE_NAME}"
echo "   • Nginx Site: ${NGINX_SITE_NAME}"
echo "   • Domain/IP: ${DOMAIN_OR_IP}"
echo ""
echo "🔧 Service Management Commands:"
echo "   • Restart Gunicorn: sudo systemctl restart ${GUNICORN_SERVICE_NAME}"
echo "   • Restart Nginx: sudo systemctl restart nginx"
echo "   • View logs: sudo journalctl -u ${GUNICORN_SERVICE_NAME} -f"
echo "   • Check status: sudo systemctl status ${GUNICORN_SERVICE_NAME}"
echo ""
echo "🌐 Access your application:"
echo "   • Web: http://${DOMAIN_OR_IP}/"
echo "   • Admin: http://${DOMAIN_OR_IP}/admin/"
echo ""
echo "📝 Next Steps:"
echo "   1. Set up SSL certificates (Let's Encrypt recommended)"
echo "   2. Configure domain DNS (if using custom domain)"
echo "   3. Set up monitoring and backups"
echo "   4. Review and secure environment variables"
echo "   5. Test all application features including file uploads"
echo ""
print_warning "Remember to:"
echo "   • Keep your .env file secure and backed up"
echo "   • Regularly update dependencies and system packages"
echo "   • Monitor application logs and performance"
