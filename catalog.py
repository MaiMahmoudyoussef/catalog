from flask import Flask , render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
from flask import session as login_session
import random, string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)


# create session and connect to db
engine = create_engine('sqlite:///catalogitems.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

@app.route('/')
@app.route('/catalog')
def catalog():
    return "homepage"


@app.route('/category/<string:category_name>/items')
def categoryItems(category_name):
    return "items"


@app.route('/category/<string:category_name>/<string:item_name>')
def categoryItemDescription(category_name, item_name):
    return "item description"


@app.route('/category/<string:item_name>/edit')
def editItem(item_name):
    return "edit item"


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    #to restart the server automatic every time i change the code
    app.debug = True
    app.run(host = '0.0.0.0', port = 8000)
