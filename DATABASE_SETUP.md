# Database Setup Guide: SQLite vs PostgreSQL

## 🎯 For AI Engineering Career: **PostgreSQL is Better**

### Why PostgreSQL for AI Engineering?

1. **Industry Standard** - Most production AI systems use PostgreSQL
2. **Better Concurrency** - Handles multiple users/queries simultaneously
3. **JSON Support** - Native JSON/JSONB for storing AI metadata
4. **Scalability** - Can handle millions of records
5. **Production Ready** - Used by companies like OpenAI, Anthropic, etc.
6. **Vector Extensions** - pgvector extension for native vector search (alternative to ChromaDB!)
7. **Better for Resumes** - Shows you know production-grade databases

### SQLite vs PostgreSQL

| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| **Best For** | Development, small projects | Production, AI systems |
| **Concurrency** | Single writer | Multiple concurrent users |
| **Scalability** | Limited | Excellent |
| **JSON Support** | Basic | Advanced (JSONB) |
| **Vector Search** | No | Yes (pgvector) |
| **Setup** | File-based, easy | Server required |
| **Career Value** | Good for learning | **Industry standard** |

---

## 🚀 Recommended Setup: Both!

**Development:** SQLite (easy, fast setup)
**Production:** PostgreSQL (industry standard)

Our code already supports both! Just change `DATABASE_URL` in `.env`.

---

## 📦 Setup Instructions

### Option 1: SQLite (Development - Quick Start)

**Already configured!** Just run:

```bash
# Install dependencies
pip install sqlalchemy alembic

# Initialize database
python3 -c "from app.database.database import init_db; init_db()"
```

**That's it!** Database file created at `./rag_service.db`

---

### Option 2: PostgreSQL (Production - Recommended for Career)

#### Step 1: Install PostgreSQL

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows:**
Download from: https://www.postgresql.org/download/windows/

#### Step 2: Create Database

```bash
# Connect to PostgreSQL
psql postgres

# Create database and user
CREATE DATABASE ragdb;
CREATE USER raguser WITH PASSWORD 'your_password_here';
GRANT ALL PRIVILEGES ON DATABASE ragdb TO raguser;
\q
```

#### Step 3: Install Python Driver

```bash
pip install psycopg2-binary
```

#### Step 4: Update `.env`

```bash
# Development (SQLite)
DATABASE_URL=sqlite:///./rag_service.db

# Production (PostgreSQL)
DATABASE_URL=postgresql://raguser:your_password_here@localhost:5432/ragdb
```

#### Step 5: Initialize Database

```bash
python3 -c "from app.database.database import init_db; init_db()"
```

---

## 🎓 Career Tip: Learn PostgreSQL

For AI engineering roles, PostgreSQL knowledge is **highly valued**:

- **OpenAI** uses PostgreSQL
- **Anthropic** uses PostgreSQL  
- **Most AI startups** use PostgreSQL
- **Vector databases** often integrate with PostgreSQL (pgvector)

**Learning PostgreSQL shows:**
- Production-ready skills
- Understanding of scalable systems
- Real-world experience

---

## 🔥 Bonus: pgvector Extension (Advanced)

PostgreSQL has a **pgvector** extension for native vector search!

This means you could potentially:
- Store embeddings directly in PostgreSQL
- Use PostgreSQL for both metadata AND vectors
- Skip ChromaDB entirely (optional)

**Setup pgvector:**
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

**This is cutting-edge** and shows advanced AI engineering skills!

---

## 📝 Quick Reference

### SQLite Commands
```bash
# View database
sqlite3 rag_service.db
.tables
.schema users
SELECT * FROM users;
```

### PostgreSQL Commands
```bash
# Connect
psql -U raguser -d ragdb

# List tables
\dt

# View schema
\d users

# Query
SELECT * FROM users;
```

---

## 🎯 Recommendation

**For Learning:** Start with SQLite (easier)
**For Career:** Use PostgreSQL (industry standard)
**For Resume:** Mention PostgreSQL experience

Our code supports both - just change `DATABASE_URL`!
