# pgvector Setup Instructions

## Current Status

pgvector compiled successfully but needs to be installed with sudo. The extension files are ready in `/tmp/pgvector-src`.

## Installation Steps

### Option 1: Install with Sudo (Recommended)

Run this command (you'll be prompted for your password):

```bash
cd /tmp/pgvector-src
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
sudo make install PG_CONFIG=/opt/homebrew/opt/postgresql@15/bin/pg_config
```

Then restart PostgreSQL and create the extension:

```bash
brew services restart postgresql@15
sleep 3
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
psql -U raguser -d ragdb -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Option 2: Use ChromaDB Temporarily

While setting up pgvector, you can use ChromaDB by setting:

```bash
# In .env file
VECTOR_STORE_PROVIDER=chroma
```

Then switch back to pgvector once installed.

## After Installation

Once pgvector is installed, initialize the database:

```bash
python3 scripts/init_db.py
```

This will create the `document_chunks` table with the `VECTOR(1536)` column.

## Verify Installation

```bash
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
psql -U raguser -d ragdb -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
```

Should show:
```
 extname | extversion 
---------+------------
 vector  | 0.8.1
```

## Troubleshooting

If you get "extension vector is not available":
1. Make sure pgvector was installed: `sudo make install`
2. Restart PostgreSQL: `brew services restart postgresql@15`
3. Check extension location: `psql -U raguser -d ragdb -c "SHOW sharedir;"`
