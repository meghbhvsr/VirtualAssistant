from flask import Flask, request, render_template, redirect, url_for, jsonify, session
import openai
import datetime
from datetime import datetime, timedelta
from flask_session import Session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import MySQLdb.cursors, re, hashlib
import pyautogui
import time
from dotenv import load_dotenv
import os

openai.api_key = os.getenv('API_KEY')
load_dotenv()
app = Flask(__name__)
app.config['SESSION_TYPE'] = os.getenv('SESSION_TYPE')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] =  os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] =  os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] =  os.getenv('MYSQL_DB')
Session(app)
mysql = MySQL(app)
global_delete = 0
reminders = []

@app.route('/', methods=['GET', 'POST'])
def login():
    msg = ''
    # Check if username and password have been entered
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        account = cursor.fetchone()
        # if the username and password user enters matches an account in the database
        if account:
            # Create session data using their account info
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            cursor.execute('SELECT * FROM reminders WHERE user_id = %s', (account['id'],))
            reminders = cursor.fetchall()
            session['reminders'] = reminders
            # Redirect to home page
            return redirect(url_for('home'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    else:
        msg = 'Enter a username and/or password!'
    return render_template('index.html', msg=msg)

@app.route('/pythonlogin/register', methods=['GET', 'POST'])
def register():
    msg = ''
    # Check if username and password have been entered
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesn't exist, and the form data is valid, so insert the new account into the accounts table
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email,))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)

@app.route('/profile')
def profile():
    # Check if the user is logged in
    if 'loggedin' in session:
        # Gather account info for user
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not logged in redirect to login page
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('reminders', None)
    return redirect(url_for('login'))

