CREATE TABLE IF NOT EXISTS departures (
    id SERIAL PRIMARY KEY,
    station_name VARCHAR(100) NOT NULL,
    departure_time TIMESTAMP NOT NULL,
    train_category VARCHAR(50),
    train_number VARCHAR(50),
    destination VARCHAR(100) NOT NULL,
    delay_minutes INTEGER DEFAULT 0,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
