#!/usr/bin/env python
# -*- coding: utf8

from flask import Flask, session, Response, jsonify
from flask.ext.sqlalchemy import SQLAlchemy
import json
import os
import random
import string
import sys
import time
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/piotr/sqlite.db'
db = SQLAlchemy(app)
production = False

"""
    MODELS
"""

class Constituency(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)

    def __init__(self, name):
        self.name = name

    def __retr__(self):
        return '<Constituency %r>' % self.name

class Commission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    constituency_id = db.Column(db.Integer, db.ForeignKey('constituency.id'), nullable=False)
    name = db.Column(db.String(160), nullable=False)

    def __init__(self, constituency_id, name):
        self.constituency_id = constituency_id
        self.name = name

    def __retr__(self):
        return '<Commision %r>' % self.name

class Type(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)

    def __init__(self, name):
        self.name = name

    def __retr__(self):
        return '<Type %r>' % self.name

class List(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    constituency_id = db.Column(db.Integer, db.ForeignKey('constituency.id'), nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('type.id'), nullable=False)

    def __init__(self, constituency_id, type_id, name):
        self.name = name
        self.constituency_id = constituency_id
        self.type_id = type_id

    def __retr__(self):
        return '<List %r>' % self.name

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)
    surname = db.Column(db.String(60), nullable=False)
    list_id = db.Column(db.Integer, db.ForeignKey('list.id'), nullable=False)
    votes = db.Column(db.Integer)

    def __init__(self, name, surname, list_id):
        self.name = name
        self.surname = surname
        self.list_id = list_id

voter_type = db.Table('voter_type',
    db.Column('voter_id', db.Integer, db.ForeignKey('voter.id')),
    db.Column('type_id', db.Integer, db.ForeignKey('type.id'))
)

class Voter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_number = db.Column(db.String(160), nullable=False)
    passport_number = db.Column(db.String(160), nullable=False)
    pesel = db.Column(db.String(160), nullable=False)
    commission_id = db.Column(db.Integer, db.ForeignKey('commission.id'), nullable=False)
    types = db.relationship('Type', secondary=type, backref=db.backref('voter', lazy='dynamic'))

    def __init__(self, document_number, passport_number, pesel, commission_id):
        self.document_number = document_number
        self.passport_number = passport_number
        self.pesel = pesel
        self.commission_id = commission_id

    def voter_types(self):
        return self.types

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    random = db.Column(db.String(64), unique=True, nullable=False)
    voter_id = db.Column(db.Integer, db.ForeignKey('voter.id'), nullable=False)
    expires = db.Column(db.Integer, nullable=False)

    def __init__(self, voter_id):
        self.random = ''.join(random.choice(string.digits + string.ascii_letters) for _ in range(64))
        self.voter_id = voter_id
        self.expires = int(time.time())

"""
    PROPERTIES
"""

errors = {
    "603" : "Brak autoryzacji, nieprawidłowy identyfikator sesji.",
    "604" : "Wyborca został autoryzowany wcześniej.",
    "605" : "Numer PESEL nie istnieje w bazie danych.",
    "606" : "Numer drugiego dokumentu (dowód osobisty lub paszport) nie zgadza się."
}

"""
    HELPERS
"""

def return_json(data):
    """ Zwraca kod JSON """
    data["status"] = "OK"
    return Response(json.dumps(data), status=200, mimetype='application/json')

def error(errno):
    """ Zwraca błąd o numerze podanym jako parametr """
    data = {
        "status" : "ERROR",
        "message" : errors[str(errno)],
        "errno" : errno
    }
    return Response(json.dumps(data), status=200, mimetype='application/json')

"""
    CONTROLLERS
"""

@app.route("/testing_data")
def testing_data():
    # zabezpiezpieczenie przed dodaniem testowych danych na serwerze produkcyjnym
    if production != False:
        return error(600)

    # utworzenie wszystkich niezbędnych tabel
    db.create_all()

    # dane do testowania
    constituency_data = [
        u"Warszawski Okręg Wyborczy",
        u"Poznański Okręg Wyborczy",
        u"Wrocławski Okręg Wyborczy"
    ]

    commision_data = [
        u"Okręgowa Komisja Wyborcza Mokotów",
        u"Okręgowa Komisja Wyborcza Żoliborz",
        u"Okręgowa Komisja Wyborcza Praga Północ",
        u"Okręgowa Komicja Wyborcza Praga Południe"
    ]

    type_data = [
        u"Wybory Parlamentarne 2015"
    ]

    list_data = [
        u"Polska Partia Świętego Mikołaja",
        u"Porozumienie \"Lepsze jutro było wczoraj\"",
        u"Prawo i Lewo"
    ]

    candidate_data = [
        [ u"Kaczor", u"Donald" ],
        [ u"Myszka", u"Miki" ],
        [ u"Mikołaj", u"Święty" ]
    ]

    # dodanie danych do testowania
    for data in constituency_data:
        constituency = Constituency(data)
        db.session.add(constituency)

    for data in commision_data:
        commission = Commission(1, data)
        db.session.add(commission)

    for data in type_data:
        type = Type(data)
        db.session.add(type)

    for data in list_data:
        list = List(1, 1,data)
        db.session.add(list)

    for x in range(0, 20):
        document_number = ''.join(random.choice(string.ascii_uppercase) for _ in range(3)) + ''.join(random.choice(string.digits) for _ in range(6))
        pesel = "910101" + ''.join(random.choice(string.digits) for _ in range(5))
        voter = Voter(str(document_number), "", pesel, 1)
        db.session.add(voter)

    for data in candidate_data:
        candidate = Candidate(data[0], data[1], 1)
        db.session.add(candidate)

    db.session.commit()

    return 'OK'


@app.route("/auth/<document_number>/<pesel>")
def auth(document_number, pesel):
    """

    :param document_number: numer dowodu lub paszportu
    :param pesel: numer pesel
    :return: { "status" : "ERROR", "message" : "(...)", "errno" : "603" }
    :return: { "status" : "OK", "session_id" : "(...)", "types" : {TODO} }
    """
    voter = Voter.query.filter_by(pesel=pesel).first()
    # sprawdzamy, czy użytkownik istnieje
    if voter is None:
        return error(605)
    # sprawdzamy drugi dokument
    if voter.document_number != document_number and voter.passport_number != document_number:
        return error(606)
    # sprawdzamy, czy nie zalogowano wcześniej
    #TODO
    # generujemy identyfikator sesji (będzie w session_record.random)
    session_record = Session(voter.id)
    db.session.add(session_record)
    db.session.commit()
    # zwracamy JSON
    return return_json({
        "session_id" : session_record.random,
        "commission_id" : voter.commission_id,
        "types" : voter.voter_types()
    })

@app.route("/get_lists/<int:constituency_id>/<int:type_id>")
def get_lists(constituency_id, type_id):
    #TODO zwraca listy wyborcze wg okręgu w którym głosuje wyborca
    pass

@app.route("/get_candidates/<int:list_id>")
def get_candidates(list_id):
    #TODO zwraca listę kandydatów z listy wyborczej
    pass

@app.route("/vote/<int:candidate_id>")
def vote(candidate_id):
    #TODO wyświetla czy udało się oddać głos
    pass

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True)