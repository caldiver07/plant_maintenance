from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime, timedelta
import calendar

app = Flask(__name__, template_folder='templates')

def init_db():
    with sqlite3.connect('plants.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                species TEXT,
                watering_frequency INTEGER NOT NULL,
                last_watered DATE
            )
        ''')
        conn.commit()

@app.route('/')
def index():
    with sqlite3.connect('plants.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM plants')
        plants = cursor.fetchall()
        
        plant_list = []
        for plant in plants:
            last_watered = datetime.strptime(plant[4], '%Y-%m-%d').date()
            next_watering = last_watered + timedelta(days=plant[3])
            days_until_watering = (next_watering - datetime.now().date()).days
            plant_list.append({
                'id': plant[0],
                'name': plant[1],
                'species': plant[2],
                'watering_frequency': plant[3],
                'last_watered': last_watered.strftime('%B %d, %Y'),
                'next_watering': next_watering,
                'next_watering_str': next_watering.strftime('%B %d, %Y'),
                'days_until_watering': days_until_watering,
                'needs_water': days_until_watering <= 0
            })

    # Calendar Data
    now = datetime.now()
    cal = calendar.Calendar()
    month_days = cal.monthdatescalendar(now.year, now.month)
    
    # Create a dictionary to hold watering events
    watering_schedule = {}
    for plant in plant_list:
        # Show upcoming waterings for the next 30 days for the calendar
        next_date = plant['next_watering']
        for _ in range(30 // plant['watering_frequency'] + 1):
            if next_date.month == now.month and next_date.year == now.year:
                if next_date.day not in watering_schedule:
                    watering_schedule[next_date.day] = []
                watering_schedule[next_date.day].append(plant['name'])
            next_date += timedelta(days=plant['watering_frequency'])


    return render_template('index.html', 
                           plants=plant_list, 
                           month_days=month_days, 
                           today=now.day,
                           current_month_name=now.strftime('%B'),
                           current_year=now.year,
                           watering_schedule=watering_schedule)

@app.route('/add', methods=['POST'])
def add_plant():
    name = request.form.get('name')
    species = request.form.get('species')
    watering_frequency = request.form.get('watering_frequency')
    last_watered = datetime.now().strftime('%Y-%m-%d')

    with sqlite3.connect('plants.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO plants (name, species, watering_frequency, last_watered) VALUES (?, ?, ?, ?)',
            (name, species, watering_frequency, last_watered)
        )
        conn.commit()

    return redirect(url_for('index'))

@app.route('/water/<int:plant_id>')
def water_plant(plant_id):
    last_watered = datetime.now().strftime('%Y-%m-%d')
    with sqlite3.connect('plants.db') as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE plants SET last_watered = ? WHERE id = ?', (last_watered, plant_id))
        conn.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:plant_id>')
def delete_plant(plant_id):
    with sqlite3.connect('plants.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM plants WHERE id = ?', (plant_id,))
        conn.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0')
