# Production Architecture Plan

## Current State

✅ **Vector Database:** ChromaDB (local) - stores embeddings + document chunks
❌ **Relational Database:** None - no metadata, users, or query history

---

## Production Architecture

### 1. **Relational Database (PostgreSQL/SQLite)**
**Purpose:** Store structured metadata and business logic

**Tables Needed:**
- `users` - User accounts, authentication
- `documents` - Document metadata (filename, upload date, status)
- `document_chunks` - Mapping between documents and vector chunks
- `queries` - Query history and analytics
- `sessions` - User sessions
- `api_keys` - API key management
- `rate_limits` - Rate limiting tracking

### 2. **Vector Database (ChromaDB or Managed Service)**
**Purpose:** Store embeddings for semantic search

**Options:**
- **ChromaDB** (current) - Good for self-hosted, free
- **Pinecone** - Managed, scalable, production-ready
- **Weaviate** - Self-hosted or cloud, feature-rich
- **Qdrant** - Fast, self-hosted or cloud

**Recommendation:** Start with ChromaDB, upgrade to Pinecone/Weaviate for scale

---

## Implementation Plan

### Phase 1: Add Relational Database
1. Set up SQLAlchemy ORM
2. Create database models
3. Add migrations (Alembic)
4. Update document upload to store metadata in DB
5. Add query history tracking

### Phase 2: Production Vector DB (Optional)
1. Add Pinecone/Weaviate support
2. Keep ChromaDB as fallback
3. Make vector store provider configurable

### Phase 3: Production Features
1. User authentication
2. API key management
3. Rate limiting
4. Query analytics
5. Document versioning

---

## Database Schema (Proposed)

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    filename VARCHAR NOT NULL,
    file_size INTEGER,
    file_type VARCHAR,
    status VARCHAR DEFAULT 'processing', -- processing, completed, failed
    chunks_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Document chunks mapping
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    chunk_index INTEGER NOT NULL,
    vector_chunk_id VARCHAR NOT NULL, -- ID in ChromaDB
    content_preview TEXT, -- First 200 chars
    created_at TIMESTAMP DEFAULT NOW()
);

-- Query history
CREATE TABLE queries (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    question TEXT NOT NULL,
    answer TEXT,
    sources_count INTEGER,
    latency_ms FLOAT,
    model VARCHAR,
    provider VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);

-- API keys
CREATE TABLE api_keys (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    key_hash VARCHAR UNIQUE NOT NULL,
    name VARCHAR,
    rate_limit INTEGER DEFAULT 100, -- requests per hour
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);
```

---

## Next Steps

1. **Add SQLAlchemy + Alembic**
2. **Create database models**
3. **Update document upload to use DB**
4. **Add query history tracking**
5. **Make vector DB configurable**
