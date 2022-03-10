import json

from flask import Flask, abort, jsonify, request
from flask_cors import CORS

from .auth.auth import AuthError, requires_auth
from .database.models import Drink, db_drop_and_create_all, setup_db

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO: uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
# db_drop_and_create_all()

# ROUTES


@app.route('/drinks')
def get_drinks():
    '''
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
    '''
    return jsonify({
        'success': True,
        'drinks': [drink.short() for drink in Drink.query.all()]
    }), 200


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    '''
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
    '''
    return jsonify({
        'success': True,
        'drinks': [drink.long() for drink in Drink.query.all()]
    }), 200


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_drink(payload):
    '''
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
    '''

    try:
        drink_data = request.json
        drink = Drink(
            title=drink_data['title'],
            recipe=json.dumps(drink_data['recipe'])
        )
        drink.insert()
    except:
        abort(422)

    return jsonify({
        'success': True,
        'drinks': [drink.long() for drink in Drink.query.all()]
    }), 200


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drink(payload, drink_id):
    '''
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
    '''

    try:
        drink = Drink.query.get(drink_id)
        if not drink:
            abort(404)

        drink_data = request.json
        drink.title = drink_data.get('title', drink.title)
        if 'recipe' in drink_data:
            drink.recipe = json.dumps(drink_data['recipe'])
        drink.update()
    except Exception as err:
        abort(err.code) if err.code else abort(422)

    return jsonify({
        'success': True,
        'drinks': [drink.long() for drink in Drink.query.all()]
    }), 200


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, drink_id):
    '''
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
    '''

    try:
        drink = Drink.query.get(drink_id)
        if not drink:
            abort(404)
        drink.delete()
    except Exception as err:
        abort(err.code) if err.code else abort(422)

    return jsonify({
        'success': True,
        'drinks': [drink.long() for drink in Drink.query.all()]
    }), 200


# Error Handling
@app.errorhandler(404)
def not_found(error):
    '''
    Error handling for resource not found
    '''
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


@app.errorhandler(422)
def unprocessable(error):
    '''
    Error handling for unprocessable entity
    '''
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(AuthError)
def auth_error(error):

    return jsonify({
        'success': False,
        'error': error.status_code,
        'message': error.error['code']
    }), error.status_code
