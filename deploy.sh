#!/bin/bash

# IEEE 738 Dynamic Line Rating - Quick Deployment Script
# This script helps you prepare your project for deployment

echo "🚀 IEEE 738 DLR - Deployment Preparation"
echo "========================================"
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing Git repository..."
    git init
    echo "✅ Git initialized"
else
    echo "✅ Git repository already exists"
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo "📝 Creating .gitignore..."
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv
*.egg-info/
dist/
build/

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*
dist/
.DS_Store

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Environment
.env
.env.local
.env.*.local

# OS
.DS_Store
Thumbs.db

# Data files (optional - uncomment if you don't want to commit data)
# *.csv
# *.xlsx
# *.json
EOF
    echo "✅ .gitignore created"
else
    echo "✅ .gitignore already exists"
fi

# Check backend requirements
echo ""
echo "🔍 Checking backend dependencies..."
if [ -f "backend/requirements.txt" ]; then
    echo "✅ requirements.txt found"
else
    echo "⚠️  requirements.txt not found, generating..."
    cd backend && pip freeze > requirements.txt && cd ..
    echo "✅ requirements.txt generated"
fi

# Check frontend package.json
echo ""
echo "🔍 Checking frontend dependencies..."
if [ -f "frontend/package.json" ]; then
    echo "✅ package.json found"
else
    echo "❌ frontend/package.json not found!"
    exit 1
fi

# Test backend locally
echo ""
echo "🧪 Testing backend..."
cd backend
if python -c "import fastapi; import uvicorn; import pandas; import numpy" 2>/dev/null; then
    echo "✅ Backend dependencies installed"
else
    echo "⚠️  Some backend dependencies missing. Install with:"
    echo "   cd backend && pip install -r requirements.txt"
fi
cd ..

# Test frontend build
echo ""
echo "🧪 Testing frontend build..."
if [ -d "frontend/node_modules" ]; then
    echo "✅ Frontend dependencies installed"
else
    echo "⚠️  Frontend dependencies not installed. Install with:"
    echo "   cd frontend && npm install"
fi

echo ""
echo "============================================"
echo "🎉 Deployment preparation complete!"
echo ""
echo "Next steps:"
echo "1. Commit your code:"
echo "   git add ."
echo "   git commit -m 'Prepare for deployment'"
echo ""
echo "2. Push to GitHub:"
echo "   git remote add origin YOUR_GITHUB_REPO_URL"
echo "   git push -u origin main"
echo ""
echo "3. Choose a deployment platform:"
echo "   - Render.com (recommended): See DEPLOYMENT.md"
echo "   - Vercel + Render: See DEPLOYMENT.md"
echo "   - Railway.app: See DEPLOYMENT.md"
echo ""
echo "4. Read DEPLOYMENT.md for detailed instructions"
echo "============================================"
