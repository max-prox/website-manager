from flask import Flask, render_template_string, request, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
import os, random, string, time

app = Flask(__name__)
app.secret_key = "supersecretkey"
socketio = SocketIO(app)

# All rooms data
rooms = {}  # room_id -> {players:[{name,symbol,sid}], board, turn, gameOver, countdown}

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Neon Tic Tac Toe ⚡</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500&display=swap" rel="stylesheet">
    <style>
        body { font-family:'Orbitron', sans-serif; background:#0f0f0f; color:#fff; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;}
        #container { text-align:center; background:#111; padding:20px; border-radius:20px; box-shadow:0 0 20px #0ff;}
        h1,h2 { color:#0ff; text-shadow:0 0 10px #0ff; }
        input, button { padding:10px; margin:5px; border-radius:10px; border:none; outline:none; font-size:16px; }
        input { width:150px; text-align:center;}
        button { cursor:pointer; background:#0ff; color:#000; font-weight:bold; transition:0.3s;}
        button:hover { background:#0aa; color:#fff;}
        table { margin:auto; border-collapse:collapse; margin-top:20px;}
        td { width:80px; height:80px; font-size:50px; text-align:center; vertical-align:middle; border:2px solid #0ff; cursor:pointer; transition:0.2s; color:#0ff; text-shadow:0 0 5px #0ff;}
        td:hover { background:#0ff1; }
        #status { margin-top:15px; font-size:20px; color:#0ff; text-shadow:0 0 5px #0ff;}
        @media(max-width:500px){ td{ width:60px; height:60px; font-size:40px; } }
    </style>
</head>
<body>
<div id="container">
{% if not username %}
    <h1>Neon Tic Tac Toe ⚡</h1>
    <input id="name" placeholder="Your name" required>
    <button onclick="createRoom()">Create Room</button>
    <input id="join_code" placeholder="Room Code">
    <button onclick="joinRoom()">Join Room</button>
    <div id="msg" style="margin-top:10px;color:#f00;"></div>
{% else %}
    <h2>Room {{ room_id }} | Player {{ player_symbol }}</h2>
    <div id="countdown"></div>
    <table id="board">
        {% for i in range(3) %}
        <tr>
            {% for j in range(3) %}
            <td id="cell-{{i}}-{{j}}" onclick="makeMove({{i}},{{j}})"></td>
            {% endfor %}
        </tr>
        {% endfor %}
    </table>
    <div id="status">Waiting for opponent...</div>
    <button onclick="resetGame()">Reset Game</button>
{% endif %}
</div>

<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
<script>
const socket = io();
{% if not username %}
// create/join room
function createRoom(){
    const name = document.getElementById("name").value.trim();
    if(!name){ alert("Enter name"); return; }
    socket.emit("create_room",{name:name});
}
function joinRoom(){
    const name = document.getElementById("name").value.trim();
    const code = document.getElementById("join_code").value.trim();
    if(!name || !code){ alert("Enter name & room code"); return; }
    socket.emit("join_room",{name:name, room:code});
}
socket.on("room_created", data=>{
    window.location.href = `/?username=${data.name}&room=${data.room}&symbol=${data.symbol}`;
});
socket.on("room_joined", data=>{
    window.location.href = `/?username=${data.name}&room=${data.room}&symbol=${data.symbol}`;
});
socket.on("error_msg", msg=>{
    document.getElementById("msg").innerText = msg;
});
{% else %}

// Game logic
let board = [["","",""],["","",""],["","",""]];
let turn = "X";
let gameOver = false;
const mySymbol = "{{ player_symbol }}";
const room = "{{ room_id }}";

function makeMove(r,c){
    if(gameOver || board[r][c]!="" || turn!==mySymbol) return;
    socket.emit("make_move",{row:r,col:c,room:room});
}

function resetGame(){
    socket.emit("reset_game",{room:room});
}

// receive updates
socket.on("update_board", data=>{
    board = data.board;
    turn = data.turn;
    gameOver = data.gameOver;
    document.getElementById("status").innerText = data.status;
    for(let i=0;i<3;i++){
        for(let j=0;j<3;j++){
            document.getElementById(`cell-${i}-${j}`).innerText = board[i][j];
        }
    }
});

socket.on("countdown", num=>{
    document.getElementById("countdown").innerText = num>0 ? `Game starts in ${num}...` : "";
});
{% endif %}
</script>
</body>
</html>
"""

# --- Flask Routes ---
@app.route("/")
def index():
    username = request.args.get("username")
    room_id = request.args.get("room")
    player_symbol = request.args.get("symbol")
    if username and room_id and player_symbol:
        return render_template_string(HTML, username=username, room_id=room_id, player_symbol=player_symbol)
    return render_template_string(HTML, username=None)

# --- Socket.IO Events ---
def checkWin(board, player):
    for i in range(3):
        if all(board[i][j]==player for j in range(3)): return True
    for j in range(3):
        if all(board[i][j]==player for i in range(3)): return True
    if board[0][0]==board[1][1]==board[2][2]==player: return True
    if board[0][2]==board[1][1]==board[2][0]==player: return True
    return False

def checkTie(board):
    return all(cell!="" for row in board for cell in row)

def startCountdown(room):
    for i in range(3,0,-1):
        socketio.emit("countdown", i, room=room)
        socketio.sleep(1)
    socketio.emit("countdown", 0, room=room)

@socketio.on("create_room")
def handle_create(data):
    name = data["name"]
    code = ''.join(random.choices(string.digits,k=4))
    rooms[code] = {"players":[{"name":name,"symbol":"X","sid":request.sid}],
                   "board":[["","",""],["","",""],["","",""]],
                   "turn":"X","gameOver":False}
    join_room(code)
    emit("room_created", {"name":name,"room":code,"symbol":"X"})

@socketio.on("join_room")
def handle_join(data):
    name = data["name"]
    code = data["room"]
    room = rooms.get(code)
    if not room:
        emit("error_msg","Room does not exist!")
        return
    if len(room["players"])>=2:
        emit("error_msg","Room full!")
        return
    room["players"].append({"name":name,"symbol":"O","sid":request.sid})
    join_room(code)
    emit("room_joined", {"name":name,"room":code,"symbol":"O"})
    # start countdown
    socketio.start_background_task(startCountdown, code)

@socketio.on("make_move")
def handle_move(data):
    room_id = data["room"]
    r = data["row"]
    c = data["col"]
    game = rooms.get(room_id)
    if not game or game["gameOver"]: return
    if game["board"][r][c]!="": return
    sym = game["turn"]
    game["board"][r][c] = sym
    # check win/tie
    status = ""
    if checkWin(game["board"], sym):
        status = f"Player {sym} wins! 🎉"
        game["gameOver"] = True
        socketio.start_background_task(lambda: rematchCountdown(room_id))
    elif checkTie(game["board"]):
        status = "It's a tie! 🤝"
        game["gameOver"] = True
        socketio.start_background_task(lambda: rematchCountdown(room_id))
    else:
        game["turn"] = "O" if sym=="X" else "X"
        status = f"Player {game['turn']}'s turn"
    emit("update_board", {"board":game["board"],"turn":game["turn"],"gameOver":game["gameOver"],"status":status}, room=room_id)

def rematchCountdown(room):
    socketio.sleep(3)
    game = rooms.get(room)
    if not game: return
    game["board"] = [["","",""],["","",""],["","",""]]
    game["turn"] = "X"
    game["gameOver"] = False
    emit("update_board", {"board":game["board"],"turn":game["turn"],"gameOver":False,"status":"Player X's turn"}, room=room)

@socketio.on("reset_game")
def handle_reset(data):
    room_id = data["room"]
    game = rooms.get(room_id)
    if not game: return
    game["board"] = [["","",""],["","",""],["","",""]]
    game["turn"] = "X"
    game["gameOver"] = False
    emit("update_board", {"board":game["board"],"turn":game["turn"],"gameOver":False,"status":"Player X's turn"}, room=room_id)

if __name__=="__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT",5000)), allow_unsafe_werkzeug=True)
