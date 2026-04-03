-- Initialize attendance database
-- This script runs automatically when the PostgreSQL container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create database roles and permissions
-- These are created in the Dockerfile environment variables, 
-- but we can set permissions here

-- Grant permissions to attendance_user
GRANT CONNECT ON DATABASE attendance_db TO attendance_user;
GRANT USAGE ON SCHEMA public TO attendance_user;
GRANT CREATE ON SCHEMA public TO attendance_user;

-- Alter default privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO attendance_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO attendance_user;

-- Create indexes for performance
CREATE INDEX idx_user_email ON public.user(email) WHERE email IS NOT NULL;
CREATE INDEX idx_user_username ON public.user(username);
CREATE INDEX idx_attendance_user_id ON public.attendance(user_id);
CREATE INDEX idx_attendance_date ON public.attendance(date);
CREATE INDEX idx_logs_created_at ON public.logs(created_at DESC);

-- Set connection limits
ALTER USER attendance_user CONNECTION LIMIT 100;

COMMIT;
