# Multi-Environment Django Setup Guide

This project supports th3. **Configure AWS S3**: Follow `AWS_S3_SETUP_MULTI_ENV.md` guideee environments: **Local**, **Test**, and **Production**.

## 🏗️ Architecture Overview

### Local Environment (Windows Development)
- **Database**: SQLite
- **Media Storage**: Local filesystem
- **Purpose**: Development and testing on Windows machine

### Test Environment (EC2)
- **Database**: PostgreSQL on separate EC2 instance
- **Media Storage**: AWS S3 (test folder)
- **Purpose**: Testing and QA before production deployment

### Production Environment (EC2)
- **Database**: PostgreSQL on separate EC2 instance  
- **Media Storage**: AWS S3
- **Purpose**: Live production system

## 🚀 Quick Start

### Local Development (Windows)

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Switch to local environment**:
   ```bash
   switch_env.bat local
   ```

3. **Run development server**:
   ```bash
   python manage.py runserver
   ```

### Test Environment (EC2)

1. **Deploy to EC2**:
   ```bash
   chmod +x deploy_test.sh
   ./deploy_test.sh
   ```

2. **Configure AWS S3**: Follow `AWS_S3_SETUP_MULTI_ENV.md` guide

3. **Update environment variables** in `.env`:
   - Set PostgreSQL connection details
   - Configure AWS S3 credentials (test bucket)
   - Update ALLOWED_HOSTS
   - Set secure SECRET_KEY

3. **Switch environment**:
   ```bash
   ./switch_env.sh test
   ```

### Production Environment (EC2)

1. **Deploy to EC2**:
   ```bash
   chmod +x deploy_production.sh
   ./deploy_production.sh
   ```

2. **Configure AWS S3**: Follow AWS_S3_SETUP.md

3. **Update environment variables** in `.env`:
   - Set PostgreSQL connection details
   - Configure AWS S3 credentials
   - Set production domain in ALLOWED_HOSTS
   - Generate secure SECRET_KEY

4. **Switch environment**:
   ```bash
   ./switch_env.sh production
   ```

## 📁 Environment Files

### `.env.local` - Local Development
- Minimal environment configuration (only ENVIRONMENT=local required)
- All settings hardcoded in settings.py for simplicity
- SQLite database (no configuration needed)
- Local media storage (no configuration needed)
- Debug mode enabled (hardcoded)

### `.env.test` - Test Environment  
- PostgreSQL database
- AWS S3 media storage (test folder)
- Debug mode enabled
- Test-specific configurations

### `.env.production` - Production Environment
- PostgreSQL database
- AWS S3 media storage
- Debug mode disabled
- Security headers enabled
- Production optimizations

## 🔧 Environment Variables

### Required for Local Development:
- `ENVIRONMENT`: Set to 'local' (all other settings are hardcoded)

### Required for Test & Production environments:
- `ENVIRONMENT`: Environment name (test/production)
- `DEBUG`: Enable/disable debug mode
- `SECRET_KEY`: Django secret key (generate secure keys for test/production)
- `ALLOWED_HOSTS`: Comma-separated allowed hosts

### Database (Test & Production):
- `DATABASE_ENGINE`: Database engine
- `DATABASE_NAME`: Database name
- `DATABASE_USER`: Database username
- `DATABASE_PASSWORD`: Database password
- `DATABASE_HOST`: Database host (PostgreSQL EC2 IP)
- `DATABASE_PORT`: Database port (5432)

### AWS S3 (Production only):
- `USE_S3`: Enable S3 storage (True/False)
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_STORAGE_BUCKET_NAME`: S3 bucket name
- `AWS_S3_REGION_NAME`: AWS region

### Security (Production):
- `SECURE_SSL_REDIRECT`: Force HTTPS
- `SECURE_HSTS_SECONDS`: HSTS max age
- `SESSION_COOKIE_SECURE`: Secure session cookies
- `CSRF_COOKIE_SECURE`: Secure CSRF cookies

## 🔄 Environment Switching

### Windows (Local):
```bash
switch_env.bat local
switch_env.bat test     # If testing locally
switch_env.bat production  # If testing production settings locally
```

### Linux/EC2:
```bash
./switch_env.sh test
./switch_env.sh production
```

## 🗄️ Database Setup

### Local (SQLite)
No setup required - Django creates the database automatically.

### Test & Production (PostgreSQL)

1. **On PostgreSQL EC2 instance**:
   ```sql
   CREATE DATABASE precatorios_test;
   CREATE DATABASE precatorios_prod;
   CREATE USER precatorios_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE precatorios_test TO precatorios_user;
   GRANT ALL PRIVILEGES ON DATABASE precatorios_prod TO precatorios_user;
   ```

2. **Configure PostgreSQL** to accept connections from Django EC2:
   ```bash
   # In postgresql.conf
   listen_addresses = 'localhost,private_ip'
   
   # In pg_hba.conf
   host    all    precatorios_user    django_ec2_ip/32    md5
   ```

## ☁️ AWS S3 Setup (Test & Production)

See `AWS_S3_SETUP_MULTI_ENV.md` for detailed S3 configuration for both environments.

## 🔐 Security Considerations

### Test Environment:
- Use strong database passwords
- Restrict EC2 security groups
- Keep DEBUG=True for testing

### Production Environment:
- Generate new SECRET_KEY
- Set DEBUG=False
- Configure HTTPS/SSL
- Use IAM roles for S3 access
- Enable security headers
- Set up proper logging
- Configure firewall rules

## 📊 Monitoring & Logging

### Log Files:
- **Local**: `logs/django.log`
- **EC2**: `/var/log/precatorios/django.log`

### Log Levels:
- **Local**: DEBUG
- **Test**: INFO  
- **Production**: WARNING

## 🚨 Troubleshooting

### Database Connection Issues:
```bash
python manage.py check --database default
```

### S3 Access Issues:
```bash
python manage.py shell -c "
from django.core.files.storage import default_storage
print(default_storage.location)
print(default_storage.bucket_name)
"
```

### Environment Check:
```bash
python manage.py shell -c "
from django.conf import settings
print(f'Environment: {settings.ENVIRONMENT}')
print(f'Debug: {settings.DEBUG}')
print(f'Database: {settings.DATABASES[\"default\"][\"ENGINE\"]}')
"
```

## 📋 Deployment Checklist

### Before Test Deployment:
- [ ] PostgreSQL EC2 instance configured
- [ ] Database created and user configured
- [ ] S3 bucket created and configured for test
- [ ] IAM user/role configured for S3
- [ ] Security groups configured
- [ ] Environment variables set

### Before Production Deployment:
- [ ] All test environment checks passed
- [ ] S3 bucket created and configured
- [ ] IAM user/role configured for S3
- [ ] SSL certificate ready
- [ ] Domain configured
- [ ] Backup strategy planned
- [ ] Monitoring setup ready

### After Deployment:
- [ ] Run `python manage.py check`
- [ ] Test file upload functionality
- [ ] Test database connectivity
- [ ] Verify static files serving
- [ ] Test user authentication
- [ ] Check log files
- [ ] Verify S3 integration (test and production)
- [ ] Test file upload to S3

## 🔄 Maintenance

### Regular Tasks:
- Monitor log files
- Update dependencies
- Database backups
- S3 bucket monitoring
- Security updates

### Environment Updates:
1. Update `.env.*` files as needed
2. Run `./switch_env.sh [environment]`
3. Test functionality
4. Deploy changes if needed
