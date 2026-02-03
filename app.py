from flask import Flask, render_template_string, request, session, redirect
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

messages = []

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Mini Chat</title>
</head>
<body>

{% if not name %}
    <h2>Enter your name 👇</h2>
    <form method="POST">
        <input name="username" placeholder="Your name" required>
        <button type="submit">Join Chat</button>
    </form>
{% else %}
    <h2>Welcome {{ name }}</h2>

    {% for m in messages %}
        <p><b>{{ m.name }}</b>: {{ m.text }} <small>[{{ m.time }}]</small></p>
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
