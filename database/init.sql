-- Database initialization script for ContextProvider
-- This script runs when the PostgreSQL container starts for the first time

-- Create necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Set timezone
SET timezone = 'UTC';

-- Create additional indexes for performance (if needed)
-- These will be created by SQLAlchemy migrations, but we can add custom ones here

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE contextprovider TO contextuser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO contextuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO contextuser;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO contextuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO contextuser;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'ContextProvider database initialized successfully';
END $$; 