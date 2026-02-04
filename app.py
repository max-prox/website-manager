from flask import Flask, render_template_string
import os

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Tic Tac Toe 🎮</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; background:#f0f2f5; margin:0; }
        #container { text-align:center; background:white; padding:20px; border-radius:15px; box-shadow:0 4px 10px rgba(0,0,0,0.1); }
        h2 { margin-bottom:20px; }
        table { border-collapse: collapse; margin:auto; }
        td { width:80px; height:80px; font-size:50px; text-align:center; vertical-align:middle; border:2px solid #555; cursor:pointer; transition:0.3s; }
        td:hover { background:#e0e0e0; }
        #status { margin-top:20px; font-size:20px; }
        button { margin-top:20px; padding:10px 20px; border:none; border-radius:10px; background:#0084ff; color:white; font-size:16px; cursor:pointer; }
        button:hover { background:#005bb5; }
        @media(max-width:500px){ td{ width:60px; height:60px; font-size:40px; } }
    </style>
</head>
<body>
<div id="container">
    <h2>Tic Tac Toe 🎮</h2>
    <table id="board">
        {% for i in range(3) %}
        <tr>
            {% for j in range(3) %}
            <td onclick="makeMove({{i}},{{j}})" id="cell-{{i}}-{{j}}"></td>
            {% endfor %}
        </tr>
        {% endfor %}
    </table>
    <div id="status">Player X's turn</div>
    <button onclick="resetGame()">Reset Game</button>
</div>

<script>
let board = [
    ["","",""],
    ["","",""],
    ["","",""]
];
let turn = "X";
let gameOver = false;

function makeMove(row,col){
    if(gameOver || board[row][col] !== "") return;
    board[row][col] = turn;
    document.getElementById(`cell-${row}-${col}`).innerText = turn;
    if(checkWin(turn)){
        document.getElementById("status").innerText = "Player " + turn + " wins! 🎉";
        gameOver = true;
        return;
    }
    if(checkTie()){
        document.getElementById("status").innerText = "It's a tie! 🤝";
        gameOver = true;
        return;
    }
    turn = turn==="X" ? "O" : "X";
    document.getElementById("status").innerText = "Player " + turn + "'s turn";
}

function checkWin(player){
    for(let i=0;i<3;i++)
        if(board[i][0]===player && board[i][1]===player && board[i][2]===player) return true;
    for(let i=0;i<3;i++)
        if(board[0][i]===player && board[1][i]===player && board[2][i]===player) return true;
    if(board[0][0]===player && board[1][1]===player && board[2][2]===player) return true;
    if(board[0][2]===player && board[1][1]===player && board[2][0]===player) return true;
    return false;
}

function checkTie(){
    return board.flat().every(cell => cell !== "");
}

function resetGame(){
    board = [["","",""],["","",""],["","",""]];
    turn = "X";
    gameOver = false;
    document.getElementById("status").innerText = "Player X's turn";
    for(let i=0;i<3;i++){
        for(let j=0;j<3;j++){
            document.getElementById(`cell-${i}-${j}`).innerText = "";
        }
    }
}
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
