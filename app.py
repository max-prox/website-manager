from flask import Flask, render_template_string, session, request, redirect
from flask_socketio import SocketIO, emit
from datetime import datetime
import os
import requests

app = Flask(__name__)
app.secret_key = "supersecretkey"
socketio = SocketIO(app)

messages = []

GIPHY_API_KEY = "T3pDFULRBq9mwUMHm29ePrtTteNeeP8M"

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Real-Time Chat 💬</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <style>
        body { font-family: 'Segoe UI', sans-serif; background:#f0f2f5; display:flex; justify-content:center; margin:0; padding:0;}
        #container { width:100%; max-width:500px; margin-top:20px; background:white; border-radius:10px; box-shadow:0 4px 10px rgba(0,0,0,0.1); padding:15px;}
        #chat-box { height:400px; overflow-y:auto; border:1px solid #ddd; padding:10px; border-radius:10px; background:#fafafa; margin-bottom:10px;}
        .msg { margin:5px 0; padding:5px 10px; border-radius:8px; max-width:80%; word-wrap:break-word; }
        .msg.user { background:#dcf8c6; margin-left:auto; }
        .msg.other { background:#fff; margin-right:auto; border:1px solid #eee; }
        .time { font-size:10px; color:gray; margin-left:5px;}
        input, button { padding:10px; border-radius:20px; border:1px solid #ccc; outline:none; }
        input { width:65%; }
        button { width:15%; background:#0084ff; color:white; border:none; cursor:pointer; }
        button:hover { background:#005bb5; }
        h2 { text-align:center; }
        #emoji-button, #gif-button { background:#eee; border-radius:50%; width:35px; height:35px; margin-left:5px; cursor:pointer; }
        #emoji-picker, #gif-picker { display:none; position:absolute; z-index:1000; background:white; border:1px solid #ddd; border-radius:10px; padding:5px; max-height:200px; overflow-y:auto; }
        #gif-picker img { width:60px; cursor:pointer; margin:3px; }
    </style>
</head>
<body>
<div id="container">
{% if not name %}
    <h2>Enter your name 👇</h2>
    <form method="POST">
        <input name="username" placeholder="Your name" required>
        <button type="submit">Join Chat</button>
    </form>
{% else %}
    <h2>Welcome {{ name }} 😎</h2>
    <div id="chat-box"></div>
    <form id="chatForm" style="display:flex; align-items:center;" onsubmit="return sendMsg();">
        <input id="msgInput" placeholder="Type a message..." required>
        <div id="emoji-button"><i class="fa-regular fa-face-smile"></i></div>
        <div id="gif-button"><i class="fa-solid fa-photo-film"></i></div>
        <button type="submit">Send</button>
    </form>
    <div id="emoji-picker"></div>
    <div id="gif-picker"></div>

<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@joeattardi/emoji-button@4.6.2/dist/index.js"></script>
<script>
const socket = io();
const msgInput = document.getElementById("msgInput");
const chatBox = document.getElementById("chat-box");

// Load old messages
const messages = {{ messages|tojson }};
messages.forEach(m => addMessage(m));

// Send message
function sendMsg(){
    const msg = msgInput.value;
    if(msg.trim()==="") return false;
    socket.emit("send_message", {name:"{{ name }}", text:msg, time:new Date().toLocaleTimeString()});
    msgInput.value = "";
    return false;
}

// Receive messages
socket.on("receive_message", function(m){
    addMessage(m);
});

function addMessage(m){
    const div = document.createElement("div");
    div.className = "msg " + (m.name==="{{ name }}" ? "user" : "other");
    div.innerHTML = `<b>${m.name}</b>: ${m.text} <span class="time">[${m.time}]</span>`;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Emoji picker
const picker = new EmojiButton({ position: 'top-start' });
document.querySelector('#emoji-button').addEventListener('click', () => { picker.togglePicker(document.querySelector('#emoji-button')); });
picker.on('emoji', emoji => { msgInput.value += emoji; });

// GIF picker
const gifButton = document.getElementById("gif-button");
const gifPicker = document.getElementById("gif-picker");
gifButton.addEventListener('click', () => { 
    gifPicker.style.display = gifPicker.style.display==='block'?'none':'block';
    fetchGifs('funny');
});

async function fetchGifs(query){
    gifPicker.innerHTML = '';
    const res = await fetch(`/gifs?q=${query}`);
    const data = await res.json();
    data.forEach(url=>{
        const img = document.createElement('img');
        img.src = url;
        img.onclick = ()=>{ msgInput.value += `<img src='${url}' width='80'>`; gifPicker.style.display='none'; };
        gifPicker.appendChild(img);
    });
}
</script>
{% endif %}
</div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if "name" not in session:
        if request.method=="POST":
            username = request.form.get("username")
            if username:
                session["name"] = username
                return redirect("/")
        return render_template_string(HTML, name=None, messages=messages)
    return render_template_string(HTML, name=session["name"], messages=messages)

@app.route("/gifs")
def get_gifs():
    q = request.args.get("q", "funny")
    url = f"https://api.giphy.com/v1/gifs/search?api_key={GIPHY_API_KEY}&q={q}&limit=10&rating=g"
    res = requests.get(url).json()
    return [item["images"]["downsized"]["url"] for item in res["data"]]

@socketio.on("send_message")
def handle_message(data):
    messages.append(data)
    socketio.emit("receive_message", data, broadcast=True)

if __name__=="__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
