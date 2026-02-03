from flask import Flask, render_template_string, request, session, redirect
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"  # required for session

messages = []

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Mini Chat</title>
    <style>
        body { font-family: Arial; }
        .msg { margin: 5px 0; }
        .time { color: gray; font-size: 12px; }
    </style>
</head>
<body>

{% if not name %}
    <h2>Enter your name 👇</h2>
    <form method="POST">
        <input name="username" placeholder="Your name" required>
        <button type="submit">Join Chat</button>
    </form>
{% else %}
    <h2>Welcome {{ name }} 👋</h2>
    <h3>Chat 💬</h3>

    {% for m in messages %}
        <div class="msg">
            <b>{{ m.name }}</b>: {{ m.text }}
            <span class="time">[{{ m.time }}]</span>
        </div>
    {% endfor %}

    <form method="POST">
        <input name="msg" placeholder="Type message" required>
        <button type="submit">Send</button>
    </form>
{% endif %}

</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def chat():
    if "name" not in session:
        if request.method == "POST":
            session["name"] = request.form["username"]
            return redirect("/")
        return render_template_string(HTML, name=None, messages=messages)

    if request.method == "POST" and "msg" in request.form:
        messages.append({
            "name": session["name"],
            "text": request.form["msg"],
            "time": datetime.now().strftime("%H:%M:%S")
        })

    return render_template_string(
        HTML,
        name=session["name"],
        messages=messages
    )

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
