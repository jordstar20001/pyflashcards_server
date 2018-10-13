# Server program. Created by Jordan Zdimirovic.

# Currently, users credentials will be stored in a JSON file.

# TODO Make it so users can't impersonate other users just because they have a token. HINT Edit the token_auth() function.

from pathlib import Path

import time

import json

import codecs

import os

# RUNTIME VARS, REPLACE WITH ENV VARS

listenIP = "0.0.0.0"

listenPort = 8080

userCredsFile = Path("data/") / "credentials.json"

# END RUNTIME VARS

# OTHER VARS

runtime_users = {}

runtime_tokens = {}

accessible_users = []

runtime_chat_rooms = {}

# END OTHER VARS

from flask import Flask, request, make_response, jsonify

server = Flask(__name__)

# START routing

@server.route("/1/signup", methods=["POST"]) # Sign up a user.
def sign_up_user():
    if request.is_json == False:
        return make_response(), 400

    userJson = request.get_json()

    uName = userJson['username']
    pWord = userJson['password']

    #try:
    file = open(userCredsFile, 'r')
    fileRaw = file.read()

    creds = {}
    if fileRaw != "":
        creds = json.loads(fileRaw)

    if uName in creds:
        return create_status_response("User already exists.")

    else:
        creds[uName] = pWord

    file.close()

    file = open(userCredsFile, 'w')

    file.write(json.dumps(creds))

    file.close();

    return make_response(), 201

    #except e:
    #    return create_status_response("Something happened.")

@server.route("/1/login", methods=["POST"]) # login
def login_user():
    if not request.is_json:
        return make_response(), 400

    userJson = request.get_json()

    uName = userJson['username']
    pWord = userJson['password']

    file = open(userCredsFile, 'r')
    fileRaw = file.read()

    creds = {}
    if fileRaw != "":
        creds = json.loads(fileRaw)

    if uName in creds:
        if creds[uName] == pWord:
            if not already_logged_in(uName):
                token = new_login(uName)
                return make_response(jsonify({
                    "token":token
                })), 202

            else:
                return create_status_response("You are already logged in.")

        else:
            return create_status_response("Incorrect credentials.")

    else:
        return create_status_response("Incorrect credentials.")

@server.route("/1/login", methods=["GET"])
def check_if_user_logged_in():
    if not token_auth(request):
        return make_response(), 200

    else:
        return make_response(), 403

# ----------------------------------------------------- /////2\\\\\ -------------------------------

@server.route("/2/users", methods=["GET"])
def get_online_users():
    if not token_auth(request):
        return make_response(), 403

    userList = accessible_users
    resp = {
        "users": userList
    }

    return make_response(jsonify(resp)), 200



@server.route("/2/chatrooms/create", methods=["POST"])
def create_chat_room():
    if not token_auth(request):
        return make_response(), 403

    if not request.is_json:
        return make_response(), 400

    reqJson = request.get_json()

    uName = reqJson['username']

    roomPassword = reqJson['room_password']

    max_users = reqJson['max_users']

    if uName in runtime_chat_rooms:
        return create_status_response("You already have a chatroom.", 500)

    else:
        runtime_chat_rooms[uName] = {
            "users":[
                uName
            ],

            "password":roomPassword,

            "max_users":max_users

        }

        return make_response(), 201

@server.route("/2/chatrooms/get", methods=["POST"]) # TODO refactor this so it is GET and uses URL to pass id
def get_chat_room_info():
    if not token_auth(request):
        return make_response(), 403

    if not request.is_json:
        return make_response(), 400

    reqJson = request.get_json()

    owner = reqJson['owner']

    if owner in runtime_chat_rooms:
        passwordEnabled = False
        if runtime_chat_rooms[owner]['password'] != "":
            passwordEnabled = True
        resp = make_response(jsonify({
            'users': runtime_chat_rooms[owner]['users'],
            'password_enabled': passwordEnabled
        }))

        return resp, 200

    else:
        return create_status_response("Room not found. The room may have expired, or the owner may have changed.", 500)

@server.route("/2/chatrooms/join", methods=["POST"]) # TODO refactor this so it is GET and uses URL to pass id
def join_chat_room():


    if not request.is_json:
        return make_response(), 400

    reqJson = request.get_json()

    owner = reqJson['owner']

    user = reqJson['username']

    if not token_auth_with_user(request, user):
        return make_response(), 403

    if owner not in runtime_chat_rooms:
        return create_status_response("Room not found. The room may have expired, or the owner may have changed.", 500)


    room_password_attempt = ""

    if 'password' in reqJson:
        room_password_attempt = reqJson['password']

    if room_password_attempt == runtime_chat_rooms[owner]['password']:
        token = req.headers["Token"]
        runtime_chat_rooms[owner]['users'].append(runtime_tokens[token]['username'])
        return make_response(), 200

    else:
        return create_status_response("Incorrect password for room.", 403)












# END routing

def token_auth(req):
    token = req.headers["Token"]
    if token in runtime_tokens:
        return True

    else:
        return False

def token_auth_with_user(req, user):
    token = req.headers["Token"]
    if token in runtime_tokens:
        if runtime_tokens[token]['username'] == user:
            return True

    else:
        return False

    return False

def create_status_response(message, status=500):
    temp = {}
    temp["msg"] = message

    response = make_response(jsonify(temp), status)

    response.headers["Content-Type"] = "application/json"

    return response

def already_logged_in(user):
    if user in runtime_users:
        return True

    else:
        return False

def new_login(user):
    token = str(codecs.encode(os.urandom(16), 'hex').decode())
    runtime_users[user] = {
        "token": token,
        "timestamp": "time.now()",
        "chatroom": None
    }

    accessible_users.append(user)

    runtime_tokens[token] = {
        "username": user,
        "timestamp": "time.now()"
    }

    return token




server.run(listenIP, listenPort)
