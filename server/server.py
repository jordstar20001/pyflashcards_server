# Server program. Created by Jordan Zdimirovic.

# Currently, users credentials will be stored in a JSON file.

# TODO Make it so users can't impersonate other users just because they have a token. HINT Edit the token_auth() function.

from pathlib import Path

from OpenSSL import SSL

import time

import json

import codecs

from flask_cors import CORS, cross_origin

import os

# RUNTIME VARS, REPLACE WITH JSON CONFIG FILE

serverName = "Jordan's Test Server."

listenIP = "0.0.0.0"

listenPort = 8080

userCredsFile = "data/credentials.json"

context = ('jz-software.pw.crt', 'jz-software.pw.key')

# END RUNTIME VARS

# OTHER VARS

runtime_users = {}

runtime_tokens = {}

accessible_users = []

runtime_chat_rooms = {}

# END OTHER VARS

# context = SSL.Context(SSL.SSLv23_METHOD)
# context.use_privatekey_file('privkey.pem')
# context.use_certificate_file('cert.pem')



from flask import Flask, request, make_response, jsonify

server = Flask(__name__)

CORS(server)

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

    file.close()

    os.makedirs("data/" + uName)

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

            token = new_login(uName)
            return make_response(jsonify({
                "token":token
            })), 202

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

# ---------------------- /2/ (server ops) ------------------------

@server.route("/2/flashcard", methods=["GET"])
def get_flash_card():
    if not token_auth(request):
        return make_response(), 403

    token = request.headers["Token"]
    user = runtime_tokens[token]['username']

    


@server.route("/2/flashcard", methods=["POST"])

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

    else:
        return False

    if len(runtime_chat_rooms[chatroom_owner]['message_bank']) >= 80:
        del runtime_chat_rooms[chatroom_owner]['message_bank'][0]

    return True



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
    if already_logged_in(user):
        del runtime_tokens[runtime_users[user]['token']]
        del runtime_users[user]
        del accessible_users[accessible_users.index(user)]


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




server.run(listenIP, listenPort, ssl_context=context)
