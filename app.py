from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit, join_room
import os, random, string

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="eventlet"
)

rooms = {}   # room_code: [players]

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Tic Tac Toe</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{
  background:#0f0f1a;
  color:#0ff;
  font-family:Arial;
  text-align:center;
}
button{
  padding:12px 20px;
  font-size:18px;
  margin:10px;
  background:black;
  color:#0ff;
  border:2px solid #0ff;
  cursor:pointer;
}
#status{margin-top:20px;font-size:20px;}
</style>
</head>
<body>

<h2>Multiplayer Tic Tac Toe</h2>

<div id="menu">
  <button id="create">Create Room</button><br>
  <input id="roomInput" placeholder="Room code">
  <button id="join">Join Room</button>
</div>

<div id="status"></div>

<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
<script>
const socket = io({transports:["websocket"]});

document.getElementById("create").onclick = ()=>{
  socket.emit("create_room");
};

document.getElementById("join").onclick = ()=>{
  const code = document.getElementById("roomInput").value;
  socket.emit("join_room", code);
};

socket.on("room_created",(code)=>{
  document.getElementById("status").innerText =
    "Room created: "+code+" (waiting for opponent)";
});

socket.on("joined",(msg)=>{
  document.getElementById("status").innerText = msg;
});

socket.on("start",(msg)=>{
  document.getElementById("status").innerText = msg;
});
</script>

</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

def gen_room():
    return "".join(random.choices(string.ascii_uppercase+string.digits,k=5))

@socketio.on("create_room")
def create_room():
    code = gen_room()
    rooms[code] = []
    join_room(code)
    rooms[code].append(request.sid)
    emit("room_created", code)

@socketio.on("join_room")
def join(code):
    if code not in rooms:
        emit("joined","❌ Room not found")
        return
    join_room(code)
    rooms[code].append(request.sid)

    if len(rooms[code]) == 2:
        socketio.emit("start","Game starting in 3...", room=code)
    else:
        emit("joined","Waiting for opponent...")

if __name__=="__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT",5000)),
        allow_unsafe_werkzeug=True
    )
