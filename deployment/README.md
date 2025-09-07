# Django Multi-Environment Deployment

This folder contains all the deployment configurations, scripts, and documentation for the Precatorios Django project.

## 📁 Folder Structure

```
deployment/
├── docs/                           # Documentation
│   ├── ENVIRONMENT_SETUP.md        # Complete setup guide
│   └── AWS_S3_SETUP_MULTI_ENV.md   # S3 configuration guide
├── environments/                   # Environment templates
│   ├── .env.local                  # Local development template
│   ├── .env.test                   # Test environment template
│   └── .env.production             # Production environment template
├── scripts/                        # Deployment scripts
│   ├── deploy_test.sh              # Test environment deployment (Ubuntu)
│   ├── deploy_production.sh        # Production deployment (Ubuntu)
│   ├── switch_env.sh               # Environment switcher (Linux)
│   └── switch_env.bat              # Environment switcher (Windows)
└── README.md                       # This file
```

## 🚀 Quick Start

### 1. Local Development Setup (Windows)
```bash
# Copy minimal environment file (only sets ENVIRONMENT=local)
copy deployment\environments\.env.local .env

# Switch to local environment (validates settings)
deployment\scripts\switch_env.bat local

# Install dependencies and run (no additional configuration needed!)
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

**Note**: Local environment uses hardcoded settings in `settings.py` - no environment variables needed!

### 2. Test Environment Setup (EC2 Ubuntu)
```bash
# Copy environment template
cp deployment/environments/.env.test .env

# Edit environment variables
nano .env

# Run deployment script
chmod +x deployment/scripts/deploy_test.sh
./deployment/scripts/deploy_test.sh
```

### 3. Production Environment Setup (EC2 Ubuntu)
```bash
# Copy environment template
cp deployment/environments/.env.production .env

# Edit environment variables with production values
nano .env

# Run deployment script
chmod +x deployment/scripts/deploy_production.sh
./deployment/scripts/deploy_production.sh
```

## 🏗️ Environment Architecture

| Environment | Database | Media Storage | Configuration |
|-------------|----------|---------------|---------------|
| **Local** | SQLite | Local filesystem | Hardcoded (no env vars needed) |
| **Test** | PostgreSQL (EC2) | AWS S3 (test folder) | Environment variables |
| **Production** | PostgreSQL (EC2) | AWS S3 (production folder) | Environment variables |

## 📖 Documentation

- **[Environment Setup Guide](docs/ENVIRONMENT_SETUP.md)** - Complete multi-environment configuration
- **[AWS S3 Setup](docs/AWS_S3_SETUP_MULTI_ENV.md)** - S3 bucket configuration for test and production

## 🔧 Scripts

### Environment Management
- `switch_env.bat` - Windows environment switcher
- `switch_env.sh` - Linux environment switcher

### Deployment
- `deploy_test.sh` - Automated test environment setup
- `deploy_production.sh` - Automated production deployment

## 🔐 Security Notes

- Environment files in this folder are **templates only**
- Copy to project root as `.env` and fill with actual credentials
- Never commit real credentials to version control
- Use strong passwords and rotate keys regularly

## 📋 Prerequisites

### For EC2 Deployment:
- Ubuntu 22.04 LTS or 24.04 LTS
- PostgreSQL EC2 instance configured
- AWS S3 bucket created (for test/production)
- Domain name configured (for production)
- SSL certificate ready (for production)

### For Local Development:
- Python 3.8+
- Windows 10/11
- Git for Windows

## 🆘 Support

If you encounter issues:

1. Check the documentation in `docs/`
2. Verify environment variables in `.env`
3. Test database connectivity
4. Validate S3 permissions (for EC2 environments)
5. Check Django logs for errors

## 🔄 Environment Switching

### Windows (Local Development):
```bash
# Switch to any environment
deployment\scripts\switch_env.bat local
deployment\scripts\switch_env.bat test
deployment\scripts\switch_env.bat production
```

### Linux (EC2):
```bash
# Switch environments on server
./deployment/scripts/switch_env.sh test
./deployment/scripts/switch_env.sh production
```

---

**Note**: Always test changes in the test environment before deploying to production!
