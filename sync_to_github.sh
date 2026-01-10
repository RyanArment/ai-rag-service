#!/bin/bash
# Script to sync your RAG service to GitHub

set -e

echo "🚀 Syncing RAG Service to GitHub"
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
else
    echo "✓ Git repository already initialized"
fi

# Check if .gitignore exists
if [ ! -f ".gitignore" ]; then
    echo "⚠️  Warning: .gitignore not found!"
    exit 1
fi

echo ""
echo "📝 Current git status:"
git status --short | head -10 || echo "No changes detected"

echo ""
read -p "Enter your GitHub username: " GITHUB_USERNAME
read -p "Enter your repository name (default: production-rag-api): " REPO_NAME
REPO_NAME=${REPO_NAME:-production-rag-api}

echo ""
echo "📋 Summary:"
echo "  Username: $GITHUB_USERNAME"
echo "  Repository: $REPO_NAME"
echo "  Remote URL: https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
echo ""

read -p "Continue? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

# Add all files
echo ""
echo "📦 Adding files..."
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo "⚠️  No changes to commit. Files may already be committed."
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "💾 Committing changes..."
    git commit -m "Initial commit: Production-ready RAG API with FastAPI, PostgreSQL + pgvector"
fi

# Check if remote exists
if git remote get-url origin &>/dev/null; then
    echo ""
    echo "⚠️  Remote 'origin' already exists:"
    git remote get-url origin
    read -p "Update remote? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git remote set-url origin "https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
    fi
else
    echo ""
    echo "🔗 Adding remote..."
    git remote add origin "https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
fi

# Set main branch
echo ""
echo "🌿 Setting main branch..."
git branch -M main 2>/dev/null || echo "Already on main branch"

# Push
echo ""
echo "🚀 Pushing to GitHub..."
echo "   (You may be prompted for GitHub credentials)"
echo ""
git push -u origin main

echo ""
echo "✅ Success! Your code is now on GitHub!"
echo ""
echo "📱 View your repo at:"
echo "   https://github.com/$GITHUB_USERNAME/$REPO_NAME"
echo ""
echo "💡 Next steps:"
echo "   1. Add repository description and topics"
echo "   2. Update README.md"
echo "   3. Add LICENSE file"
echo "   4. Consider adding screenshots/demos"
