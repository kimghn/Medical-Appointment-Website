from flask import Flask, render_template, redirect, url_for, request, jsonify, session, flash
from config import Config
from models import db, User, Appointment
from datetime import datetime, timedelta
import jdatetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config.from_object(Config)
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'status': 'error', 'message': 'این ایمیل قبلاً ثبت شده است. لطفاً وارد شوید یا از ایمیل دیگری استفاده کنید.'})
        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'ثبت نام با موفقیت انجام شد'})
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id 
            return jsonify({'status': 'success', 'message': 'ورود موفقیت‌آمیز بود!'})
        else:
            return jsonify({'status': 'error', 'message': 'ایمیل یا رمز عبور اشتباه است. دوباره تلاش کنید.'})
    return render_template('login.html')

@app.route('/home')
def home():
    return render_template('home.html')

def parse_birthdate(birthdate):
    if birthdate:
        year, month, day = map(int, birthdate.split('-'))
        return year, month, day
    return None, None, None

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    user_info = User.query.get(user_id)
    if request.method == 'POST':
        name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        national_id = request.form.get('national_id')
        phone_number = request.form.get('phone')
        birth_day = request.form.get('birth_day')
        birth_month = request.form.get('birth_month')
        birth_year = request.form.get('birth_year')
        if not all([name, last_name, national_id, phone_number, birth_day, birth_month, birth_year]):
            error = "لطفاً تمام فیلدها را پر کنید."
            return render_template('dashboard.html', error=error, user_info=user_info, 
                                   birth_year=birth_year, birth_month=birth_month, birth_day=birth_day)
        birthdate = f"{birth_year}-{birth_month.zfill(2)}-{birth_day.zfill(2)}"
        user_info.name = name
        user_info.last_name = last_name
        user_info.national_id = national_id
        user_info.phone_number = phone_number
        user_info.birthdate = birthdate
        db.session.commit()
        success = "اطلاعات با موفقیت به‌روزرسانی شد."
        birth_year, birth_month, birth_day = parse_birthdate(user_info.birthdate)
        return render_template('dashboard.html', success=success, user_info=user_info,
                               birth_year=birth_year, birth_month=birth_month, birth_day=birth_day)
    birth_year, birth_month, birth_day = parse_birthdate(user_info.birthdate)
    return render_template('dashboard.html', user_info=user_info, 
                           birth_year=birth_year, birth_month=birth_month, birth_day=birth_day)

@app.context_processor
def inject_timedelta():
    return {'timedelta': timedelta}

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    today = jdatetime.date.today()
    if request.method == 'POST':
        appointment_date_str = request.form['appointment_day']
        appointment_time_str = request.form['appointment_time']
        appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
        appointment_time = datetime.strptime(appointment_time_str, '%H:%M').time()
        weekday = appointment_date.weekday()
        if weekday not in [5, 0, 2]:
            return render_template('booking.html', today=today)
        if not (appointment_time.hour >= 10 and appointment_time.hour < 15 and appointment_time.minute % 10 == 0):
            return render_template('booking.html', today=today)
        user_id = session.get('user_id')
        if user_id is None:
            return redirect(url_for('login'))
        existing_appointment = Appointment.query.filter_by(date=appointment_date, time=appointment_time).first()
        if existing_appointment:
            error_message = "این وقت قبلاً رزرو شده است، لطفاً زمان دیگری را انتخاب کنید."
            return render_template('booking.html', today=today, error=error_message) 
        new_appointment = Appointment(user_id=user_id, date=appointment_date, time=appointment_time)
        db.session.add(new_appointment)
        db.session.commit()
        return redirect(url_for('followup', appointment_id=new_appointment.id))
    upcoming_dates = []
    for day in range(30):
        shamsi_date = today + jdatetime.timedelta(days=day)
        if shamsi_date.weekday() in [5, 0, 2]:
            upcoming_dates.append({
                'shamsi': shamsi_date.strftime('%Y-%m-%d'),
                'gregorian': shamsi_date.togregorian()
            })
    upcoming_appointments = Appointment.query.filter(Appointment.date >= today.togregorian()).all()
    booked_slots = {(appointment.date, appointment.time) for appointment in upcoming_appointments}
    return render_template('booking.html', today=today, upcoming_dates=upcoming_dates, booked_slots=booked_slots)

@app.route('/followup')
def followup():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    appointments = Appointment.query.filter_by(user_id=user_id).order_by(Appointment.date.desc(), Appointment.time.desc()).all()
    appointment_data = []
    for appointment in appointments:
        shamsi_date = jdatetime.date.fromgregorian(year=appointment.date.year, month=appointment.date.month, day=appointment.date.day)
        shamsi_time = appointment.time.strftime('%H:%M')
        status_text = "مراجعه شده" if appointment.status == 1 else "رزرو شده"
        appointment_data.append({
            'id': appointment.id,
            'date': shamsi_date,
            'time': shamsi_time,
            'status_text': status_text,
            'status': appointment.status
        })
    return render_template('followup.html', appointments=appointment_data)

@app.route('/cancel_appointment/<int:appointment_id>', methods=['POST'])
def cancel_appointment(appointment_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    appointment = Appointment.query.get(appointment_id)
    if appointment and appointment.user_id == user_id:
        db.session.delete(appointment)
        db.session.commit()
    return redirect(url_for('followup'))

@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)

with app.app_context():
    db.create_all()