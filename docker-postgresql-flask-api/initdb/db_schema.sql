-- CREATE TABLE demo (
--     id   serial PRIMARY KEY,
--     name text NOT NULL
-- );

-- INSERT INTO demo (name) VALUES ('hello docker-postgres');
CREATE TABLE IF NOT EXISTS social_evaluation_status (
    id SERIAL PRIMARY KEY,
    emirates_id VARCHAR(50) NOT NULL,
    evaluation_result JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);