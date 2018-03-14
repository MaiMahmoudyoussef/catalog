from flask import Flask, render_template
from flask import request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from collections import Counter
from functools import wraps
from userDAO import createUser, getUserInfo, getUserID


app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

# create session and connect to db
engine = create_engine('sqlite:///catalogitems.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# making an API endpoint (GET REQUEST)


@app.route('/catalog.JSON')
def catalogJSON():
    categories = session.query(Category).all()
    # return jsonify(categories = [i.serialize for i in categories])

    for category in categories:
        items = session.query(Item).filter_by(category_id=category.id).all()
        return jsonify(categories=[i.serialize for i in categories],
                       Items=[i.category.serialize for i in items])


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    # return "the current session state is %s" %login_session ['state']
    return render_template('login.html', STATE=state)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in login_session:
            return redirect(url_for('showLogin', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        # exchange an authorization code for  credentials object
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps(
            'failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # check that the access token is valid
    access_token = credentials.access_token
    # to verify that it is a valid token for you from google
    url = (
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
        % access_token)
    # create json get request containing the url
    # and access token and store the result
    # in variable called result
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # if the result contains any error,
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # verify that the access token is used for the intended user
    # gplus ---> google plus
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps(
            'Tokens user ID doesnot match given user ID.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # verify that the access token is valid for this app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps(
            'Tokens user ID doesnot match app ID.'), 401)
        print "Tokens user ID doesnot match app ID."
        response.headers['Content-Type'] = 'application/json'
        return response

    # check if the user is already logged in
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'

    # store the access token in the session for later user
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = json.loads(answer.text)

    login_session['username'] = data["name"]
    login_session['picture'] = data["picture"]
    login_session['email'] = data["email"]

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    username = login_session['username']
    picture = login_session['picture']

    print "done!"
    return redirect(url_for('catalog'))

# disconnecting


@app.route('/gdisconnect')
def gdisconnect():
    # only disconnected a connected user
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(json.dumps(
            'current user is not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # execute HTTP GET request to revoke current token
    access_token = credentials.access_token
    url = ('https://accounts.google.com/o/oauth2/revoke?token=%s'
           % access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    # if result = 200 then i have successfully disconnected google account
    if result['status'] == '200':
        # reset the user session
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('successfully disconnected'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('catalog'))

    else:
        # for whatever reason, the given token as invalid
        response = make_response(json.dumps(
            'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/')
@app.route('/catalog')
def catalog():
    categories = session.query(Category).all()
    items = session.query(Item)
    # to know if this user is loged in or not
    if 'username' not in login_session:
        return render_template(
            'index.html', categories=categories, items=items)
    else:
        return render_template(
            'index3.html',
            categories=categories,
            items=items,
            username=login_session['username'],
            picture=login_session['picture'])


@app.route('/catalog/<string:category_name>/items')
def categoryItems(category_name):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name=category_name).first()
    items = session.query(Item).filter_by(category_id=category.id)
    num = items.count()
    if 'username' not in login_session:
        return render_template(
            'index2.html',
            categories=categories,
            items=items,
            category=category,
            num=num)
    else:
        return render_template(
            'index2_2.html',
            categories=categories,
            items=items,
            category=category,
            num=num,
            username=login_session['username'],
            picture=login_session['picture'])


@app.route('/catalog/<string:category_name>/items/add',
           methods=['GET', 'POST'])
@login_required
def addItem(category_name):
    category = session.query(Category).filter_by(name=category_name).first()
    if request.method == 'POST':
        if request.form['name']:
            newItem = Item(
                name=request.form['name'],
                description=request.form['description'],
                category_id=category.id,
                user_id=login_session['user_id'])
            session.add(newItem)
            session.commit()
            flash("new menu item was created")
            return redirect(url_for(
                'categoryItems', category_name=category_name))
    else:
        return render_template(
            'additem.html',
            category_name=category_name,
            picture=login_session['picture'],
            username=login_session['username'])


@app.route('/catalog/<string:category_name>/<string:item_name>')
def categoryItemDescription(category_name, item_name):
    category = session.query(Category).filter_by(name=category_name).first()
    item = session.query(Item).filter_by(
        name=item_name, category_id=category.id).first()

    # to know if this user is loged in or not
    if 'username' not in login_session:
        return render_template('description.html', item=item)
    else:
        return render_template(
            'descriptionloggedin.html',
            item_name=item.name,
            description=item.description,
            picture=login_session['picture'],
            username=login_session['username'])


@app.route('/catalog/<string:item_name>/edit', methods=['GET', 'POST'])
@login_required
def editItem(item_name):
    categories = session.query(Category).all()
    editItem = session.query(Item).filter_by(name=item_name).first()
    # to make sure that the logged in person is the creator of that item
    if editItem.user_id == login_session['user_id']:
        if request.method == 'POST':
            if request.form['name']:
                editItem.name = request.form['name']
                editItem.description = request.form['description']
                editItem.category.name = request.form['category']

                session.add(editItem)
                session.commit()
                flash("new menu item was edited")
                return redirect(url_for(
                    'categoryItems',
                    category_name=editItem.category.name))
        else:
            return render_template(
                    'edititem.html',
                    description=editItem.description,
                    item_name=editItem.name,
                    category=editItem.category,
                    categories=categories,
                    picture=login_session['picture'],
                    username=login_session['username'])
    else:
        flash('You canot edit others item, so add your own item to be able to edit it')
        return redirect(url_for(
            'addItem', category_name=editItem.category.name))


@app.route('/catalog/<string:item_name>/delete', methods=['GET', 'POST'])
@login_required
def deleteItem(item_name):
    deletedItem = session.query(Item).filter_by(name=item_name).first()
    # to make sure that the logged in person is the creator of that item
    if deletedItem.user_id == login_session['user_id']:
        if request.method == 'POST':
            session.delete(deletedItem)
            session.commit()
            flash("new menu item was deleted")
            return redirect(url_for('catalog'))
        else:
            return render_template(
                    'deleteitem.html',
                    item_name=deletedItem.name,
                    item=deletedItem)
    else:
        flash('You canot delete others item, so add your own item to be able to delete it')
        return redirect(url_for(
            'addItem', category_name=deletedItem.category.name))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    # to restart the server automatic every time i change the code
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