@app.route('/get_reminders/<int:user_id>', methods=['GET'])
def get_user_reminders(user_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM reminders WHERE user_id = %s', (user_id,))
    reminders = cursor.fetchall()
    reminder_list = []
    for reminder in reminders:
        if isinstance(reminder['date'], datetime):
            date_str = reminder['date'].strftime('%Y-%m-%d')
        else:
            date_str = str(reminder['date'])
        if isinstance(reminder['time'], timedelta):
            total_seconds = int(reminder['time'].total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{hours:02}:{minutes:02}"
        elif isinstance(reminder['time'], str):
            time_str = reminder['time']
        else:
            time_str = str(reminder['time'])
        reminder_list.append({
            'id': reminder['id'],
            'user_id': reminder['user_id'],
            'task': reminder['task'],
            'date': date_str,
            'time': time_str,
            'duration':reminder['duration']
        })
    return jsonify(reminder_list)

def view_reminders():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM reminders WHERE user_id = %s', (session['id'],))
    reminders_list = cursor.fetchall()
    if reminders_list:
        response = "Upcoming reminders:\n"
        for reminder in reminders_list:
            word_form = reminder['date'].strftime("%A, %B %d, %Y")
            response += f"You have a {reminder['task']} on {word_form} at {reminder['time']} that lasts {reminder['duration']} minutes.\n"
    else:
        response = "You have no upcoming reminders."
    return response

def answer_question(question):
    response = openai.chat.completions.create (
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": "You are a knowledgeable and helpful virtual assistant."},
            {"role": "user", "content": question}
        ]
    )
    return response.choices[0].message.content

@app.route('/home')
def home():
    if 'loggedin' in session:
        return render_template('home.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/virtual-assistant')
def virtual_assistant():
    return render_template('assistant.html')

@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

@app.route('/get_user_id')
def get_user_id():
    if 'id' in session:
        return jsonify({"user_id": session['id']})
    else:
        return jsonify({"message": "User not logged in"}), 401

def delete_all_reminders():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM reminders WHERE user_id = %s', (session['id'],))
    mysql.connection.commit()
    session['reminders'] = []

def delete_single_reminder(user_input):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM reminders WHERE user_id = %s and task = %s', (session['id'], user_input))
    if cursor.rowcount > 0:
        mysql.connection.commit()
        session['reminders'] = [rem for rem in session['reminders'] if rem['task'] != user_input]
        global_delete = 0
        return "Reminder deleted"
    else:
        return "Reminder not found"



@app.route('/chat', methods=['POST'])
def chat():
    global global_delete
    user_input = request.form['message']
    reminders_list = session['reminders']
    print(user_input)
    print(reminders_list)
    if global_delete == 1:
        print("1")
        global_delete = 0
        return jsonify({"response": delete_single_reminder(user_input)})

    if is_view_reminders(user_input):
        print("2")
        response = view_reminders()
    elif is_create_reminder(user_input):
        print("3")
        response = "Fill up the reminder form below"
    elif is_clear_all_reminders(user_input):
        print("4")
        delete_all_reminders()
        response = "Ok, cleared all reminders."
    elif is_clear_single_reminder(user_input):
        print("5")
        global_delete = 1
        response = "Write the task of the reminder you want to delete"
    elif is_email(user_input):
        print("6")
        response = "Sure, can you fill up this form"
    else:
        print("7")
        response = answer_question(user_input)

    return jsonify({"response": response})

def is_view_reminders(user_input):
    return 'reminders' in user_input.lower() and 'delete' not in user_input.lower() and 'clear' not in user_input.lower()

def is_create_reminder(user_input):
    return 'reminder' in user_input.lower() and 'delete' not in user_input.lower() and 'clear' not in user_input.lower()

def is_clear_all_reminders(user_input):
    return 'clear' in user_input.lower() or 'delete' in user_input.lower() and 'reminders' in user_input.lower() and 'all' in user_input.lower()

def is_clear_single_reminder(user_input):
    return  'clear'  in user_input.lower() or 'delete' in user_input.lower() and 'reminder' in user_input.lower()

def is_email(user_input):
    return 'email' in user_input.lower() or 'e-mail' in user_input.lower()

@app.route('/set_reminder', methods=['POST'])
def set_reminder():
    data = request.get_json()
    task = data.get('task')
    date = data.get('date')
    time = data.get('time')
    duration = data.get('duration')

    reminder = {
        'task': task,
        'number-date': date,
        'date': datetime.strptime(date, "%Y-%m-%d"),
        'time': time,
        'duration': duration
    }
    #reminders.append(reminder)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('INSERT INTO reminders (user_id, task, date, time, duration) VALUES (%s, %s, %s, %s, %s)', (session['id'], task, date, time, duration))
    mysql.connection.commit()

    # Update session reminders
    cursor.execute('SELECT * FROM reminders WHERE user_id = %s', (session['id'],))
    reminders = cursor.fetchall()
    session['reminders'] = reminders
    print(session['reminders'])
    message = "Reminder set Successfully"
    return jsonify({'message': message})

@app.route('/send_email', methods=['POST'])
def send_email():
    data = request.get_json()
    recipientEmail = data.get('recipientEmail')
    subjectData = data.get('emailSubject')
    question = "Write an email on " + subjectData + "With the senders name being" + session['username']
    emailBody = answer_question(question)
    pyautogui.hotkey('winleft')
    time.sleep(1)
    
    # Type 'Mail' to search for the Mail app
    pyautogui.typewrite('Mail', interval=0.1)
    time.sleep(1)
    
    # Press 'Enter' to open the Mail app
    pyautogui.press('enter')
    time.sleep(5)

    pyautogui.click(100, 100)  # Adjust coordinates as necessary
    time.sleep(2)
    
    # Type the recipient's email address
    pyautogui.typewrite(recipientEmail, interval=0.1)
    pyautogui.press('tab')  # Move to subject field
    pyautogui.press('tab')
    pyautogui.press('tab')
    pyautogui.press('tab')
    time.sleep(1)
    
    # Type the email subject
    pyautogui.typewrite(subjectData, interval=0.1)
    pyautogui.press('tab')  # Move to body field
    time.sleep(1)
    
    # Type the email body
    pyautogui.typewrite(emailBody, interval=0.1)

if __name__ == "__main__":
    app.run(debug=True)