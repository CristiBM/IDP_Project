from __future__ import print_function
from mysql.connector import errorcode
from flask import Flask, jsonify, request, Response, render_template, flash, redirect
from time import sleep
from wtforms import Form, StringField, IntegerField, FloatField, SelectField, SubmitField, validators
from wtforms.fields.html5 import DateField

import fileinput
import json
import mysql.connector
import redis
import sys
from uuid import uuid4

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

app = Flask(__name__)
app.secret_key = 'Shut up, Meg!'

config = {
        'user': 'root',
        'password': 'root',
        'host': 'db',
        'port': '3306',
        'database': 'tutorFinder'
    }

DB_NAME = 'tutorFinder'

# waiting for the database to initialize
sleep(15)

cache = redis.Redis(host='redis', port=6379, password='root')

try:
    connection = mysql.connector.connect(**config)
    connection.start_transaction(isolation_level='READ COMMITTED')
except mysql.connector.Error as err:
    print("Something went wrong: {}".format(err))
    exit(1)

cursor = connection.cursor()
try:
    cursor.execute("USE {}".format(DB_NAME))
except mysql.connector.Error as err:
    print(err)
    exit(1)


class LogInForm(Form):
    username = StringField('Enter your User ID and password:', [validators.Length(max=40)])
    passwd = StringField('', [validators.Length(max=40)])

class SignUpForm(Form):
    name = StringField('Your full name:', [validators.Length(min=4, max=30)])
    address = StringField('Your town/city of residence:', [validators.Length(max=40)])
    mail = StringField('Your email address:', [validators.Email()])
    phone = StringField('Your phone number:', [validators.Length(min=10, max=10)])
    username = StringField('A preferred username:', [validators.Length(min=6, max=20)])
    password = StringField('Password', [validators.Length(min=6)])

class HostForm(Form):
    subject = StringField('The name of the subject:', [validators.Length(min=4)])
    experience = IntegerField('Years of experience in the field:')
    channel = SelectField('Way of communication:', choices=[('AtResidence', 'AtResidence'), ('Online', 'Online')])
    price = FloatField('The price per hour:')

class SearchFilterForm(Form):
    subject = StringField('Subject:', [validators.Length(max=30)])
    town = StringField('Town:', [validators.Length(max=20)])
    maxprice = StringField('Max price:', [validators.Length(max=20)])
    Tutor = SubmitField("Tutor")

class CancelReservationForm(Form):
    resId = StringField('For cancelling a reservation, enter its ID:')

current_user = ''
current_user_name = ''

@app.route('/', methods=['GET', 'POST', 'PUT'])
def home():
    form1 = LogInForm(request.form)
    welcome = 0
    if request.method == 'POST' and form1.validate():
        found = False
        realName = ''
        try:
            # First we look in the cache
            password = cache.hget("userName_passwdH", form1.username.data)
            if password and (str(password, 'utf-8') == form1.passwd.data):
                found = True
                realName = str(cache.hget("userName_realnameH", form1.username.data), 'utf-8')
                eprint('<<<Taking it from the cache>>Real name is ' + realName)
            # No luck so we have to go to the backend DB
            else:
                eprint('<<<Not in the cache>>>')
                res = cursor.callproc('searchUser', (form1.passwd.data, form1.username.data, None, None))
                found = res[2]
                realName = res[3]
                # Since we found it here, we also bring it into cache
                if found:
                    eprint('Putting it in cache')
                    cache.hset("userName_passwdH", form1.username.data, form1.passwd.data)
                    cache.hset("userName_realnameH", form1.username.data, realName)
        except mysql.connector.Error as err:
            print(err)
            return Response('An exception occurred: ' + str(err))
        
        if found:
            global current_user
            global current_user_name
            current_user = form1.username.data
            current_user_name = realName
            flash('Welcome, ' + realName + '!')
        # Not in cache, not in DB.. you leave me no choice
        else:
            flash('Invalid credentials')
        welcome = 1

    studentsFound = 0
    if current_user:
        try:
            # in res[2] we may find the tutorId corresponding to the current user
            res = cursor.callproc('searchTutor', (current_user, None, None))
            if res[1]:
                cursor.callproc('getMatches', (res[2],))
                for result in cursor.stored_results():
                    for entry in result.fetchall():
                        entry_str = ''
                        for field in entry:
                            entry_max_len = 40
                            entry_str += str(field)

                            # assuring some alignment
                            while (entry_max_len - len(str(field)) - 5) > 0:
                                entry_str += '\t'
                                entry_max_len -= 4
                        studentsFound = 1
                        flash(entry_str)
        except mysql.connector.Error as err:
                print(err)
                return Response('An exception occurred: ' + str(err))



    return render_template('index.html', form1=form1, var=welcome, var2=studentsFound)


