import getmac
from flask import Flask, jsonify, request, make_response
import jwt
from functools import wraps
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from flask_pymongo import PyMongo


user_app = Flask(__name__)
user_app.config['MONGO_DBNAME'] = 'users_db'
user_app.config['MONGO_URI'] = 'mongodb://useragent:osilayer8@localhost:49153/users_db'
user_app.config['SECRET_KEY'] = 'verysecretkey'

mongo = PyMongo(user_app)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            data = jwt.decode(token, user_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = mongo.db.users.find_one({'_id': uuid.UUID(data['_id'])})
        except():
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


@user_app.route('/user', methods=['GET'])
@token_required
def get_all_users(current_user):
    if not current_user['admin']:
        return jsonify({'message': 'cannot perform that function'})

    users = mongo.db.users.find()
    output = []
    for user in users:
        output.append(user)

    return jsonify({'Users': output})


@user_app.route('/user/<user_id>', methods=['GET'])
@token_required
def get_one_user(current_user, user_id):
    if not current_user['admin']:
        return jsonify({'message': 'cannot perform that function'})

    user = mongo.db.users.find_one({'_id': uuid.UUID(user_id)})

    return jsonify({'User': user})


@user_app.route('/user/<user_id>', methods=['PUT'])
def promote_user(user_id):
    mongo.db.users.update_one({'_id': uuid.UUID(user_id)}, {'$set': {'admin': True}})

    return jsonify({'message': 'User promoted'})


@user_app.route('/user/<user_id>', methods=['DELETE'])
@token_required
def delete_user(current_user, user_id):
    if not current_user['admin']:
        return jsonify({'message': 'cannot perform that function'})

    mongo.db.users.delete_one({'_id': uuid.UUID(user_id)})

    return jsonify({'message': 'user deleted'})


@user_app.route('/registration')
def register():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Registration Required"'})

    data = {
        'name': auth.username,
        'password': auth.password
    }

    hashed_pass = generate_password_hash(data['password'], method='sha256')
    new_user = {
        '_id': uuid.uuid4(),
        'mac': getmac.getmac.get_mac_address(),
        'name': data['name'],
        'password': hashed_pass,
        'admin': False
    }
    mongo.db.users.insert_one(new_user)

    user = mongo.db.users.find_one({'name': auth.username})

    if user is None:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Registration Required"'})

    curr_id = uuid.UUID(user['_id'].hex)
    api_tok_usr = mongo.db.api_tokens.find_one({'user_id': curr_id})

    if check_password_hash(user['password'], auth.password):
        if api_tok_usr is None:
            token = jwt.encode({'_id': user['_id'].hex}, user_app.config['SECRET_KEY'])
            # adding the token with the corresponding user id to the api_tokens collection
            api_token = {
                '_id': uuid.uuid4(),
                'user_id': user['_id'],
                'token': token
            }
            mongo.db.api_tokens.insert_one(api_token)

            return jsonify({'token': token, 'message': 'You can close this page after you copied the token'})

        return jsonify({'message': 'You already have an account, please sign in instead'})


if __name__ == "__main__":
    user_app.run(debug=False, port=5001)
