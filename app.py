from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime, timedelta
import calendar
import os
import click
from flask.cli import with_appcontext

app = Flask(__name__)

# --- Database Setup ---
def get_db_connection():
    """Creates a database connection."""
    db_path = '/app/data/plants.db'
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema."""
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS plants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                species TEXT,
                watering_frequency INTEGER NOT NULL,
                last_watered DATE
            )
        ''')
        conn.commit()

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

app.cli.add_command(init_db_command)

# --- Routes ---
@app.route('/')
def index():
    """Main route to display plants and calendar."""
    with get_db_connection() as conn:
        plants_result = conn.execute('SELECT * FROM plants').fetchall()

    plant_list = []
    now = datetime.now()

    for plant in plants_result:
        last_watered = datetime.strptime(plant['last_watered'], '%Y-%m-%d').date()
        next_watering = last_watered + timedelta(days=plant['watering_frequency'])
        days_until_watering = (next_watering - now.date()).days
        plant_list.append({
            'id': plant['id'],
            'name': plant['name'],
            'species': plant['species'],
            'watering_frequency': plant['watering_frequency'],
            'last_watered': last_watered.strftime('%B %d, %Y'),
            'next_watering': next_watering,
            'next_watering_str': next_watering.strftime('%B %d, %Y'),
            'days_until_watering': days_until_watering,
            'needs_water': days_until_watering <= 0
        })

    # --- Calendar Data ---
    cal = calendar.Calendar()
    month_days = cal.monthdatescalendar(now.year, now.month)
    
    watering_schedule = {}
    for plant in plant_list:
        next_date = plant['next_watering']
        for _ in range(60 // plant['watering_frequency'] + 1):
            if next_date.month == now.month and next_date.year == now.year:
                day_key = next_date.day
                if day_key not in watering_schedule:
                    watering_schedule[day_key] = []
                watering_schedule[day_key].append(plant['name'])
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
    """Adds a new plant to the database."""
    name = request.form.get('name')
    species = request.form.get('species')
    watering_frequency = request.form.get('watering_frequency')
    last_watered = datetime.now().strftime('%Y-%m-%d')

    with get_db_connection() as conn:
        conn.execute(
            'INSERT INTO plants (name, species, watering_frequency, last_watered) VALUES (?, ?, ?, ?)',
            (name, species, watering_frequency, last_watered)
        )
        conn.commit()
    return redirect(url_for('index'))

@app.route('/water/<int:plant_id>')
def water_plant(plant_id):
    """Updates the last watered date for a plant."""
    last_watered = datetime.now().strftime('%Y-%m-%d')
    with get_db_connection() as conn:
        conn.execute('UPDATE plants SET last_watered = ? WHERE id = ?', (last_watered, plant_id))
        conn.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:plant_id>')
def delete_plant(plant_id):
    """Deletes a plant from the database."""
    with get_db_connection() as conn:
        conn.execute('DELETE FROM plants WHERE id = ?', (plant_id,))
        conn.commit()
    return redirect(url_for('index'))
