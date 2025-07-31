# Agent IA de lecture des stats de hockey à partir de commentaires Facebook

import re
from collections import defaultdict
import csv
import os
import json
from flask import Flask, request, render_template_string

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang='fr'>
<head>
  <meta charset='UTF-8'>
  <title>Stats Hockey</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f4f7fa; padding: 20px; }
    textarea { width: 100%; height: 150px; margin-bottom: 10px; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { border: 1px solid #ccc; padding: 10px; text-align: center; }
    th { background-color: #004080; color: white; }
    tr:nth-child(even) { background-color: #eef3f7; }
  </style>
</head>
<body>
  <h1>Coller les commentaires de hockey</h1>
  <form method="post">
    <textarea name="commentaires">{{ commentaires }}</textarea><br>
    <button type="submit">Analyser</button>
  </form>
  {% if stats %}
  <h2>Statistiques cumulatives</h2>
  <table>
    <tr><th>Nom</th><th>Buts</th><th>Passes</th></tr>
    {% for joueur, s in classement %}
      <tr><td>{{ joueur }}</td><td>{{ s['buts'] }}</td><td>{{ s['passes'] }}</td></tr>
    {% endfor %}
  </table>
  <h2>Top 3 buteurs</h2>
  <ol>
    {% for joueur, s in top_buteurs %}
      <li>{{ joueur }} : {{ s['buts'] }} buts</li>
    {% endfor %}
  </ol>
  {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    commentaires = ""
    stats = defaultdict(lambda: {'buts': 0, 'passes': 0})
    cumulative_file = "stats_cumulatives.json"
    cumulative_stats = defaultdict(lambda: {'buts': 0, 'passes': 0})

    if os.path.exists(cumulative_file):
        with open(cumulative_file, "r", encoding="utf-8") as f:
            cumulative_stats.update(json.load(f))

    if request.method == "POST":
        commentaires = request.form["commentaires"]
        for ligne in commentaires.strip().split("\n"):
            if ":" not in ligne:
                continue
            nom, contenu = ligne.split(":", 1)
            buts = re.search(r"(\d+)\s*but", contenu)
            passes = re.search(r"(\d+)\s*pass", contenu)
            stats[nom.strip()]["buts"] = int(buts.group(1)) if buts else 0
            stats[nom.strip()]["passes"] = int(passes.group(1)) if passes else 0

        for joueur, s in stats.items():
            cumulative_stats[joueur]['buts'] += s['buts']
            cumulative_stats[joueur]['passes'] += s['passes']

        with open(cumulative_file, "w", encoding="utf-8") as f:
            json.dump(cumulative_stats, f, ensure_ascii=False, indent=2)

    classement = sorted(cumulative_stats.items(), key=lambda x: (-x[1]['buts'], -x[1]['passes']))
    top_buteurs = classement[:3]

    return render_template_string(HTML_TEMPLATE, commentaires=commentaires, stats=cumulative_stats, classement=classement, top_buteurs=top_buteurs)

if __name__ == "__main__":
    app.run(debug=True)
