#!/bin/bash
# Comprehensive deployment script for PRODUCTION environment on EC2
# Based on django_build.sh logic with multi-environment and production-grade features

set -e

echo "🚀 Deploying Django PRODUCTION environment on EC2 with Nginx + Gunicorn..."

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
NGINX_SITE_NAME="${PROJECT_NAME}_production"
GUNICORN_SERVICE_NAME="gunicorn_${PROJECT_NAME}_production"

# Production server configuration (update these with your actual production values)
PRODUCTION_IP="44.242.204.124"  # From .env.production
PRODUCTION_DNS="ec2-44-242-204-124.us-west-2.compute.amazonaws.com"  # From .env.production
PRODUCTION_DOMAIN="henriqueteixeira.adv.br"  # From .env.production

# For backward compatibility, still support PRODUCTION_DOMAIN_OR_IP override
DOMAIN_OR_IP="${PRODUCTION_DOMAIN_OR_IP:-$PRODUCTION_DOMAIN}"

print_status "Starting PRODUCTION environment deployment..."
print_status "Production Server Configuration:"
echo "   • Production IP: ${PRODUCTION_IP}"
echo "   • Production DNS: ${PRODUCTION_DNS}"
echo "   • Production Domain: ${PRODUCTION_DOMAIN}"
echo "   • Nginx will respond to all three addresses"
echo ""
print_warning "⚠️  PRODUCTION DEPLOYMENT - Please ensure you have:"
echo "   • Valid SSL certificates ready"
echo "   • Production domain configured"
echo "   • Database backups completed"
echo "   • All credentials securely stored"
echo ""
read -p "Continue with production deployment? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_error "Production deployment cancelled."
    exit 1
fi

# 1. Update system packages
print_status "Updating system packages..."
sudo apt update -y
sudo apt upgrade -y

# 2. Install required system packages
print_status "Installing system dependencies..."
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    nginx \
    postgresql-client \
    awscli \
    supervisor \
    curl \
    software-properties-common \
    ufw \
    fail2ban \
    certbot \
    python3-certbot-nginx

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
#print_status "Setting up project repository..."
#if [ -d "${PROJECT_DIR}/.git" ]; then
#    print_status "Repository exists, updating..."
#    cd ${PROJECT_DIR}
#    git pull origin main
#else
#    print_status "Cloning repository..."
#    sudo rm -rf ${PROJECT_DIR}/*
#    git clone ${REPO_URL} ${PROJECT_DIR}
#    cd ${PROJECT_DIR}
#fi

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
cp deployment/environments/.env.production .env

print_warning "Environment configuration copied. Please update .env with your PRODUCTION credentials:"
echo "   - DATABASE_HOST (PostgreSQL EC2 private IP)"
echo "   - DATABASE_PASSWORD (secure production password)"
echo "   - SECRET_KEY (generate new secure key for production)"
echo "   - ALLOWED_HOSTS (your production domain)"
echo "   - AWS_ACCESS_KEY_ID (production AWS credentials)"
echo "   - AWS_SECRET_ACCESS_KEY (production AWS credentials)"
echo "   - AWS_STORAGE_BUCKET_NAME (production S3 bucket)"

# Wait for user confirmation
read -p "Press Enter after updating .env file with your PRODUCTION credentials..."

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
        file = ContentFile(b'Test content from PRODUCTION environment')
        name = default_storage.save('production-test-file.txt', file)
        print(f'✅ S3 test successful: {name}')
        url = default_storage.url(name)
        print(f'✅ File URL: {url}')
        default_storage.delete(name)
        print('✅ File cleanup successful')
    except Exception as e:
        print(f'❌ S3 test failed: {e}')
        print('🔧 You may need to review S3 configuration')
        exit(1)
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
print_status "Setting up admin user..."
echo "Creating superuser account for production..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    print('Creating admin user...')
    import os
    admin_password = os.environ.get('ADMIN_PASSWORD')
    if not admin_password:
        print('Please create admin user manually after deployment')
    else:
        User.objects.create_superuser('admin', 'admin@production.com', admin_password)
        print('Admin user created successfully')
else:
    print('Admin user already exists')
"

