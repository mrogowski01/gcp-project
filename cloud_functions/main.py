import os
import sqlalchemy
from sqlalchemy import create_engine, Column, Float, DateTime, Integer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from flask import jsonify, request
import requests
import datetime
import logging
import functions_framework
import psycopg2

def save_weather_data(data):
    db_uri = "postgresql+psycopg2://xfregnil:YSq_rH6EbdiUa61ZDEkud1egutaJKd3j@kandula.db.elephantsql.com/xfregnil"
    if not db_uri:
        raise ValueError("DB_URI environment variable not set.")
    try:
        engine = sqlalchemy.create_engine(db_uri)
        conn = engine.connect()
        print("Connection successful")
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        raise
    try:
        conn.execute(
            sqlalchemy.text(
                """
                INSERT INTO weather_data (temp, wind, humidity, pm2_5, pm10, last_updated)
                VALUES (:temperature, :wind, :humidity, :pm2_5, :pm10, :last_updated)
                """
            ),
            {
                "temperature": data["temperature"],
                "wind": data["wind"],
                "humidity": data["humidity"],
                "pm2_5": data["pm2_5"],
                "pm10": data["pm10"],
                "last_updated": datetime.datetime.now(),
            },
        )
        conn.commit()
        print("Data inserted successfully")
    except Exception as e:
        print(f"Error inserting data: {e}")
        raise
    finally:
        conn.close()

def return_data(request):
    api_url = "http://api.weatherapi.com/v1/current.json?key=3309dc60d52d4a63ad6214517251601&q=Cracow&aqi=yes"
    try:
        response = requests.get(api_url)
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch data from API"}), 500

        data = {
            "temperature": response.json()["current"]["temp_c"],
            "wind": response.json()["current"]["wind_kph"],
            "humidity": response.json()["current"]["humidity"],
            "pm2_5": response.json()["current"]["air_quality"]["pm2_5"],
            "pm10": response.json()["current"]["air_quality"]["pm10"],
        }
        logging.info(f"Fetched data: {data}")
        print(f"Fetched data: {data}")

        save_weather_data(data)
        print("Data fetched and saved successfully")
    except Exception as e:
        logging.error(f"Error in return_data: {e}")
        return jsonify({"error": str(e)}), 500
