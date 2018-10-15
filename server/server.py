# Server program. Created by Jordan Zdimirovic.

# Currently, users credentials will be stored in a JSON file.

# TODO Make it so users can't impersonate other users just because they have a token. HINT Edit the token_auth() function.

from pathlib import Path

import time

import json

import codecs

import os

# RUNTIME VARS, REPLACE WITH ENV VARS

serverName = "Jordan's Test Server."

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

@server.route("/0", methods=["GET"])
def send_heartbeat():
    return make_response(jsonify({
        "name":serverName
    })), 200

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
        return make_response(), 403

    else:
        return make_response(), 200

@server.route("/1/login", methods=["DELETE"])
def log_out_user():
    if not token_auth(request):
        return make_response(), 403

    token = request.headers["Token"]
    user = runtime_tokens[token]['username']
    del runtime_tokens[token]
    del runtime_users[user]
    accessible_users.remove(user)
    return make_response(), 200


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

    title = reqJson['title']

    description = reqJson['description']

    roomPassword = reqJson['room_password']

    max_users = reqJson['max_users']

    # VALIDATION

    for val in reqJson:
        if len(str(reqJson[val])) == 0 and val != 'room_password':
            return create_status_response("Invalid input.", 500);



    if uName in runtime_chat_rooms:
        return create_status_response("You already have a chatroom.", 500)

    else:

        runtime_chat_rooms[uName] = {
            "users":[
                uName
            ],

            "title":title,

            "description":description,

            "password":roomPassword,

            "max_users":max_users,

            "message_bank":[]

        }

        return make_response(), 201

@server.route("/2/chatrooms/getall", methods=["GET"])
def get_all_chat_rooms():
    if not token_auth(request):
        return make_response(), 403

    listResp = []
    for owner in runtime_chat_rooms:
        listResp.append(owner)

    return make_response(jsonify({
        "rooms":listResp,
    })), 200


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
        currentRoom = runtime_chat_rooms[owner]
        if currentRoom['password'] != "":
            passwordEnabled = True
        resp = make_response(jsonify({
            "users": currentRoom['users'],
            "title": currentRoom['title'],
            "description": currentRoom['description'],
            "max_users": currentRoom['max_users'],
            "password_enabled": passwordEnabled,


        }))

        return resp, 200

    else:
        return create_status_response("Room not found. The room may have expired, or the owner may have changed.", 500)

@server.route("/2/chatrooms/join", methods=["POST"]) # TODO refactor this so it is GET and uses URL to pass id
def join_chat_room():

    if not token_auth(request):
        return make_response(), 403

    if not request.is_json:
        return make_response(), 400

    reqJson = request.get_json()

    owner = reqJson['owner']

    user = reqJson['username']

    if not token_auth_with_user(request, user):
        return create_status_response("User not authenticated.", 403)

    if owner not in runtime_chat_rooms:
        return create_status_response("Room not found. The room may have expired, or the owner may have changed.", 400)


    room_password_attempt = ""

    if 'password' in reqJson:
        room_password_attempt = reqJson['password']

    if room_password_attempt == runtime_chat_rooms[owner]['password']:
        token = request.headers["Token"]
        runtime_chat_rooms[owner]['users'].append(runtime_tokens[token]['username'])
        return make_response(), 200

    else:
        return create_status_response("Incorrect password for room.", 403)





@server.route("/2/chatrooms/message", methods=["POST", "GET"])
def message_handle():
    # New message
    if request.method == "POST":
        if not request.is_json:
            return make_response(), 400

        if not token_auth(request):
            return make_response(), 403

        # Get data

        reqJson = request.get_json()

        username = reqJson['username']

        owner = reqJson['owner']

        message = reqJson['message']

        if owner not in runtime_chat_rooms:


            return create_status_response("Room not found.", 400)

        if username in runtime_chat_rooms[owner]['users']:
            if token_auth_with_user(request, username):
                if(new_message_in_chatroom(username, owner, message)):
                    return make_response(), 201

                else:
                    return create_status_response("Message was not sent.", 500)

            else:
                return make_response(), 403

        else:
            return make_response(), 403









        return "NotImplementedException"

    # Read messages
    elif request.method == "GET":
        if not token_auth(request):
            return make_response(), 403

        else:
            token = request.headers["Token"]
            owner = request.headers["Owner"]
            user = runtime_tokens[token]['username']
            if user in runtime_chat_rooms[owner]['users']:
                messages = runtime_chat_rooms[owner]['message_bank']
                return make_response(jsonify(messages))






# END routing

def token_auth(req):
    token = req.headers["Token"]
    if token in runtime_tokens:
        return True

    else:
        return False

def new_message_in_chatroom(username, chatroom_owner, message):
    if username in runtime_chat_rooms[chatroom_owner]['users']:
        # Add message to buffer

        runtime_chat_rooms[chatroom_owner]['message_bank'].append({
            "sender": username,
            "message": message
        })

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
