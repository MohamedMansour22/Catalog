#!/usr/bin/env python
from flask import Flask, render_template, request, redirect
from flask import url_for, jsonify, make_response, flash
from flask import session as login_session
from functools import wraps
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Game, User
import json
import random
import string
import requests
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2


app = Flask(__name__)
CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Menu Application"

engine = create_engine('sqlite:///catalog.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


# user login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in login_session:
            return f(*args, **kwargs)
        else:
            flash('Please login !!')
            return redirect('/login')
    return decorated_function


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps
                                 ('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'
    user_id = getUserID(data["email"])

    print ('User email is: ') + str(login_session['email'])
    user_id = getUserID(login_session['email'])
    if user_id:
        print ('Existing user #') + str(user_id) + (' matches this email.')
    else:
        user_id = createUser(login_session)
        print ('New user id #') + str(user_id) + (' created.')
        if user_id is None:
            print ('A new user could not be created.')
    login_session['user_id'] = user_id
    print ('Login session is tied to: id #') + str(login_session['user_id'])
    # See if a user exists, if it doesn't make a new one

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ''' " style = "width: 300px; height: 300px;border-radius:
                    150px;-webkit-border-radius:
                    150px;-moz-border-radius: 150px;"> '''
    flash("you are now logged in as %s" % login_session['username'])
    print ("done!")
    return output

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/categories/<int:category_id>/JSON')
def GameCategory(category_id):
    items = session.query(Game).filter_by(category_id=category_id).all()
    category = session.query(Category).filter_by(id=category_id).one()
    return jsonify(Game=[i.serialize for i in items])


@app.route('/')
@app.route('/catalog/')
def Display_categ():
    signed = 'username' not in login_session
    games = session.query(Game).order_by(Game.id.desc())
    categories = session.query(Category).all()
    return render_template('Home.html', categories=categories,
                           game=games, signed=signed)


@app.route('/categories/<int:category_id>/<int:game_id>/JSON')
def GameJSON(category_id, game_id):
    game = session.query(Game).filter_by(id=game_id).one()
    return jsonify(Game=game.serialize)


@app.route('/<int:category_id>')
@app.route('/catalog/<int:category_id>')
def categories(category_id):
    games = session.query(Game).filter_by(category_id=category_id)
    category = session.query(Category).filter_by(id=category_id).first()
    return render_template('category.html', category=category,
                           category_id=category_id,
                           game=games)


@app.route('/catalog/<int:category_id>/<int:game_id>')
def Display(category_id, game_id):
    Display = session.query(Game).filter_by(id=game_id).one()
    return render_template('the_game.html', category_id=category_id,
                           game_id=game_id, item=Display)


@app.route('/catalog/<int:category_id>/new', methods=['GET', 'POST'])
def Add(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newGame = Game(name=request.form.get('name', False),
                       description=request.form.get('description', False),
                       category_id=request.form.get('categories_id', False))
        session.add(newGame)
        session.commit()
        return redirect(url_for('categories',
                                category_id=category_id))
    else:
        return render_template('Add.html',
                               category_id=category_id)


# update
@app.route('/catalog/<int:category_id>/<int:game_id>/edit',
           methods=['GET', 'POST'])
def edit(category_id, game_id):

    edit = session.query(Game).filter_by(id=game_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if edit.user_id != login_session['user_id']:
        return "<script>{alert('Unauthorized');}</script>"
    if request.method == 'POST':
        if request.form['name']:
            edit.name = request.form['name']
        if request.form['description']:
            edit.description = request.form['description']
        session.add(edit)
        session.commit()
        return redirect(url_for('categories', category_id=category_id))
    else:
        return render_template('Edit.html', category_id=category_id,
                               game_id=game_id,
                               item=edit)


@app.route('/catalog/<int:category_id>/<int:game_id>/delete',
           methods=['GET', 'POST'])
def delete(category_id, game_id):

    delete = session.query(Game).filter_by(id=game_id).one()
    # if delete.user_id != login_session['user_id']:
    #     return redirect('/login')
    # Authorization check
    if 'username' not in login_session:
        return redirect('/login')
    # return render_template('Delete.html', item=delete)
    if request.method == 'POST':
        session.delete(delete)
        session.commit()
        return redirect(url_for('categories', category_id=category_id))
    else:
        return render_template('Delete.html', item=delete)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
