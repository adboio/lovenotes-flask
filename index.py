from Adafruit_Thermal import *
from datetime import datetime
from flask import Flask, request
import pymysql.cursors
from dotenv import load_dotenv
import os
import subprocess

load_dotenv()

app = Flask(__name__)
printer = Adafruit_Thermal("/dev/serial0", 19200, timeout=5)
printer.setTimes(1000, 2100)

subprocess.run([f"NGROK_AUTHTOKEN={os.environ.get('NGROK_AUTH')} ngrok http --domain=lovenotes.ngrok.io 127.0.0.1:5000"], shell=True)

@app.route('/', methods=['POST'])
def incoming_sms():
    print(request.form)

    from_number = request.form['From']
    if (from_number not in get_allowed_numbers()):
        print('illegal1!')
        return

    recipient = get_recipient(from_number)
    if recipient is None:
        print('illegal2!')
        return

    connection = create_connection()
    cursor = connection.cursor()
    
    try:
        message_body = request.form['Body']
        log(cursor, 'INFO', f'New message from {from_number}: {message_body}')
        print_message(message_body, from_number)
    except Exception as e:
        print(e)
        log(cursor, 'ERROR', 'something happened :(')
    finally:
        cursor.close()
        connection.close()

    return "ok"

LOG_LEVEL_MAP = {
    'INFO': 1,
    'WARN': 2,
    'ERROR': 3
}

PEOPLE_MAP = {
    '+19102602599': {
        'is': 'adam',
        'to': 'rose'
    }
}

def get_allowed_numbers():
    return ['+19102602599']


def get_recipient(from_number):
    return PEOPLE_MAP[from_number]['to']

def get_from(from_number):
    return PEOPLE_MAP[from_number]['is']

def create_connection():
    return pymysql.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASS'),
        database=os.environ.get('DB_NAME'),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def log(cursor, log_level, message):
    log_query = '''
        INSERT INTO notes_log
        (log_level, log_level_name, log)
        VALUES (%s, %s, %s)
    '''
    cursor.execute(log_query, (LOG_LEVEL_MAP[log_level], log_level, message))

def print_message(body, from_number):
    # start with some slack
	printer.feed(2)

	# center justify
	printer.justify('C')

	# print box top
	printer.println("~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~")

	# print message
	printer.println(body)

	# print box bottom
	printer.feed(1)
	printer.println("~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~")

	# print from
	printer.feed(1)
	printer.println(f"- {get_from(from_number)} -")

	printer.println(datetime.now().strftime('%-I:%M%p on %b %-d, %Y'))

	printer.feed(5)

if __name__ == "__main__":
    app.run()