from flask import Flask, render_template_string, request, session, redirect, jsonify
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

messages = []

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Mini Chat 💬</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f0f2f5;
            display: flex;
            justify-content: center;
            margin: 0;
            padding: 0;
        }
        #container {
            width: 400px;
            margin-top: 50px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }
        #chat-box {
            height: 300px;
            overflow-y: auto;
            border: 1px solid #ddd;
            padding: 10px;
            border-radius: 10px;
            background: #fafafa;
            margin-bottom: 10px;
        }
        .msg {
            margin: 5px 0;
            padding: 5px 10px;
            border-radius: 8px;
            max-width: 80%;
            word-wrap: break-word;
        }
        .msg.user { background: #dcf8c6; margin-left: auto; }
        .msg.other { background: #fff; margin-right: auto; border:1px solid #eee;}
        .time { font-size: 10px; color: gray; margin-left: 5px;}
        input, button {
            padding: 10px;
            border-radius: 20px;
            border: 1px solid #ccc;
            outline: none;
        }
        input { width: 70%; }
        button { width: 25%; background: #0084ff; color: white; border: none; cursor: pointer; }
        button:hover { background: #005bb5; }
        h2 { text-align: center; }
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
    <div id="chat-box">
        {% for m in messages %}
            <div class="msg {% if m.name==name %}user{% else %}other{% endif %}">
                <b>{{ m.name }}</b>: {{ m.text }} <span class="time">[{{ m.time }}]</span>
            </div>
        {% endfor %}
    </div>
    <form method="POST">
        <input name="msg" placeholder="Type a message... emojis too! 😃" required>
        <button type="submit">Send</button>
    </form>

<script>
function fetchMessages() {
    fetch("/messages")
        .then(res => res.json())
        .then(data => {
            let chatBox = document.getElementById("chat-box");
            chatBox.innerHTML = "";
            data.forEach(m => {
                let msgDiv = document.createElement("div");
                msgDiv.className = "msg " + (m.name === "{{ name }}" ? "user" : "other");
                msgDiv.innerHTML = `<b>${m.name}</b>: ${m.text} <span class="time">[${m.time}]</span>`;
                chatBox.appendChild(msgDiv);
            });
            chatBox.scrollTop = chatBox.scrollHeight; // Auto scroll
        });
}

// Auto refresh every 1.5 seconds
setInterval(fetchMessages, 1500);
</script>
{% endif %}
</div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def chat():
    if "name" not in session:
        if request.method == "POST":
            username = request.form.get("username")
            if username:
                session["name"] = username
                return redirect("/")
        return render_template_string(HTML, name=None, messages=messages)

    if request.method == "POST":
        msg = request.form.get("msg")
        if msg:
            messages.append({
                "name": session["name"],
                "text": msg,
                "time": datetime.now().strftime("%H:%M:%S")
            })

    return render_template_string(HTML, name=session["name"], messages=messages)

@app.route("/messages")
def get_messages():
    return jsonify(messages)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
