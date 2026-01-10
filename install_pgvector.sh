#!/bin/bash
# Script to install pgvector extension for PostgreSQL 15

set -e

echo "Installing pgvector extension for PostgreSQL 15..."

# Navigate to temp directory
cd /tmp

# Clone pgvector if not already there
if [ ! -d "pgvector-src" ]; then
    git clone --branch v0.8.1 https://github.com/pgvector/pgvector.git pgvector-src
fi

cd pgvector-src

# Set PostgreSQL path
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"

# Compile
echo "Compiling pgvector..."
make

# Install (requires sudo)
echo "Installing pgvector (requires sudo password)..."
sudo make install PG_CONFIG=/opt/homebrew/opt/postgresql@15/bin/pg_config

# Restart PostgreSQL
echo "Restarting PostgreSQL..."
brew services restart postgresql@15

# Wait for PostgreSQL to start
sleep 3

# Create extension (requires superuser - use current user who installed PostgreSQL)
echo "Creating vector extension in database..."
CURRENT_USER=$(whoami)
if psql -U "$CURRENT_USER" -d ragdb -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null; then
    echo "✓ Extension created as $CURRENT_USER user"
else
    echo "⚠️  Could not create extension automatically. Please run manually as superuser:"
    echo "   psql -U $CURRENT_USER -d ragdb -c \"CREATE EXTENSION IF NOT EXISTS vector;\""
fi

# Verify
echo "Verifying installation..."
psql -U raguser -d ragdb -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"

echo "✅ pgvector installed successfully!"
echo ""
echo "Next step: Run 'python3 scripts/init_db.py' to create tables"
