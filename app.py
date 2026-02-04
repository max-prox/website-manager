from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit, join_room
import random, string, os

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

rooms = {}

def gen_room():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Neon Tic Tac Toe</title>
<script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
<style>
body{
    background:#0b0b16;
    color:#0ff;
    font-family:Arial;
}
.container{
    display:flex;
    justify-content:center;
    gap:30px;
    margin-top:20px;
}
.game{
    text-align:center;
}
.grid{
    display:grid;
    grid-template-columns:repeat(3,100px);
    gap:10px;
}
.cell{
    width:100px;
    height:100px;
    font-size:40px;
    cursor:pointer;
    background:#000;
    border:2px solid #0ff;
    color:#0ff;
}
.chat{
    width:250px;
    border:2px solid #0ff;
    padding:10px;
}
#messages{
    height:300px;
    overflow-y:auto;
    border:1px solid #0ff;
    margin-bottom:10px;
    padding:5px;
}
input,button{
    background:#000;
    color:#0ff;
    border:1px solid #0ff;
    padding:8px;
}
</style>
</head>
<body>

<h1 style="text-align:center;">Neon Tic Tac Toe ✨</h1>

<div id="menu" style="text-align:center;">
    <input id="name" placeholder="Your name"><br><br>
    <button onclick="createRoom()">Create Room</button><br><br>
    <input id="roomcode" placeholder="Room code">
    <button onclick="joinRoom()">Join Room</button>
</div>

<h3 id="status" style="text-align:center;"></h3>

<div class="container" id="gameArea" style="display:none;">
    <div class="game">
        <div class="grid">
            {% for i in range(9) %}
            <div class="cell" onclick="move({{i}})" id="c{{i}}"></div>
            {% endfor %}
        </div>
    </div>

    <div class="chat">
        <h3>Room Chat 💬</h3>
        <div id="messages"></div>
        <input id="chatInput" placeholder="message">
        <button onclick="sendChat()">Send</button>
    </div>
</div>

<script>
const socket = io();
let room = "";

function createRoom(){
    socket.emit("create_room",{
        name:document.getElementById("name").value
    });
}

function joinRoom(){
    room=document.getElementById("roomcode").value;
    socket.emit("join_room",{
        room,
        name:document.getElementById("name").value
    });
}

socket.on("room_created",data=>{
    room=data.room;
    document.getElementById("menu").style.display="none";
    document.getElementById("gameArea").style.display="flex";
    document.getElementById("status").innerText="Room: "+room+" (Waiting for opponent)";
});

socket.on("room_joined",data=>{
    document.getElementById("menu").style.display="none";
    document.getElementById("gameArea").style.display="flex";
    document.getElementById("status").innerText=data.msg;
});

socket.on("update_board",data=>{
    data.board.forEach((v,i)=>{
        document.getElementById("c"+i).innerText=v;
    });
    document.getElementById("status").innerText=data.msg;
});

function move(i){
    socket.emit("move",{room,index:i});
}

/* CHAT */
function sendChat(){
    let text=document.getElementById("chatInput").value;
    socket.emit("chat",{room,text});
    document.getElementById("chatInput").value="";
}

socket.on("chat",data=>{
    let div=document.createElement("div");
    div.innerText=data;
    document.getElementById("messages").appendChild(div);
});
</script>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

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
    room=data["room"]
    if room not in rooms:
        emit("room_joined",{"msg":"❌ Room not found"})
        return

    join_room(room)

    if len(rooms[room]["players"])<2:
        rooms[room]["players"].append(data["name"])
        msg="Game started! Player X turn"
    else:
        msg="Spectator joined 👀"

    emit("room_joined",{"msg":msg})
    emit("update_board",{
        "board":rooms[room]["board"],
        "msg":msg
    },room=room)

@socketio.on("move")
def move(data):
    room=data["room"]
    i=data["index"]
    board=rooms[room]["board"]

    if board[i]!="": return

    board[i]=rooms[room]["turn"]
    rooms[room]["turn"]="O" if rooms[room]["turn"]=="X" else "X"

    emit("update_board",{
        "board":board,
        "msg":"Turn: "+rooms[room]["turn"]
    },room=room)

@socketio.on("chat")
def chat(data):
    emit("chat",data["text"],room=data["room"])

if __name__=="__main__":
    port=int(os.environ.get("PORT",10000))
    socketio.run(app,host="0.0.0.0",port=port)
