from flask import Flask, request, send_file, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import psycopg2
from sqlalchemy import create_engine, text
import matplotlib.pyplot as plt
from datetime import datetime
import base64
import io

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://xfregnil:YSq_rH6EbdiUa61ZDEkud1egutaJKd3j@kandula.db.elephantsql.com/xfregnil'
db = SQLAlchemy(app)
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])

with engine.begin() as conn:
    with open('schema.sql', 'r') as script_file:
        sql_script = script_file.read()
        result = conn.execute(text(sql_script))
        conn.commit()

class WeatherData(db.Model):
    __tablename__ = 'weather_data'
    data_id = db.Column(db.Integer, primary_key=True)
    temp = db.Column(db.Float, nullable=False)
    wind = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    pm2_5 = db.Column(db.Float, nullable=False)
    pm10 = db.Column(db.Float, nullable=False)
    last_updated = db.Column(db.DateTime, nullable=False)

    def get_formatted_date(self):
        if isinstance(self.last_updated, str):
            date_obj = datetime.strptime(self.last_updated, '%Y-%m-%d %H:%M:%S')
        else:
            date_obj = self.last_updated
        return date_obj.strftime('%Y-%m-%d %H:%M:%S')
    def __repr__(self):
        return f'<WeatherData {self.data_id}>'

class Parameter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value1 = db.Column(db.Float, nullable=False)
    value2 = db.Column(db.Float, nullable=False)

with app.app_context():
    db.create_all()


def create_temperature_chart(weather_data_list):
    parameter = Parameter.query.first()
    alarm_value = parameter.value1 if parameter else 0
    weather_data_list = weather_data_list[-10:]

    times = [record.last_updated for record in weather_data_list]
    temperatures = [record.temp for record in weather_data_list]
    
    formatted_times = [time.strftime('%m-%d %H:%M') for time in times]

    plt.figure(figsize=(10, 6))
    plt.plot(times, temperatures, label='Temperatura (°C)', color='tab:blue')
    plt.axhline(y=alarm_value, color='red', linestyle='--', label=f'Alarm value: {alarm_value}°C')
    plt.text(times[0], alarm_value + 1, 'Alarm value', color='red', fontsize=12)
    plt.xticks(times, formatted_times, rotation=45)
    plt.xlabel('Czas')
    plt.ylabel('Temperatura (°C)')
    plt.title('Temperatura w czasie')
    plt.tight_layout()
    plt.legend()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode('utf8')
    return img_base64

def create_humidity_chart(weather_data_list):
    parameter = Parameter.query.first()
    alarm_value = parameter.value2 if parameter else 0 
    weather_data_list = weather_data_list[-10:]

    times = [record.last_updated for record in weather_data_list]
    humidity = [record.humidity for record in weather_data_list]
    
    formatted_times = [time.strftime('%m-%d %H:%M') for time in times]
    
    plt.figure(figsize=(10, 6))
    plt.plot(times, humidity, label='Wilgotność (%)', color='tab:green')
    plt.axhline(y=alarm_value, color='red', linestyle='--', label=f'Alarm value: {alarm_value}%')
    plt.text(times[0], alarm_value + 1, 'Alarm value', color='red', fontsize=12)
    plt.xticks(times, formatted_times, rotation=45)
    plt.xlabel('Czas')
    plt.ylabel('Wilgotność (%)')
    plt.title('Wilgotność w czasie')
    plt.tight_layout()
    plt.legend()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode('utf8')
    return img_base64

@app.route('/get-weather-data', methods=['GET'])
def get_weather_data():
    weather_data_list = WeatherData.query.all()
    data = [{
        'data_id': record.data_id,
        'temp': record.temp,
        'wind': record.wind,
        'humidity': record.humidity,
        'pm2_5': record.pm2_5,
        'pm10': record.pm10,
        'last_updated': record.last_updated.strftime('%Y-%m-%d %H:%M:%S')
    } for record in weather_data_list]
    return jsonify(data)

@app.route('/')
def home():
    weather_data_list = WeatherData.query.all()

    chart_temp = create_temperature_chart(weather_data_list)
    chart_humidity = create_humidity_chart(weather_data_list)
    return render_template('index.html', chart_temp=chart_temp, chart_humidity=chart_humidity)

@app.route('/changeParameter', methods=['GET', 'POST'])
def change_parameter():
    if request.method == 'POST':
        value_temperature = request.form.get('value_temperature')
        value_PM10 = request.form.get('value_PM10')
        try:
            value_tempf = float(value_temperature)
            value_PM10f = float(value_PM10)
            if value_tempf <= 0 or value_PM10f <= 0:
                return jsonify({"error": "Each value must be positive"}), 400
            
            db.session.query(Parameter).delete()
            params = Parameter(value1=value_tempf, value2=value_PM10f)
            db.session.add(params)
            db.session.commit()

            return redirect(url_for('home')) 
        except ValueError:
            return jsonify({"error": "Wrong values"}), 400
    return send_file('changeParameter.html')

if __name__ == '__main__':
    app.run(debug=True)
