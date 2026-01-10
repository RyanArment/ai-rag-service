# Quick Sync to GitHub 🚀

## Option 1: Use the Script (Easiest)

```bash
./sync_to_github.sh
```

The script will guide you through everything!

---

## Option 2: Manual Steps

### 1. Create Repo on GitHub First
- Go to https://github.com/new
- Name: `production-rag-api`
- **Don't** initialize with README/gitignore
- Click "Create repository"

### 2. Run These Commands

```bash
cd /Users/ryan/ai-rag-service

# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Production-ready RAG API with FastAPI, PostgreSQL + pgvector"

# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/production-rag-api.git

# Push
git branch -M main
git push -u origin main
```

---

## What Gets Synced?

✅ **Included:**
- All Python code (`app/`, `scripts/`)
- Configuration files (`requirements.txt`, `.gitignore`)
- Documentation (`*.md` files)
- Setup scripts (`install_pgvector.sh`, etc.)

❌ **Excluded (via .gitignore):**
- Virtual environment (`venv/`)
- Environment variables (`.env`)
- Database files (`*.db`, `chroma_db/`)
- Python cache (`__pycache__/`)
- Logs (`*.log`)

---

## After Syncing

1. ✅ Add description: "🚀 Production-ready RAG API..."
2. ✅ Add topics: `rag`, `fastapi`, `postgresql`, `pgvector`, etc.
3. ✅ Update README with badges
4. ✅ Add LICENSE file (MIT recommended)

---

## Troubleshooting

**"Repository not found"**
- Make sure you created the repo on GitHub first
- Check username/repo name spelling

**"Authentication failed"**
- Use GitHub Personal Access Token (not password)
- Or set up SSH keys

**"Large files"**
- Check `.gitignore` is working
- Remove large files: `git rm --cached largefile.pdf`

---

Ready? Run `./sync_to_github.sh` or follow Option 2! 🎯
