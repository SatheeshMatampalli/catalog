import httplib2
import json
import random
import string
from flask import Flask, render_template
from flask import request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from projector_DB import Base, User_Data, Brand_Data, Model_Data
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Projectors Info"


# Connect to Database and create database session
engine = create_engine('sqlite:///projector_databse.db',
                       connect_args={'check_same_thread': False}, echo=True)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
# DB Session
session = DBSession()
# login page


@app.route('/login')
def DisplayLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

# GConnect


@app.route('/gconnect', methods=['POST'])
def gconnect():
    ''' Validate state token'''
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    code = request.data.decode('utf-8')

    try:
        # Upgrade the authorization code into a credentials objects
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # Error in the access token info and ABORTED
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Access token is valid for this Application
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response
    # Access tokens are stored
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'
            ), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    # Get user information.
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = Create_User(login_session)
    login_session['user_id'] = user_id
    output = ''
    output += '<h2>Welcome, '
    output += login_session['username']
    output += '!</h2>'
    output += '<img src=" '
    output += login_session['picture']
    output += ' " style = "width: 225px; height: 250px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print("done!")
    return output


def Create_User(login_session):
    newuser = User_Data(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newuser)
    session.commit()
    user = session.query(User_Data).filter_by(
                                            email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User_Data).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User_Data).filter_by(email=email).one()
        return user.id
    except:
        return None

# JSON END API's


@app.route('/brand/JSON')
def json_brand():
    session = DBSession()
    brand = session.query(Brand_Data)
    session.close()
    return jsonify(brand=[i.serialize for i in brand])


@app.route('/brands/<int:brand_id>/models/<int:model_id>/JSON')
def brandsModels(brand_id, model_id):
    session = DBSession()
    brand = session.query(Brand_Data).filter_by(id=brand_id).all()
    model = session.query(Model_Data).filter_by(id=model_id).all()
    session.close()
    return jsonify(brand=[i.serialize for i in brand],
                   model=[i.serialize for i in model])


@app.route('/brand/<int:brand_id>/JSON')
def jsonbrandModels(brand_id):
    session = DBSession()
    brand = session.query(Brand_Data).filter_by(id=brand_id).all()
    model = session.query(Model_Data).filter_by(brand_id=brand_id).all()
    session.close()
    return jsonify(brand=[i.serialize for i in brand],
                   model=[i.serialize for i in model])


# To See All Brands and Users Created
@app.route('/brand')
def Pj_Brand():
    try:
        session = DBSession()
        brands = session.query(Brand_Data).order_by(asc(Brand_Data.name)).all()
        if not brands:
            # print Message
            flash("No Brands to show.")
        session.close()
        return render_template(
            'showALLbrands.html',
            brands=brands,
            cur_user=login_session)
    except Exception as l:
        print(l)

# To Add New Brand


@app.route('/')
def Pj_Brands():
    session = DBSession()
    brands = session.query(Brand_Data)
    return render_template(
        'Pro_brands.html', brands=brands,
        cur_user=login_session)


@app.route('/brand/new', methods=['GET', 'POST'])
def Nw_Brand():
    if 'username' in login_session:
        if request.method == 'POST':
            newBrd = Brand_Data(
                name=request.form['name'],
                user_id=login_session['user_id'])
            session = DBSession()
            session.add(newBrd)
            session.commit()
            '''printing message'''
            flash(newBrd.name + "Shoe brand added Successfully.")
            session.close()
            return redirect('/')
        else:
            return render_template('new_brand.html', cur_user=login_session)
    else:
        # Printing message
        flash("Login sucessfully...... !")
        return redirect('/login')

# Edit Brand


@app.route('/brand/<int:brand_id>/edit', methods=['GET', 'POST'])
def Ed_Brand(brand_id):
    session = DBSession()
    editBrd = session.query(Brand_Data).filter_by(id=brand_id).one()
    if 'username' in login_session:
        if login_session['user_id'] == editBrd.user_id:
            before = editBrd.name
            if request.method == 'POST':
                editBrd.name = request.form['name']
                session.add(editBrd)
                session.commit()
                # Print message
                flash(
                    before + " brand name is Changed  " + editBrd.name)
                session.close()
                return redirect('/')
            else:
                return render_template(
                    'editbrand.html',
                    br=editBrd,
                    cur_user=login_session)
        else:
            # Print message
            flash("you are not authorized to change")
            return redirect('/')
    else:
        # flash message
        flash("Login sucessful.......... !")
        return redirect('/login')


