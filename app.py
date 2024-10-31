import os
import random
import json
import socket

from datetime import datetime
from flask import Flask, request, make_response, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
dbhost = os.environ.get('DB_HOST', '')
dbport = os.environ.get('DB_PORT', '')
dbname = os.environ.get('DB_NAME', '')
dbuser = os.environ.get('DB_USER', '')
dbpass = os.environ.get('DB_PASS', '')
dbtype = os.environ.get('DB_TYPE', '')

if dbtype == 'mysql':
    dburi = dbtype + '://' + dbuser + ':' + dbpass + '@' + dbhost + ':' + dbport + '/' + dbname
elif dbtype == 'postgresql':
    dburi = dbtype + '://' + dbuser + ':' + dbpass + '@' + dbhost + ':' + dbport + '/' + dbname
else:
    dburi = 'sqlite:///' + os.path.join(basedir, 'data/app.db')

app.config['SQLALCHEMY_DATABASE_URI'] = dburi
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False

db = SQLAlchemy(app)

class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)
    question = db.Column(db.String(90))
    stamp = db.Column(db.DateTime)
    options = db.relationship('Option', backref='option', lazy='dynamic', overlaps="poll,options")

class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(30))
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'))
    poll = db.relationship('Poll', backref=db.backref('poll', lazy='dynamic'), overlaps="poll,options")
    votes = db.Column(db.Integer)

@app.route('/')
@app.route('/index.html')
def index():
    hostname = socket.gethostname()
    
    # Query the poll object within the request context
    poll = Poll.query.first()  # This fetcahes the first poll from the database
    
    # Pass the hostname and poll to the template
    return render_template('index.html', hostname=hostname, poll=poll)

@app.route('/vote.html', methods=['POST', 'GET'])
def vote():
    has_voted = False
    vote_stamp = request.cookies.get('vote_stamp')

    # Fetch the poll inside the function
    poll = Poll.query.first()
    
    if request.method == 'POST':
        has_voted = True
        vote = request.form['vote']
        if vote_stamp:
            print("This client has already voted! His vote stamp is: " + vote_stamp)
        else:
            print("This client has not voted yet!")
        
        voted_option = Option.query.filter_by(poll_id=poll.id, id=vote).first() 
        if voted_option:
            voted_option.votes += 1
            db.session.commit()

    options = Option.query.filter_by(poll_id=poll.id).all()        
    resp = make_response(render_template('vote.html', hostname=socket.gethostname(), poll=poll, options=options))
    
    if has_voted:
        vote_stamp = hex(random.getrandbits(64))[2:-1]
        print("Set cookie for voted")
        resp.set_cookie('vote_stamp', vote_stamp)
    
    return resp

@app.route('/results.html')
def results():
    # Fetch the poll inside the function
    poll = Poll.query.first()
    results = Option.query.filter_by(poll_id=poll.id).all()
    return render_template('results.html', hostname=socket.gethostname(), poll=poll, results=results)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        db.session.commit()
        hostname = socket.gethostname()
         
        print("Check if a poll already exists in db")
        poll = Poll.query.first()
        
        if poll:
            print("Restart the poll")
            poll.stamp = datetime.utcnow()
            db.session.commit()
        
        else:
            print("Load seed data from file")
            try: 
                with open(os.path.join(basedir, 'seeds/seed_data.json')) as file:
                    seed_data = json.load(file)
                    print("Start a new poll")
                    poll = Poll(seed_data['poll'], seed_data['question'])
                    db.session.add(poll)
                    for i in seed_data['options']:
                        option = Option(i, poll, 0)
                        db.session.add(option)
                    db.session.commit()
            except Exception as e:
                print("Cannot load seed data from file:", e)
                poll = Poll("", "")
    
    app.run(host='0.0.0.0', port=8000, debug=False)