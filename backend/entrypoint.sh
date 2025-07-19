#!/bin/bash
set -e

echo "🚀 Starting ContextProvider Backend..."

# Wait for database to be available
echo "⏳ Waiting for database connection..."
python3 -c "
import time
import psycopg2
import os
from urllib.parse import urlparse

# Parse database URL
db_url = os.getenv('DATABASE_URL')
if not db_url:
    print('❌ DATABASE_URL not found')
    exit(1)

parsed = urlparse(db_url)
db_config = {
    'host': parsed.hostname,
    'port': parsed.port or 5432,
    'user': parsed.username,
    'password': parsed.password,
    'database': parsed.path[1:]  # Remove leading slash
}

# Wait for database
max_retries = 30
for i in range(max_retries):
    try:
        conn = psycopg2.connect(**db_config)
        conn.close()
        print(f'✅ Database connected after {i+1} attempts')
        break
    except psycopg2.OperationalError as e:
        if i == max_retries - 1:
            print(f'❌ Failed to connect to database after {max_retries} attempts')
            print(f'Error: {e}')
            exit(1)
        print(f'⏳ Attempt {i+1}/{max_retries} failed, retrying in 2 seconds...')
        time.sleep(2)
"

# Create database tables
echo "📋 Creating database tables..."
python3 -c "
try:
    from app.core.database import engine, Base
    from app.models.models import User, Document
    
    print('Creating tables with SQLAlchemy...')
    Base.metadata.create_all(bind=engine)
    print('✅ Database tables created successfully')
except Exception as e:
    print(f'❌ Error creating tables: {e}')
    exit(1)
"

# Wait for ChromaDB to be available
echo "⏳ Waiting for ChromaDB connection..."
python3 -c "
import time
import requests
import os

chroma_host = os.getenv('CHROMA_HOST', 'chromadb')
chroma_port = os.getenv('CHROMA_PORT', '8000')
chroma_url = f'http://{chroma_host}:{chroma_port}/api/v1/heartbeat'

max_retries = 30
for i in range(max_retries):
    try:
        response = requests.get(chroma_url, timeout=5)
        if response.status_code == 200:
            print(f'✅ ChromaDB connected after {i+1} attempts')
            break
    except Exception as e:
        if i == max_retries - 1:
            print(f'⚠️  ChromaDB not available after {max_retries} attempts, continuing anyway...')
            break
        print(f'⏳ ChromaDB attempt {i+1}/{max_retries} failed, retrying in 2 seconds...')
        time.sleep(2)
"

echo "🎯 Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 