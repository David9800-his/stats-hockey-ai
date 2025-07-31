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
    .error { color: red; font-weight: bold; margin-top: 20px; text-align: center; }
  </style>
</head>
<body>
  <h1>Coller les commentaires de hockey</h1>
  <form method="post">
    <textarea name="commentaires">{{ commentaires }}</textarea><br>
    <button type="submit">Analyser</button>
  </form>
  {% if error %}
    <div class="error">{{ error }}</div>
  {% endif %}
  {% if stats and not error %}
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

def extraire_stats(commentaires):
    stats = defaultdict(lambda: {'buts': 0, 'passes': 0})
    lignes_valides = 0
    for ligne in commentaires.strip().split("\n"):
        ligne = ligne.strip()
        if not ligne or ":" not in ligne:
            continue
        nom, contenu = ligne.split(":", 1)
        contenu = contenu.lower()

        # NLP simple pour attraper des phrases floues
        buts = re.search(r"(\d+)\s*(but|buts|goals?)", contenu)
        passes = re.search(r"(\d+)\s*(pass|passes|assists?)", contenu)
        if not buts and "but" in contenu:
            buts = re.search(r"(un|une)\s*but", contenu)
            if buts: buts = [None, "1"]
        if not passes and "pass" in contenu:
            passes = re.search(r"(une|un|1)\s*pass", contenu)
            if passes: passes = [None, "1"]

        if not buts and not passes:
            continue

        lignes_valides += 1
        stats[nom.strip()]["buts"] += int(buts[1]) if buts else 0
        stats[nom.strip()]["passes"] += int(passes[1]) if passes else 0

    return stats if lignes_valides > 0 else None

@app.route("/", methods=["GET", "POST"])
def index():
    commentaires = ""
    cumulative_file = "stats_cumulatives.json"
    cumulative_stats = defaultdict(lambda: {'buts': 0, 'passes': 0})
    error = None

    if os.path.exists(cumulative_file):
        with open(cumulative_file, "r", encoding="utf-8") as f:
            cumulative_stats.update(json.load(f))

    if request.method == "POST":
        commentaires = request.form["commentaires"]
        stats = extraire_stats(commentaires)

        if stats is None:
            error = "Aucune statistique détectée dans les commentaires. Assurez-vous qu'ils sont bien formatés."
        else:
            for joueur, s in stats.items():
                cumulative_stats[joueur]['buts'] += s['buts']
                cumulative_stats[joueur]['passes'] += s['passes']
            with open(cumulative_file, "w", encoding="utf-8") as f:
                json.dump(cumulative_stats, f, ensure_ascii=False, indent=2)

    classement = sorted(cumulative_stats.items(), key=lambda x: (-x[1]['buts'], -x[1]['passes']))
    top_buteurs = classement[:3]

    return render_template_string(HTML_TEMPLATE, commentaires=commentaires, stats=cumulative_stats if not error else None, classement=classement, top_buteurs=top_buteurs, error=error)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
