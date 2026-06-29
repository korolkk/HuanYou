-- HuanYou Database Initialization Script
-- Enables pgvector and Chinese full-text search support

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable uuid-ossp for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create Chinese text search configuration
-- This enables PostgreSQL full-text search for Chinese content
DO $$
BEGIN
    -- Create Chinese text search configuration if not exists
    IF NOT EXISTS (SELECT 1 FROM pg_ts_config WHERE cfgname = 'chinese') THEN
        CREATE TEXT SEARCH CONFIGURATION chinese (PARSER = default);
        -- For basic Chinese support, we use the 'simple' dictionary
        -- In production, consider installing zhparser or jieba
        ALTER TEXT SEARCH CONFIGURATION chinese
            ALTER MAPPING FOR asciiword, word, hword, hword_part
            WITH simple;
    END IF;
END $$;

-- Log setup completion
DO $$
BEGIN
    RAISE NOTICE 'HuanYou database initialized: pgvector + Chinese FTS ready';
END $$;