# 14. Configure Gunicorn service
print_status "Configuring Gunicorn service..."
sudo tee /etc/systemd/system/${GUNICORN_SERVICE_NAME}.service > /dev/null << EOF
[Unit]
Description=Gunicorn daemon for Django ${PROJECT_NAME} PRODUCTION environment
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=${PROJECT_DIR}
Environment="PATH=${PROJECT_DIR}/venv/bin"
ExecStart=${PROJECT_DIR}/venv/bin/gunicorn \\
    --workers 4 \\
    --bind unix:/tmp/${PROJECT_NAME}_production.sock \\
    --timeout 120 \\
    --keep-alive 5 \\
    --max-requests 1000 \\
    --max-requests-jitter 100 \\
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
# HTTP server (redirects to HTTPS)
server {
    listen 80;
    server_name ${PRODUCTION_IP} ${PRODUCTION_DNS} ${PRODUCTION_DOMAIN};
    return 301 https://\$server_name\$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name ${PRODUCTION_IP} ${PRODUCTION_DNS} ${PRODUCTION_DOMAIN};
    
    # SSL Configuration (will be updated by certbot)
    # ssl_certificate /etc/letsencrypt/live/${DOMAIN_OR_IP}/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/${DOMAIN_OR_IP}/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    # Static files (always served locally by Nginx for performance)
    location /static/ {
        alias /var/www/${PROJECT_NAME}/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        gzip on;
        gzip_types text/css application/javascript application/json;
    }
    ${MEDIA_LOCATION_BLOCK}
    
    # Main application
    location / {
        proxy_pass http://unix:/tmp/${PROJECT_NAME}_production.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
        proxy_buffering off;
        
        # Security
        proxy_hide_header X-Powered-By;
    }
    
    # Health check endpoint
    location /health/ {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
    
    # Deny access to sensitive files
    location ~ /\. {
        deny all;
    }
    
    location ~ /(\.env|\.git|requirements\.txt) {
        deny all;
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

# 18. Configure SSL with Let's Encrypt
print_status "Setting up SSL certificate..."
print_warning "Setting up SSL certificate with Let's Encrypt..."
echo "Available domains for SSL:"
echo "   • Production IP: ${PRODUCTION_IP} (IP addresses don't support SSL certificates)"
echo "   • Production DNS: ${PRODUCTION_DNS}"
echo "   • Production Domain: ${PRODUCTION_DOMAIN}"
echo ""
echo "Choose SSL setup option:"
echo "   1. SSL for domain only (${PRODUCTION_DOMAIN}) - RECOMMENDED"
echo "   2. SSL for all domains (${PRODUCTION_DNS} and ${PRODUCTION_DOMAIN})"
echo "   3. Skip SSL setup"
read -p "Enter choice (1/2/3): " ssl_choice

case $ssl_choice in
    1)
        echo "Setting up SSL for domain: ${PRODUCTION_DOMAIN}"
        sudo certbot --nginx -d ${PRODUCTION_DOMAIN} --non-interactive --agree-tos --email admin@${PRODUCTION_DOMAIN}
        ;;
    2)
        echo "Setting up SSL for multiple domains: ${PRODUCTION_DNS} and ${PRODUCTION_DOMAIN}"
        sudo certbot --nginx -d ${PRODUCTION_DNS} -d ${PRODUCTION_DOMAIN} --non-interactive --agree-tos --email admin@${PRODUCTION_DOMAIN}
        ;;
    3)
        print_warning "SSL setup skipped. Configure manually later."
        echo "Manual commands:"
        echo "   • Domain only: sudo certbot --nginx -d ${PRODUCTION_DOMAIN}"
        echo "   • Multiple domains: sudo certbot --nginx -d ${PRODUCTION_DNS} -d ${PRODUCTION_DOMAIN}"
        ;;
    *)
        print_warning "Invalid choice. SSL setup skipped."
        ;;
esac

if [ $? -eq 0 ] && [ "$ssl_choice" != "3" ]; then
    print_success "SSL certificate installed successfully"
else
    if [ "$ssl_choice" != "3" ]; then
        print_warning "SSL certificate installation failed. You can run it manually later:"
        echo "   • Domain only: sudo certbot --nginx -d ${PRODUCTION_DOMAIN}"
        echo "   • Multiple domains: sudo certbot --nginx -d ${PRODUCTION_DNS} -d ${PRODUCTION_DOMAIN}"
    fi
fi

# 19. Configure firewall
print_status "Configuring firewall..."
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw reload

# 20. Configure fail2ban
print_status "Configuring fail2ban..."
sudo tee /etc/fail2ban/jail.local > /dev/null << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
EOF

sudo systemctl restart fail2ban
sudo systemctl enable fail2ban

# 21. Set up log rotation
print_status "Setting up log rotation..."
sudo tee /etc/logrotate.d/${PROJECT_NAME} > /dev/null << EOF
/var/log/${PROJECT_NAME}/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 0644 $USER www-data
    postrotate
        systemctl reload ${GUNICORN_SERVICE_NAME}
    endscript
}
EOF

# 22. Set up automated backups (basic script)
print_status "Setting up backup script..."
sudo tee /usr/local/bin/backup_${PROJECT_NAME}.sh > /dev/null << 'EOF'
#!/bin/bash
# Basic backup script for production
BACKUP_DIR="/var/backups/precatorios"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p ${BACKUP_DIR}

