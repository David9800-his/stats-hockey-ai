from flask import Flask
from agent_stats_hockey import app as hockey_app

app = hockey_app

if __name__ == "__main__":
    app.run(debug=True, port=10000)
