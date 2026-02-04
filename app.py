from flask import Flask, render_template_string, session, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import random

app = Flask(__name__)
app.secret_key = "supersecretkey"
socketio = SocketIO(app)

# Game state
games = {}  # room_id -> board + turn + players

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Multiplayer Tic Tac Toe 🎮</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; background:#f0f2f5; margin:0; }
        #container { text-align:center; background:white; padding:20px; border-radius:15px; box-shadow:0 4px 10px rgba(0,0,0,0.1); }
        h2 { margin-bottom:20px; }
        table { border-collapse: collapse; margin:auto; }
        td { width:80px; height:80px; font-size:50px; text-align:center; vertical-align:middle; border:2px solid #555; cursor:pointer; transition:0.3s; }
        td:hover { background:#e0e0e0; }
        #status { margin-top:20px; font-size:20px; }
        input, button { padding:10px; border-radius:10px; border:1px solid #ccc; margin-top:10px; }
        button { background:#0084ff; color:white; border:none; cursor:pointer; }
        button:hover { background:#005bb5; }
        @media(max-width:500px){ td{ width:60px; height:60px; font-size:40px; } }
    </style>
</head>
<body>
<div id="container">
    {% if not username %}
    <h2>Enter your name to play 🎮</h2>
    <form id="joinForm">
        <input id="username" placeholder="Your name" required>
        <input id="room" placeholder="Room ID (1-9999)" required>
        <button type="submit">Join Game</button>
    </form>
    {% else %}
    <h2>Room {{ room_id }} | Player: {{ username }} ({{ player_symbol }})</h2>
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
// Join form
document.getElementById("joinForm").onsubmit = function(e){
    e.preventDefault();
    const username = document.getElementById("username").value;
    const room = document.getElementById("room").value;
    window.location.href = `/?username=${username}&room=${room}`;
};
{% else %}

let board = [
    ["","",""],
    ["","",""],
    ["","",""]
];
let turn = "X";
let gameOver = false;
const mySymbol = "{{ player_symbol }}";
const room = "{{ room_id }}";

function makeMove(row,col){
    if(gameOver || board[row][col]!=="" || turn!==mySymbol) return;
    socket.emit("make_move",{row:row,col:col,room:room});
}

socket.on("update_board", function(data){
    board = data.board;
    turn = data.turn;
    gameOver = data.gameOver;
    for(let i=0;i<3;i++){
        for(let j=0;j<3;j++){
            document.getElementById(`cell-${i}-${j}`).innerText = board[i][j];
        }
    }
    document.getElementById("status").innerText = data.status;
});

function resetGame(){
    socket.emit("reset_game",{room:room});
}
{% endif %}
</script>
</body>
</html>
"""

from flask import request

@app.route("/")
def index():
    username = request.args.get("username")
    room_id = request.args.get("room")
    player_symbol = None
    if username and room_id:
        room_id = str(room_id)
        if room_id not in games:
            # init game
            games[room_id] = {
                "board":[["","",""],["","",""],["","",""]],
                "turn":"X",
                "players":[],
                "gameOver":False
            }
        # Assign player symbol
        if username not in [p["name"] for p in games[room_id]["players"]]:
            if len(games[room_id]["players"])<2:
                sym = "X" if not games[room_id]["players"] else "O"
                games[room_id]["players"].append({"name":username,"symbol":sym})
        # find symbol
        for p in games[room_id]["players"]:
            if p["name"]==username:
                player_symbol = p["symbol"]
        return render_template_string(HTML, username=username, room_id=room_id, player_symbol=player_symbol)
    return render_template_string(HTML, username=None)

# Socket.IO events
def checkWin(board, player):
    for i in range(3):
        if all(board[i][j]==player for j in range(3)):
            return True
    for j in range(3):
        if all(board[i][j]==player for i in range(3)):
            return True
    if board[0][0]==board[1][1]==board[2][2]==player: return True
    if board[0][2]==board[1][1]==board[2][0]==player: return True
    return False

def checkTie(board):
    return all(cell!="" for row in board for cell in row)

@socketio.on("make_move")
def handle_move(data):
    room_id = data["room"]
    row = data["row"]
    col = data["col"]
    game = games.get(room_id)
    if not game or game["gameOver"]: return
    turn = game["turn"]
    if game["board"][row][col]!="": return
    game["board"][row][col] = turn
    # Check win/tie
    status = ""
    if checkWin(game["board"], turn):
        status = f"Player {turn} wins! 🎉"
        game["gameOver"] = True
    elif checkTie(game["board"]):
        status = "It's a tie! 🤝"
        game["gameOver"] = True
    else:
        # switch turn
        game["turn"] = "O" if turn=="X" else "X"
        status = f"Player {game['turn']}'s turn"
    emit("update_board", {"board":game["board"],"turn":game["turn"],"gameOver":game["gameOver"],"status":status}, room=request.sid, broadcast=True)

@socketio.on("reset_game")
def handle_reset(data):
    room_id = data["room"]
    game = games.get(room_id)
    if not game: return
    game["board"] = [["","",""],["","",""],["","",""]]
    game["turn"] = "X"
    game["gameOver"] = False
    emit("update_board", {"board":game["board"],"turn":game["turn"],"gameOver":game["gameOver"],"status":"Player X's turn"}, room=request.sid, broadcast=True)

if __name__=="__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
