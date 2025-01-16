DROP TABLE IF EXISTS parameter;

CREATE TABLE IF NOT EXISTS parameter (
    id SERIAL PRIMARY KEY,
    value1 FLOAT NOT NULL,
    value2 FLOAT NOT NULL
);

CREATE TABLE IF NOT EXISTS  weather_data (
    data_id SERIAL NOT NULL PRIMARY KEY, 
    temp FLOAT, 
    wind FLOAT, 
    humidity FLOAT, 
    pm2_5 FLOAT, 
    pm10 FLOAT, 
    last_updated TIMESTAMP
);