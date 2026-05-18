-- Migration: Add last_login_at column to users table
-- Apply with psql or via your migration tool (Alembic recommended)

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP;

-- Optional index for quick lookups
CREATE INDEX IF NOT EXISTS ix_users_last_login_at ON users (last_login_at);