# Backup database (adjust for your database)
# pg_dump your_db > ${BACKUP_DIR}/db_backup_${DATE}.sql

# Backup media files (if not using S3)
# tar -czf ${BACKUP_DIR}/media_backup_${DATE}.tar.gz /var/www/precatorios/media/

# Backup environment file
cp /var/www/precatorios/.env ${BACKUP_DIR}/env_backup_${DATE}

# Clean old backups (keep 7 days)
find ${BACKUP_DIR} -type f -mtime +7 -delete

echo "Backup completed: ${DATE}"
EOF

sudo chmod +x /usr/local/bin/backup_${PROJECT_NAME}.sh

# Add to crontab for daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup_${PROJECT_NAME}.sh") | crontab -

# 23. Final system checks
print_status "Running final system checks..."

# Check services status
services=("nginx" "${GUNICORN_SERVICE_NAME}" "fail2ban")
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

# Test HTTPS response (if SSL was configured)
print_status "Testing HTTPS response..."
response=$(curl -s -o /dev/null -w "%{http_code}" https://localhost/ --insecure 2>/dev/null || echo "000")
if [ "$response" = "200" ]; then
    print_success "Application is responding correctly (HTTPS $response)"
elif [ "$response" = "000" ]; then
    # Try HTTP if HTTPS failed
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/)
    if [ "$response" = "200" ] || [ "$response" = "301" ]; then
        print_success "Application is responding correctly (HTTP $response)"
    else
        print_warning "Application response: HTTP $response"
    fi
else
    print_warning "Application response: HTTPS $response"
fi

# 24. Display deployment summary
echo ""
print_success "🎉 PRODUCTION environment deployment completed successfully!"
echo ""
echo "📋 Production Deployment Summary:"
echo "   • Project Directory: ${PROJECT_DIR}"
echo "   • Log Directory: /var/log/${PROJECT_NAME}"
echo "   • Gunicorn Service: ${GUNICORN_SERVICE_NAME}"
echo "   • Nginx Site: ${NGINX_SITE_NAME}"
echo "   • Server Names: ${PRODUCTION_IP}, ${PRODUCTION_DNS}, ${PRODUCTION_DOMAIN}"
echo "   • SSL: $([ -f /etc/letsencrypt/live/${PRODUCTION_DOMAIN}/fullchain.pem ] && echo 'Configured' || echo 'Manual setup needed')"
echo "   • Firewall: Enabled"
echo "   • Fail2ban: Enabled"
echo "   • Backups: Scheduled daily at 2 AM"
echo ""
echo "🔧 Service Management Commands:"
echo "   • Restart Gunicorn: sudo systemctl restart ${GUNICORN_SERVICE_NAME}"
echo "   • Restart Nginx: sudo systemctl restart nginx"
echo "   • View logs: sudo journalctl -u ${GUNICORN_SERVICE_NAME} -f"
echo "   • Check status: sudo systemctl status ${GUNICORN_SERVICE_NAME}"
echo "   • SSL renewal: sudo certbot renew"
echo ""
echo "🌐 Access your production application via any of these URLs:"
echo "   • IP (HTTP): http://${PRODUCTION_IP}/ (redirects to HTTPS)"
echo "   • DNS (HTTP): http://${PRODUCTION_DNS}/ (redirects to HTTPS)"
echo "   • Domain (HTTP): http://${PRODUCTION_DOMAIN}/ (redirects to HTTPS)"
echo ""
echo "🔒 Secure HTTPS access (after SSL setup):"
echo "   • DNS (HTTPS): https://${PRODUCTION_DNS}/"
echo "   • Domain (HTTPS): https://${PRODUCTION_DOMAIN}/"
echo ""
echo "🔑 Django Admin access:"
echo "   • DNS: https://${PRODUCTION_DNS}/admin/"
echo "   • Domain: https://${PRODUCTION_DOMAIN}/admin/"
echo ""
echo "🔒 Security Features Enabled:"
echo "   • SSL/TLS encryption"
echo "   • Security headers"
echo "   • Rate limiting"
echo "   • Firewall (UFW)"
echo "   • Intrusion prevention (Fail2ban)"
echo ""
echo "📝 Important Next Steps:"
echo "   1. Test all application features thoroughly"
echo "   2. Set up monitoring (Uptime, Performance)"
echo "   3. Configure database backups"
echo "   4. Set up log monitoring"
echo "   5. Review and test SSL certificate auto-renewal"
echo "   6. Set up alerting for critical issues"
echo ""
print_warning "🚨 PRODUCTION SECURITY REMINDERS:"
echo "   • Keep your .env file secure and backed up"
echo "   • Regularly update dependencies and system packages"
echo "   • Monitor application logs and performance"
echo "   • Test backups regularly"
echo "   • Keep SSL certificates updated"
echo "   • Review firewall rules periodically"