@app.route('/signup.html', methods=['GET','POST'])
def create_account():
    form = SignUpForm(request.form)
    if request.method == 'POST' and form.validate():
        try:
            data = {
                'username'  : form.username.data,
                'password'  : form.password.data,
                'name'      : form.name.data,
                'address'   : form.address.data,
                'mail'      : form.mail.data,
                'phone'     : form.phone.data
            }
            cache.rpush('queue:users', json.dumps(data))
        except Exception as e:
            print(e)
            return Response('An exception occured: ' + str(e))
        flash('Your account has been successfully created.')
    if request.method == 'POST' and not form.validate():
        flash('Invalid fields')
    return render_template('signup.html', form=form)


@app.route('/host.html', methods=['GET','POST'])
def register_host():
    form = HostForm(request.form)
    tutor_id = str(uuid4())
    if request.method == 'POST' and form.validate():
        try:
            data = {
                'tutid'     : tutor_id,
                'user'      : current_user,
                'subject'   : form.subject.data,
                'xp'        : form.experience.data,
                'channel'   : form.channel.data,
                'price'     : form.price.data
            }
            cache.rpush('queue:tutors', json.dumps(data))
        except Exception as e:
            print(e)
            return Response('An exception occured: ' + str(e))
        flash('Great! You are officialy registered as a mentor!')
    if request.method == 'POST' and not form.validate():
        flash('Invalid fields')
    return render_template('host.html', form=form)



'''Very important note:
The following dictionary is used for mapping the names of the tutors obtained
at the last tutor search performed with their associated ids.

This is used by the submit buttons mechanism used for the output of the search.
When one of those multiple buttons is pressed, here we receive the field name - Tutor -
and the value printed on the button - name subject... - This could have been easier
if we could have identified each button individually but since the number of output entries
cannot be known beforehand and no mechanism was found for generating corresponding Form
fields (FieldList cannot encapsulate SubmitFields), we had to base our solution on
parsing and interpreting the value of the button

Also, the tutor id is needed because in the database the tutor-student association is done
with the tutor id
'''
lastTutorSearchDict = {}

@app.route('/guest.html', methods=['GET', 'POST'])
def search_locations():
    global lastTutorSearchDict
    global current_user

    form = SearchFilterForm(request.form)
    if request.method == 'POST' and form.validate():
        subject_filter = False
        town_filter = False
        maxprice_filter = False

        if 'Tutor' in request.form or form.Tutor.data:
            tutorName = request.form['Tutor'].split("|")[0].strip()
            try:
                data = {
                    'tutor'     : lastTutorSearchDict[tutorName],
                    'student'   : current_user
                }
                cache.rpush('queue:matches', json.dumps(data))
            except Exception as e:
                print(e)
                return Response('An exception occured: ' + str(e))


        if form.subject.data:
            subject_filter = True
        if form.town.data:
            town_filter = True
        if form.maxprice.data:
            maxprice_filter = True
            maxprice_num = float(form.maxprice.data)
        else:
            maxprice_num = 0.0
        try:
            lastTutorSearchDict = {}
            cursor.callproc('getTutors', (subject_filter, town_filter, maxprice_filter,\
                    form.subject.data, form.town.data, maxprice_num))
            results = cursor.stored_results()
            for result in results:
                entries = result.fetchall()
                for entry in entries:
                    entry_str = ''
                    lastTutorSearchDict[entry[0].strip()] = entry[len(entry) - 1]
                    for (idx, field) in enumerate(entry[0:len(entry) - 1]):
                        entry_max_len = 40
                        entry_str += str(field)
                        if idx != len(entry) - 2:
                            # assuring some alignment
                            while (entry_max_len - len(str(field)) - 5) > 0:
                                entry_str += '\t'
                                entry_max_len -= 4
                            entry_str += '|'
                    entry_str += '$/hour'

                    flash(entry_str)

        except mysql.connector.Error as err:
            print(err)
            return Response('An exception occured: ' + str(err))

    return render_template('guest.html', form=form)


print('Initializing service...')


if __name__ == "__main__":
    # host option makes the server visible globally not just on the host
    app.run(debug=True, host='0.0.0.0')
