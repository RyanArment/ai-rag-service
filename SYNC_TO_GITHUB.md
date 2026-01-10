# How to Sync Your App to GitHub

## Step-by-Step Guide

### Step 1: Initialize Git (if not already done)

```bash
cd /Users/ryan/ai-rag-service
git init
```

### Step 2: Create/Update .gitignore

Make sure you have a `.gitignore` file that excludes:
- Virtual environment (`venv/`)
- Environment variables (`.env`)
- Python cache (`__pycache__/`, `*.pyc`)
- Database files
- IDE files
- OS files

### Step 3: Add All Files

```bash
git add .
```

### Step 4: Make Initial Commit

```bash
git commit -m "Initial commit: Production-ready RAG API with FastAPI, PostgreSQL + pgvector"
```

### Step 5: Create Repository on GitHub

1. Go to https://github.com/new
2. Repository name: `production-rag-api` (or your chosen name)
3. Description: (paste your description)
4. Choose **Public** or **Private**
5. **DO NOT** initialize with README, .gitignore, or license (we already have files)
6. Click **Create repository**

### Step 6: Add Remote and Push

After creating the repo, GitHub will show you commands. Use these:

```bash
# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/production-rag-api.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

---

## Complete Command Sequence

Copy and paste this entire block (replace `YOUR_USERNAME`):

```bash
cd /Users/ryan/ai-rag-service

# Initialize git (if needed)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Production-ready RAG API with FastAPI, PostgreSQL + pgvector"

# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/production-rag-api.git

# Set main branch
git branch -M main

# Push to GitHub
git push -u origin main
```

---

## If You Already Have a Git Repo

If git is already initialized, skip to Step 5:

```bash
# Check current remotes
git remote -v

# If no remote, add it
git remote add origin https://github.com/YOUR_USERNAME/production-rag-api.git

# Push
git push -u origin main
```

---

## Troubleshooting

### "Repository not found"
- Check your GitHub username is correct
- Make sure you created the repo on GitHub first
- Verify the repo name matches exactly

### "Authentication failed"
- Use GitHub Personal Access Token instead of password
- Or use SSH: `git remote set-url origin git@github.com:YOUR_USERNAME/production-rag-api.git`

### "Large files" error
- Make sure `.gitignore` excludes large files
- Check for database dumps, large PDFs, etc.

### "Branch main does not exist"
- Create it: `git checkout -b main`
- Or use: `git branch -M main`

---

## After Pushing

1. ✅ Visit your repo: `https://github.com/YOUR_USERNAME/production-rag-api`
2. ✅ Add topics/tags in GitHub UI
3. ✅ Update README if needed
4. ✅ Add a license file (MIT, Apache 2.0, etc.)
5. ✅ Consider adding a demo/deployment link

---

## Quick Reference

```bash
# Check status
git status

# See what will be committed
git status --short

# Add specific file
git add filename.py

# Commit changes
git commit -m "Your commit message"

# Push changes
git push

# Pull changes
git pull
```

---

## Next Steps After Syncing

1. **Add README badges** - Show tech stack
2. **Add screenshots** - API docs, architecture diagrams
3. **Add LICENSE** - Choose MIT, Apache 2.0, etc.
4. **Add CONTRIBUTING.md** - If open source
5. **Set up GitHub Actions** - CI/CD pipeline
6. **Add issues template** - For bug reports
7. **Deploy to production** - Heroku, Railway, AWS, etc.

---

Ready to sync! 🚀
