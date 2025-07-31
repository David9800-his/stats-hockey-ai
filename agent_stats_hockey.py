# Agent IA de lecture des stats de hockey avec interface joueur et administrateur

import re
from collections import defaultdict
import csv
import os
import json
from datetime import datetime, timedelta
from flask import Flask, request, render_template_string, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Requis pour les sessions

# --- Générer les mardis valides ---
def generer_dates_matchs():
    debut = datetime(2024, 9, 10)
    fin = datetime(2025, 4, 29)
    dates = []
    while debut <= fin:
        if debut.weekday() == 1 and not (debut.month == 12 and debut.day in [24, 31]):
            dates.append(debut.strftime('%Y-%m-%d'))
        debut += timedelta(days=1)
    return dates

DATES_MARDIS = generer_dates_matchs()

ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html lang='fr'>
<head>
  <meta charset='UTF-8'>
  <title>Admin - Stats Hockey</title>
  <style>
    body {
      font-family: 'Open Sans', sans-serif;
      background: linear-gradient(to right, #f0f4f8, #e1eaf1);
      padding: 40px;
      color: #333;
    }
    textarea, select { width: 100%; margin-bottom: 10px; padding: 10px; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { border: 1px solid #ccc; padding: 10px; text-align: center; }
    th {
      background-color: #003366;
      color: white;
      text-transform: uppercase;
      letter-spacing: 1px;
    }
    tr:nth-child(even) { background-color: #eef3f7; }
    .error { color: red; font-weight: bold; margin-top: 20px; text-align: center; }
  </style>
</head>
<body>
  <h1>Interface Administrateur – Ajouter les statistiques</h1>
  {% if not session.get('logged_in') %}
    <form method="post">
      <input type="password" name="password" placeholder="Mot de passe admin" required>
      <button type="submit">Se connecter</button>
    </form>
  {% else %}
    <form method="post">
      <select name="date" onchange="this.form.submit()">
        {% for d in dates %}
          <option value="{{ d }}" {% if d == selected_date %}selected{% endif %}>Match du {{ d }}</option>
        {% endfor %}
      </select>
      <textarea name="commentaires">{{ commentaires }}</textarea><br>
      <button type="submit">Analyser et mettre à jour les statistiques</button>
    </form>
    <form method="post">
      <button name="reset" value="1">Réinitialiser les statistiques</button>
    </form>
    <p><a href="/logout">Se déconnecter</a></p>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    <p><a href="/stats">→ Voir l'interface joueur</a></p>
  {% endif %}
</body>
</html>
  {% else %}
    <form method="post">
      <select name="date">
        {% for d in dates %}<option value="{{ d }}">Match du {{ d }}</option>{% endfor %}
      </select>
      <textarea name="commentaires">{{ commentaires }}</textarea><br>
      <button type="submit">Analyser et mettre à jour les statistiques</button>
    </form>
    <form method="post">
      <button name="reset" value="1">Réinitialiser les statistiques</button>
    </form>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    <p><a href="/stats">→ Voir l'interface joueur</a></p>
  {% endif %}
</body>
</html>
"""

PLAYER_TEMPLATE = """
<!DOCTYPE html>
<html lang='fr'>
<head>
  <meta charset='UTF-8'>
  <title>Stats Hockey</title>
  <style>
    body {
      font-family: 'Open Sans', sans-serif;
      background: linear-gradient(to right, #f0f4f8, #e1eaf1);
      padding: 40px;
      color: #333;
    }
    h1, h2 {
      text-align: center;
      color: #005A9C;
      margin-bottom: 30px;
    }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; background: white; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
    th, td { border: 1px solid #ccc; padding: 12px; text-align: center; }
    th { background-color: #005A9C; color: white; }
    tr:nth-child(even) { background-color: #f2f6f9; }
  </style>
</head>
<body>
  <h1>🏒 Statistiques cumulatives – Interface joueur</h1>
  <table>
    <tr><th>Nom</th><th>Buts</th><th>Passes</th><th>Points</th></tr>
    {% for joueur, s in classement %}
      <tr><td>{{ joueur }}</td><td>{{ s['buts'] }}</td><td>{{ s['passes'] }}</td><td>{{ s['buts'] + s['passes'] }}</td></tr>
    {% endfor %}
  </table>
  <h2>🥅 Top 3 buteurs</h2>
  <ol>{% for joueur, s in top_buteurs %}<li>{{ joueur }} : {{ s['buts'] }} buts</li>{% endfor %}</ol>
  <h2>🎯 Top 3 passeurs</h2>
  <ol>{% for joueur, s in top_passeurs %}<li>{{ joueur }} : {{ s['passes'] }} passes</li>{% endfor %}</ol>
  <h2>🏆 Top 3 points</h2>
  <ol>{% for joueur, s in top_points %}<li>{{ joueur }} : {{ s['buts'] + s['passes'] }} points</li>{% endfor %}</ol>
  <div style="text-align:center; margin-top:40px;">
    <a href="/" style="text-decoration:none; color:#005A9C; font-weight:bold;">→ Accès administrateur</a>
  </div>
</body>
</html>
"""

# --- Routes Flask ---

@app.route("/historique")
def historique():
    saisons = {
        "2022-2023": [],
        "2023-2024": [],
        "2024-2025": [],
        "2025-2026": []
    }
    for fichier in sorted(os.listdir(".")):
        if fichier.startswith("match_") and fichier.endswith(".json"):
            date_str = fichier.replace("match_", "").replace(".json", "")
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            annee = date_obj.year
            if date_obj >= datetime(2025, 9, 1):
                saisons["2025-2026"].append(date_str)
            elif date_obj >= datetime(2024, 9, 1):
                saisons["2024-2025"].append(date_str)
            elif date_obj >= datetime(2023, 9, 1):
                saisons["2023-2024"].append(date_str)
            else:
                saisons["2022-2023"].append(date_str)

    html = "<h1>Historique des matchs</h1>"
    for saison, dates in saisons.items():
        if dates:
            html += f"<h2>{saison}</h2><ul>"
            for d in dates:
                html += f"<li><a href='/telecharger/{d}'>Match du {d}</a></li>"
            html += "</ul>"
    return html"

@app.route("/telecharger/<date>")
def telecharger_csv(date):
    fichier = f"match_{date}.json"
    if not os.path.exists(fichier):
        return "Fichier introuvable", 404
    with open(fichier, "r", encoding="utf-8") as f:
        stats = json.load(f)
    from flask import Response
    lignes = ["Nom,Buts,Passes"]
    for joueur, s in stats.items():
        lignes.append(f"{joueur},{s['buts']},{s['passes']}")
    csv_content = "
".join(lignes)
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=stats_{date}.csv"}
    )

@app.route("/", methods=["GET", "POST"])
def admin():
    commentaires = ""
    error = None
    selected_date = request.form.get("date")

    if request.method == "POST" and not session.get("logged_in"):
        if request.form.get("password") == "Vanier":
            session["logged_in"] = True
            return redirect(url_for("admin"))
        else:
            error = "Mot de passe incorrect."

    if not session.get("logged_in"):
        existing_text = ""
    if selected_date and os.path.exists(f"match_{selected_date}.json"):
        with open(f"match_{selected_date}.json", "r", encoding="utf-8") as f:
            existing_text = "
".join([f"{joueur} : {val['buts']} buts, {val['passes']} passes" for joueur, val in json.load(f).items()])
    commentaires = existing_text if not commentaires else commentaires
    return render_template_string(ADMIN_TEMPLATE, session=session, commentaires=commentaires, error=error, dates=DATES_MARDIS, selected_date=selected_date)

    # Réinitialisation des stats
    if request.method == "POST" and request.form.get("reset") == "1":
        for fichier in os.listdir("."):
            if fichier.startswith("match_") and fichier.endswith(".json"):
                os.remove(fichier)
        return redirect(url_for("admin"))

    if request.method == "POST" and request.form.get("commentaires"):
        commentaires = request.form["commentaires"]
        stats = extraire_stats(commentaires)
        if not selected_date:
            error = "Veuillez sélectionner une date."
        elif not stats:
            error = "Aucune statistique détectée."
        else:
            with open(f"match_{selected_date}.json", "w", encoding="utf-8") as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            return redirect(url_for("stats"))

    return render_template_string(ADMIN_TEMPLATE, session=session, commentaires=commentaires, error=error, dates=DATES_MARDIS)

@app.route("/stats")
def stats():
    cumul = defaultdict(lambda: {"buts": 0, "passes": 0})

    for fichier in os.listdir("."):
        if fichier.startswith("match_") and fichier.endswith(".json"):
            with open(fichier, "r", encoding="utf-8") as f:
                match_stats = json.load(f)
                for joueur, sp in match_stats.items():
                    cumul[joueur]["buts"] += sp.get("buts", 0)
                    cumul[joueur]["passes"] += sp.get("passes", 0)

    classement = sorted(cumul.items(), key=lambda x: (-x[1]['buts'], -x[1]['passes'], x[0]))
    top_buteurs = sorted(cumul.items(), key=lambda x: -x[1]['buts'])[:3]
    top_passeurs = sorted(cumul.items(), key=lambda x: -x[1]['passes'])[:3]
    top_points = sorted(cumul.items(), key=lambda x: -(x[1]['buts'] + x[1]['passes']))[:3]

    return render_template_string(PLAYER_TEMPLATE,
        classement=classement,
        top_buteurs=top_buteurs,
        top_passeurs=top_passeurs,
        top_points=top_points)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("admin"))
