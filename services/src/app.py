from __future__ import print_function
from mysql.connector import errorcode
from flask import Flask, jsonify, request, Response, render_template, flash, redirect
from time import sleep
from wtforms import Form, StringField, IntegerField, FloatField, SelectField, validators
from wtforms.fields.html5 import DateField

import fileinput
import json
import mysql.connector
import sys
from uuid import uuid4

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

class CancelReservationForm(Form):
    resId = StringField('For cancelling a reservation, enter its ID:')

current_user = ''

@app.route('/', methods=['GET', 'POST', 'PUT'])
def home():
    form1 = LogInForm(request.form)

    if request.method == 'POST' and form1.validate():
        try:
            res = cursor.callproc('searchUser', (form1.passwd.data, form1.username.data, None, None))
        except mysql.connector.Error as err:
            print(err)
            return Response('An exception occurred: ' + str(err))
        if res[2]:
            global current_user
            current_user = res[1]
            flash('Welcome, ' + res[3] + '!')
        else:
            flash('Invalid credentials')

    return render_template('index.html', form1=form1)


@app.route('/signup.html', methods=['GET','POST'])
def create_account():
    form = SignUpForm(request.form)
    if request.method == 'POST' and form.validate():
        try:
            cursor.callproc('createUser', (form.username.data, form.password.data, form.name.data, form.address.data, form.mail.data, form.phone.data))
            connection.commit()
        except mysql.connector.Error as err:
            print(err)
            return Response('An exception occurred: ' + str(err))
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
            cursor.callproc('createTutor', (tutor_id, current_user, form.subject.data, form.experience.data, form.channel.data, form.price.data))
            connection.commit()
        except mysql.connector.Error as err:
            print(err)
            return Response('An exception occured: ' + str(err))
        flash('Great! You are officialy registered as a mentor!')
    if request.method == 'POST' and not form.validate():
        flash('Invalid fields')
    return render_template('host.html', form=form)


@app.route('/guest.html', methods=['GET', 'POST'])
def search_locations():
    form = SearchFilterForm(request.form)

    if request.method == 'POST' and form.validate():
        subject_filter = False
        town_filter = False
        maxprice_filter = False

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
            cursor.callproc('getTutors', (subject_filter, town_filter, maxprice_filter,\
                    form.subject.data, form.town.data, maxprice_num))
            results = cursor.stored_results()
            for result in results:
                entries = result.fetchall()
                for entry in entries:
                    entry_str = ''
                    for field in entry:
                        entry_str += str(field) + ' '
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
