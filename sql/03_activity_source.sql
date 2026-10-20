ALTER TABLE sport_activities
ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'simulated';
