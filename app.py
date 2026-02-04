from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit, join_room
import random, string, os

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

rooms = {}  # room_code -> {players: [], board, turn}

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Tic Tac Toe Neon</title>
<script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
<style>
body{
    background:#0f0f1a;
    color:#0ff;
    font-family:Arial;
    text-align:center;
}
button,input,select{
    padding:10px;
    margin:5px;
    background:#111;
    color:#0ff;
    border:1px solid #0ff;
    border-radius:6px;
}
.grid{
    display:grid;
    grid-template-columns:repeat(3,100px);
    gap:10px;
    justify-content:center;
    margin-top:20px;
}
.cell{
    width:100px;
    height:100px;
    font-size:40px;
    cursor:pointer;
    background:#000;
    border:2px solid #0ff;
}
</style>
</head>
<body>

<h1>Neon Tic Tac Toe ✨</h1>

<div id="menu">
    <input id="name" placeholder="Your name">
    <br>
    <button onclick="createRoom()">Create Room</button>
    <br>
    <input id="roomcode" placeholder="Room code">
    <select id="role">
        <option value="player">Player</option>
        <option value="spectator">Spectator</option>
    </select>
    <button onclick="joinRoom()">Join Room</button>
</div>

<h2 id="status"></h2>

<div class="grid" id="board" style="display:none;">
    {% for i in range(9) %}
    <div class="cell" onclick="move({{i}})" id="c{{i}}"></div>
    {% endfor %}
</div>

<script>
const socket = io();
let room = "";
let role = "";

function createRoom(){
    let name = document.getElementById("name").value;
    socket.emit("create_room",{name});
}

function joinRoom(){
    room = document.getElementById("roomcode").value;
    role = document.getElementById("role").value;
    let name = document.getElementById("name").value;
    socket.emit("join_room",{room,name,role});
}

socket.on("room_created",data=>{
    room = data.room;
    document.getElementById("status").innerText =
        "Room created: "+room+" (waiting for opponent)";
});

socket.on("room_joined",data=>{
    document.getElementById("menu").style.display="none";
    document.getElementById("board").style.display="grid";
    document.getElementById("status").innerText=data.msg;
});

socket.on("update",data=>{
    data.board.forEach((v,i)=>{
        document.getElementById("c"+i).innerText = v;
    });
    document.getElementById("status").innerText = data.msg;
});

function move(i){
    socket.emit("move",{room,index:i});
}
</script>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

def gen_room():
    return ''.join(random.choices(string.ascii_uppercase+string.digits,k=6))

@socketio.on("create_room")
def create(data):
    room = gen_room()
    rooms[room] = {
        "players":[data["name"]],
        "board":[""]*9,
        "turn":"X"
    }
    join_room(room)
    emit("room_created",{"room":room})

@socketio.on("join_room")
def join(data):
    room = data["room"]
    if room not in rooms:
        emit("room_joined",{"msg":"Room not found ❌"})
        return

    join_room(room)

    if data["role"]=="player" and len(rooms[room]["players"])<2:
        rooms[room]["players"].append(data["name"])
        msg="Game started! Player X turn"
    else:
        msg="Spectator joined 👀"

    emit("room_joined",{"msg":msg},room=room)
    emit("update",{
        "board":rooms[room]["board"],
        "msg":msg
    },room=room)

@socketio.on("move")
def move(data):
    room=data["room"]
    i=data["index"]

    if room not in rooms: return
    board=rooms[room]["board"]

    if board[i]!="": return

    board[i]=rooms[room]["turn"]
    rooms[room]["turn"] = "O" if rooms[room]["turn"]=="X" else "X"

    emit("update",{
        "board":board,
        "msg":"Turn: "+rooms[room]["turn"]
    },room=room)

if __name__ == "__main__":
    port=int(os.environ.get("PORT",10000))
    socketio.run(app,host="0.0.0.0",port=port)
