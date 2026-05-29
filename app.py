from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
import random
import string

app = Flask(__name__)

def generate_secret_key():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=26))

app.config['SECRET_KEY'] = generate_secret_key()

socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}

def generate_room_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Room Chat</title>

<script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>

<style>

*{
    margin:0;
    padding:0;
    box-sizing:border-box;
    font-family:Arial,sans-serif;
}

body{
    background:#0f172a;
    color:white;
    height:100vh;
    display:flex;
    justify-content:center;
    align-items:center;
}

.container{
    width:100%;
    max-width:900px;
    height:90vh;
    background:#111827;
    border-radius:20px;
    overflow:hidden;
    display:flex;
    flex-direction:column;
}

.header{
    padding:20px;
    text-align:center;
    font-size:28px;
    font-weight:bold;
    color:#38bdf8;
    background:#1e293b;
}

.home{
    padding:30px;
    display:flex;
    flex-direction:column;
    gap:20px;
}

.room-card{
    background:#1e293b;
    padding:15px;
    margin: 20px;
    border-radius:12px;
    display:flex;
    justify-content:space-between;
}

.chat{
    display:none;
    flex-direction:column;
    height:100%;
}

.room-title{
    padding:15px;
    background:#1e293b;
    display:flex;
    align-items:center;
    justify-content:space-between;
}

.chat-box{
    flex:1;
    overflow-y:auto;
    padding:20px;
    display:flex;
    flex-direction:column;
    gap:12px;
}

.message-wrapper{
    display:flex;
}

.message{
    padding:12px;
    border-radius:12px;
    max-width:70%;
}

.input-area{
    display:flex;
    gap:10px;
    padding:20px;
    background:#1e293b;
}

#message{
    flex:1;
    min-height:60px;
    padding:12px;
    border-radius:10px;
    border:none;
    background:#0f172a;
    color:white;
}

input{
    padding:12px;
    border-radius:10px;
    border:none;
    background:#0f172a;
    color:white;
}

button{
    padding:12px 16px;
    border-radius:10px;
    border:none;
    background:#38bdf8;
    font-weight:bold;
    cursor:pointer;
}

#error-msg {
    color: #ff0000;
}

</style>

</head>
<body>

<div class="container">

<div class="header">TEMP CHAT ROOM</div>

<!-- HOME -->
<div class="home" id="home">

    <input id="username" placeholder="Username">
    <h4 id="error-msg"></h4>
    <button onclick="createRoom()">Create Room</button>

    <h3>Rooms</h3>
    <div id="room-list"></div>

</div>

<!-- CHAT -->
<div class="chat" id="chat">

    <div class="room-title">
        <button onclick="goBack()">← Back</button>
        <div id="room-title"></div>
    </div>

    <div class="chat-box" id="chat-box"></div>

    <div class="input-area">
        <input id="message" placeholder="Type message...">
        <button onclick="sendMessage()">Send</button>
    </div>

</div>

</div>

<script>

const socket = io();

let username = null;
let currentRoom = null;

function goBack(){
    if(currentRoom){
        socket.emit("leave_room_event", { room: currentRoom });
    }

    document.getElementById('chat').style.display = 'none';
    document.getElementById('home').style.display = 'flex';

    currentRoom = null;
}

function validate(){
    const name = document.getElementById('username').value.trim();
    if(!name){
        document.getElementById("error-msg").innerText = "You must enter a name to join in a room";
        return false
    }

    if(!username){
        username = name;
        document.getElementById('username').disabled = true;
    }

    return true;
}

function createRoom(){
    if(!validate()) return;
    document.getElementById("error-msg").innerText = "";
    socket.emit('create_room');
}

function joinRoom(room){
    if(!validate()) return;
    document.getElementById("error-msg").innerText = "";
    socket.emit('join_room_event', { room });
}

function sendMessage(){

    if(!currentRoom) return;

    const msg = document.getElementById('message').value;
    if(!msg) return;

    socket.emit('send_message', {
        room: currentRoom,
        username,
        message: msg
    });

    document.getElementById('message').value = '';
}

socket.on('room_list', rooms => {

    const list = document.getElementById('room-list');
    list.innerHTML = '';

    rooms.forEach(r => {
        list.innerHTML += `
        <div class="room-card">
            <div>${r}</div>
            <button onclick="joinRoom('${r}')">Join</button>
        </div>`;
    });

});

socket.on('room_created', data => {
    socket.emit('join_room_event', { room: data.room });
});

socket.on('room_joined', data => {

    currentRoom = data.room;

    document.getElementById('home').style.display = 'none';
    document.getElementById('chat').style.display = 'flex';

    document.getElementById('room-title').innerText = data.room;

    const box = document.getElementById('chat-box');
    box.innerHTML = '';

    data.messages.forEach(addMessage);
});

socket.on('new_message', addMessage);

function addMessage(msg){

    const isMine = msg.username === username;

    const box = document.getElementById('chat-box');

    box.innerHTML += `
    <div style="text-align:${isMine ? 'right' : 'left'}">
        <b>${msg.username}</b>
    </div>

    <div class="message-wrapper"
        style="justify-content:${isMine ? 'flex-end' : 'flex-start'}">

        <div class="message"
            style="
                background:${isMine ? '#38bdf8' : '#1e293b'};
                color:${isMine ? 'black' : 'white'};
            ">
            <div>${msg.message}</div>

            <div style="font-size:12px; opacity:0.6;">
                ${msg.time}
            </div>
        </div>

    </div>`;

    box.scrollTop = box.scrollHeight;
}

</script>

</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML_PAGE)


# ---------------- SOCKET EVENTS ----------------

@socketio.on("connect")
def connect():
    emit("room_list", list(rooms.keys()))


@socketio.on("create_room")
def create_room():
    room = generate_room_code()
    rooms[room] = []

    socketio.emit("room_list", list(rooms.keys()))
    emit("room_created", {"room": room})


@socketio.on("join_room_event")
def join(data):
    room = data["room"]

    join_room(room)

    emit("room_joined", {
        "room": room,
        "messages": rooms.get(room, [])
    })


@socketio.on("leave_room_event")
def leave(data):
    room = data["room"]
    leave_room(room)


@socketio.on("send_message")
def send(data):

    room = data.get("room")

    # ✅ HARD GUARANTEE: only send to that room
    if room not in rooms:
        return

    msg = {
        "username": data["username"],
        "message": data["message"],
        "time": datetime.now().strftime("%H:%M:%S")
    }

    rooms[room].append(msg)

    # 🔥 ONLY THIS ROOM RECEIVES IT
    socketio.emit("new_message", msg, room=room)


if __name__ == "__main__":
    socketio.run(app, debug=True)