# To Delete a selected Brand
@app.route('/brand/<int:brand_id>/delete', methods=['GET', 'POST'])
def Del_Brand(brand_id):
    session = DBSession()
    deleteBrd = session.query(Brand_Data).filter_by(id=brand_id).one()
    if 'username' in login_session:
        if login_session['user_id'] == deleteBrd.user_id:
            deleteMoDU = session.query(Model_Data).filter_by(
                                                           brand_id=brand_id
                                                           ).all()
            if request.method == 'POST':
                for i in deleteMoDU:
                    print("deleting ", i.id)
                    session.delete(i)
                    session.commit()
                session.delete(deleteBrd)
                session.commit()
                # Print message
                flash(deleteBrd.name + " Brand deleted successfully.....!")
                session.close()
                return redirect('/')
            else:
                return render_template(
                    'del_brand.html',
                    br=deleteBrd,
                    cur_user=login_session)
        else:
            # flash message
            flash("you are not authorized to delete")
            return redirect('/')
    else:
        # flash message....
        flash("Login sucessful.... !")
        return redirect('/login')


# To See All Models
@app.route('/brand/<int:brand_id>/model')
def Pj_Model(brand_id):
        session = DBSession()
        brand = session.query(Brand_Data).filter_by(id=brand_id).one()
        model = session.query(Model_Data).filter_by(brand_id=brand.id)
        return render_template(
            'pmusers.html', brand=brand,
            model=model, cur_user=login_session)

# Show models for users data


@app.route('/brand/<int:brand_id>/')
def Pj_Models(brand_id):
    try:
        session = DBSession()
        brand = session.query(Brand_Data).filter_by(id=brand_id).one()

        if not model:
            # print message
            flash("Dont have any Models to show.")
        session.close()
        return render_template(
            'pmusers.html',
            brand=brand,
            model=model,
            cur_user=login_session)
    except Exception as l:
        return ""


# Models data for New Models
@app.route('/brand/<int:brand_id>/model/new', methods=['GET', 'POST'])
def Nw_Model(brand_id):
    if 'username' in login_session:
        session = DBSession()
        brand = session.query(Brand_Data).filter_by(id=brand_id).one()
        if login_session['user_id'] == brand.user_id:
            if request.method == 'POST':
                brand = session.query(Brand_Data).filter_by(id=brand_id).one()
                newMo = Model_Data(
                    brand_id=brand.id,
                    user_id=login_session['user_id'],
                    modelno=request.form['modelno'],
                    colors=request.form['colors'],
                    cost=request.form['cost'],
                    description=request.form['des'])
                session.add(newMo)
                # To store data in Permanently
                session.commit()
                # flash message
                flash("  New Model added successfully to %s" % brand.name)
                session.close()
                return redirect(url_for('Pj_Model', brand_id=brand_id))
            else:
                return render_template(
                    'new_model.html',
                    brand=brand,
                    cur_user=login_session)
        else:
            # print message
            flash("you are not having any permissions")
            return redirect('/')
    else:
        # print message
        flash("Login sucessful.... !")
        return redirect('/login')


# To Edit the  Model


@app.route(
    '/brand/<int:brand_id>/model/<int:model_id>/edit',
    methods=['GET', 'POST'])
def Ed_Model(brand_id, model_id):
    if 'username' in login_session:
        session = DBSession()
        brand = session.query(Brand_Data).filter_by(id=brand_id).one()
        editMod = session.query(Model_Data).filter_by(id=model_id).one()
        if login_session['user_id'] == brand.user_id:
            if request.method == 'POST':
                editMod.modelno = request.form['modelno']
                editMod.colors = request.form['colors']
                editMod.brand_id = brand_id
                editMod.cost = request.form['cost']
                editMod.description = request.form['description']
                session.add(editMod)
                session.commit()
                # print message
                flash("you have done changes Successfully")
                session.close()
                return redirect(url_for('Pj_Model', brand_id=brand_id))
            else:
                return render_template(
                    'edit_model.html', brand_id=brand_id,
                    model_id=model_id, edit=editMod,
                    cur_user=login_session)
        else:
            # print message
            flash("you are not autorized to edit")
            return redirect('/')
    else:
        # print message
        flash("Login sucessful ...!")
        return redirect('/login')


# To Delete a Model


@app.route(
    '/brand/<int:brand_id>/model/<int:model_id>/delete',
    methods=['POST', 'GET'])
def Del_Model(brand_id, model_id):
    if 'username' in login_session:
        session = DBSession()
        deleteMod = session.query(Model_Data).filter_by(id=model_id).one()
        # print(deleteMod.name)
        if login_session['user_id'] == deleteMod.user_id:
            if request.method == 'POST':
                session.delete(deleteMod)
                session.commit()
                flash(" Model deleted Successfully....")
                return redirect(url_for('Pj_Model', brand_id=brand_id))

            else:
                return render_template(
                    'delete_model.html', brand_id=brand_id,
                    model=deleteMod, cur_user=login_session)
                session.close()
        else:
            # print message
            flash("you dont have permissions to delete")
            return redirect('/')
    else:
        # print message
        flash("Login sucessful...... !")
        return redirect('/login')


@app.route('/logout')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    print(access_token)
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
        del login_session['user_id']

        response = make_response(json.dumps('Disconnected....!'), 200)
        response.headers['Content-Type'] = 'application/json'
        response = redirect(url_for('Pj_Brands'))
        flash('LoggedOut Successfully')
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

# default constructor
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
