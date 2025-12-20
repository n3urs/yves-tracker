-- Yves Tracker Database Schema for Supabase
-- Run this in your Supabase SQL Editor to create all tables

-- Users table
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    pin TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Bodyweights table (current bodyweight)
CREATE TABLE bodyweights (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE,
    bodyweight_kg DECIMAL(5,2) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(username)
);

-- Bodyweight history table
CREATE TABLE bodyweight_history (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE,
    date DATE NOT NULL,
    bodyweight_kg DECIMAL(5,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User profile table (1RM goals)
CREATE TABLE user_profile (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE,
    bodyweight_kg DECIMAL(5,2) NOT NULL,
    left_20mm_goal DECIMAL(5,2),
    left_20mm_current DECIMAL(5,2),
    right_20mm_goal DECIMAL(5,2),
    right_20mm_current DECIMAL(5,2),
    left_14mm_goal DECIMAL(5,2),
    left_14mm_current DECIMAL(5,2),
    right_14mm_goal DECIMAL(5,2),
    right_14mm_current DECIMAL(5,2),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(username)
);

-- Workout logs (finger training - Sheet1)
CREATE TABLE workouts (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE,
    date DATE NOT NULL,
    exercise TEXT NOT NULL,
    arm TEXT NOT NULL,
    sets INTEGER,
    reps INTEGER,
    weight DECIMAL(5,2),
    notes TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Activity log (climbing, board, work pullups)
CREATE TABLE activity_log (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE,
    date DATE NOT NULL,
    activity_type TEXT NOT NULL,
    duration_min INTEGER,
    notes TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Custom workout templates
CREATE TABLE custom_workout_templates (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE,
    workout_name TEXT NOT NULL,
    workout_type TEXT NOT NULL,
    description TEXT,
    tracks_weight BOOLEAN DEFAULT FALSE,
    tracks_sets BOOLEAN DEFAULT FALSE,
    tracks_reps BOOLEAN DEFAULT FALSE,
    tracks_duration BOOLEAN DEFAULT FALSE,
    tracks_distance BOOLEAN DEFAULT FALSE,
    tracks_rpe BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(username, workout_name)
);

-- Custom workout logs
CREATE TABLE custom_workout_logs (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE,
    date DATE NOT NULL,
    template_name TEXT NOT NULL,
    category TEXT NOT NULL,
    exercise_1 TEXT,
    exercise_2 TEXT,
    exercise_3 TEXT,
    exercise_4 TEXT,
    exercise_5 TEXT,
    notes TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User settings (weekly goals, preferences)
CREATE TABLE user_settings (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE,
    setting_key TEXT NOT NULL,
    setting_value TEXT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(username, setting_key)
);

-- Goals table (1RM weight goals)
CREATE TABLE goals (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE,
    exercise TEXT NOT NULL,
    arm TEXT NOT NULL,
    target_weight DECIMAL(5,2) NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    date_set DATE NOT NULL,
    date_completed DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_workouts_username_date ON workouts(username, date DESC);
CREATE INDEX idx_activity_log_username_date ON activity_log(username, date DESC);
CREATE INDEX idx_custom_workout_logs_username_date ON custom_workout_logs(username, date DESC);
CREATE INDEX idx_bodyweight_history_username_date ON bodyweight_history(username, date DESC);
CREATE INDEX idx_user_settings_username_key ON user_settings(username, setting_key);
CREATE INDEX idx_goals_username ON goals(username);

-- Enable Row Level Security (RLS) on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE bodyweights ENABLE ROW LEVEL SECURITY;
ALTER TABLE bodyweight_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profile ENABLE ROW LEVEL SECURITY;
ALTER TABLE workouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE custom_workout_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE custom_workout_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE goals ENABLE ROW LEVEL SECURITY;

-- Create permissive policies (allow all operations for now - you can tighten this later)
CREATE POLICY "Allow all operations" ON users FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations" ON bodyweights FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations" ON bodyweight_history FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations" ON user_profile FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations" ON workouts FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations" ON activity_log FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations" ON custom_workout_templates FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations" ON custom_workout_logs FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations" ON user_settings FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations" ON goals FOR ALL USING (true) WITH CHECK (true);
