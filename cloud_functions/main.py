from sqlalchemy import create_engine, Column, Float, DateTime, Integer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from flask import jsonify
import requests
import smtplib
from email.message import EmailMessage
import datetime
import logging
import functions_framework

Base = declarative_base()

class WeatherData(Base):
    __tablename__ = 'weather_data'
    data_id = Column(Integer, primary_key=True)
    temp = Column(Float, nullable=False)
    wind = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    pm2_5 = Column(Float, nullable=False)
    pm10 = Column(Float, nullable=False)
    last_updated = Column(DateTime, nullable=False)

class Parameter(Base):
    __tablename__ = 'parameter'
    id = Column(Integer, primary_key=True)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)

def get_engine():
    return create_engine("postgresql+psycopg2://xfregnil:YSq_rH6EbdiUa61ZDEkud1egutaJKd3j@kandula.db.elephantsql.com/xfregnil")

def save_weather_data(data):
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        weather_record = WeatherData(
            temp=data["temperature"],
            wind=data["wind"],
            humidity=data["humidity"],
            pm2_5=data["pm2_5"],
            pm10=data["pm10"],
            last_updated=datetime.datetime)
        session.add(weather_record)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def check_threshold_and_notify(data):
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        parameter = session.query(Parameter).first()
        if not parameter:
            logging.warning("No threshold parameters")
            return

        if data["temp_c"] > parameter.temperature or data["humidity"] > parameter.humidity:
            logging.info("Threshold exceeded")

            msg = EmailMessage()
            msg['Subject'] = 'Weather Alert'
            msg['From'] = 'gcp.projekt.mail@gmail.com'
            msg['To'] = 'mrogowski@student.agh.edu.pl'
            msg.set_content(f"Warning!\n"
                f"Temperature: {data['temperature']} (Threshold: {parameter.temperature})\n"
                f"Humidity: {data['humidity']} (Threshold: {parameter.humidity})")
            gmail_user = "gcp.projekt.mail@gmail.com"
            gmail_app_password = "gcpprojektmail"

            try:
                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(gmail_user, gmail_app_password)
                    server.send_message(msg)

                logging.info("Email sent successfully")
            except Exception as e:
                logging.error(f"Failed to send email: {e}")

    except Exception as e:
        logging.error(f"Error while checking thresholds: {e}")
    finally:
        session.close()


@functions_framework.http
def return_data(request):
    api_url = "http://api.weatherapi.com/v1/current.json?key=3309dc60d52d4a63ad6214517251601&q=Cracow&aqi=yes"
    try:
        response = requests.get(api_url)
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch data from API"}), 500

        data = response.json()
        save_weather_data(data)
        check_threshold_and_notify(data)
        return f"Data fetched, saved to the database, and thresholds checked.", 200
    except Exception as e:
        logging.error(f"Error in return_data: {e}")
        return jsonify({"error": str(e)}), 500
