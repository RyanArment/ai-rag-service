# Migrating to PostgreSQL + pgvector

## What Changed

We're migrating from **dual database** (PostgreSQL + ChromaDB) to **single database** (PostgreSQL + pgvector).

### Benefits:
- ✅ **Simpler architecture** - One database instead of two
- ✅ **ACID transactions** - Everything in one transaction
- ✅ **SQL + Vector search** - Query both in one SQL statement
- ✅ **Easier deployment** - One database to manage
- ✅ **Production-ready** - Industry standard approach

---

## Installation Required

pgvector needs to be installed in PostgreSQL. Run:

```bash
./install_pgvector.sh
```

Or manually:

```bash
cd /tmp
git clone --branch v0.8.1 https://github.com/pgvector/pgvector.git pgvector-src
cd pgvector-src
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
make
sudo make install PG_CONFIG=/opt/homebrew/opt/postgresql@15/bin/pg_config
brew services restart postgresql@15
psql -U raguser -d ragdb -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

---

## What's Different

### Before (Dual DB):
- Metadata → PostgreSQL
- Embeddings → ChromaDB
- Two separate systems

### After (Single DB):
- Metadata + Embeddings → PostgreSQL
- Everything in one place
- Vector search via pgvector

---

## Code Changes Made

1. ✅ **Updated models** - `DocumentChunk` now has `embedding` column (VECTOR type)
2. ✅ **Created PgVectorStore** - PostgreSQL-based vector store
3. ✅ **Updated router** - Defaults to `pgvector` provider
4. ✅ **Updated document upload** - Stores embeddings in PostgreSQL
5. ✅ **Updated RAG pipeline** - Uses PostgreSQL for vector search

---

## After Installation

Once pgvector is installed:

```bash
# Initialize database with new schema
python3 scripts/init_db.py

# Verify table structure
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
psql -U raguser -d ragdb -c "\d document_chunks"
```

You should see the `embedding` column as `vector(1536)`.

---

## Fallback Option

If pgvector installation is complex, you can temporarily use ChromaDB:

```bash
# In .env
VECTOR_STORE_PROVIDER=chroma
```

Then switch to pgvector once installed.

---

## Testing

After installation and initialization:

1. **Upload a document:**
   ```bash
   curl -X POST "http://localhost:8000/documents/upload" \
     -F "file=@test.pdf"
   ```

2. **Check PostgreSQL:**
   ```sql
   SELECT id, chunk_index, 
          pg_typeof(embedding) as embedding_type,
          array_length(embedding::float[], 1) as dimensions
   FROM document_chunks 
   LIMIT 1;
   ```

3. **Query with RAG:**
   ```bash
   curl -X POST "http://localhost:8000/rag/query" \
     -H "Content-Type: application/json" \
     -d '{"question": "What is this about?"}'
   ```

---

## Career Value

✅ **pgvector Experience** - Cutting-edge PostgreSQL extension
✅ **Single Database Architecture** - Simpler, more maintainable
✅ **SQL + Vector Search** - Advanced query capabilities
✅ **Production Patterns** - Industry-standard approach

This shows **advanced AI engineering** skills!
