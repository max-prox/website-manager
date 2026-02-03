from flask import Flask, render_template_string, request
import os

app = Flask(__name__)

count = 0  # global counter (memory based)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Counter</title>
    <style>
        body {
            font-family: Arial;
            text-align: center;
            margin-top: 100px;
        }
        button {
            padding: 15px 30px;
            font-size: 18px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <h1>Button Click Counter 😎</h1>
    <h2>Count: {{ count }}</h2>

    <form method="POST">
        <button type="submit">Click Me 🔥</button>
    </form>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    global count
    if request.method == "POST":
        count += 1
    return render_template_string(HTML, count=count)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
