#!/bin/bash
# Quick environment setup script for Linux/Mac
# This script provides easy access to deployment tools

COMMAND=$1

if [ -z "$COMMAND" ]; then
    echo "🚀 Django Multi-Environment Setup Tool"
    echo ""
    echo "Usage: ./setup.sh [command]"
    echo ""
    echo "Available commands:"
    echo "  local       - Switch to local development environment"
    echo "  test        - Switch to test environment"
    echo "  production  - Switch to production environment"
    echo "  deploy-test - Deploy to test environment"
    echo "  deploy-prod - Deploy to production environment"
    echo "  help        - Show deployment documentation"
    echo "  docs        - Show documentation location"
    echo ""
    echo "Examples:"
    echo "  ./setup.sh local"
    echo "  ./setup.sh deploy-test"
    exit 0
fi

case $COMMAND in
    "local")
        ./deployment/scripts/switch_env.sh local
        ;;
    "test")
        ./deployment/scripts/switch_env.sh test
        ;;
    "production")
        ./deployment/scripts/switch_env.sh production
        ;;
    "deploy-test")
        echo "🚀 Starting test environment deployment..."
        chmod +x deployment/scripts/deploy_test.sh
        ./deployment/scripts/deploy_test.sh
        ;;
    "deploy-prod")
        echo "🚀 Starting production environment deployment..."
        chmod +x deployment/scripts/deploy_production.sh
        ./deployment/scripts/deploy_production.sh
        ;;
    "help")
        echo "📖 Deployment documentation available at:"
        echo "  - deployment/README.md"
        echo "  - deployment/docs/ENVIRONMENT_SETUP.md"
        echo "  - deployment/docs/AWS_S3_SETUP_MULTI_ENV.md"
        ;;
    "docs")
        echo "📁 Documentation files:"
        ls -la deployment/docs/
        ;;
    *)
        echo "❌ Unknown command: $COMMAND"
        echo "Run './setup.sh' without arguments to see available commands."
        exit 1
        ;;
esac
