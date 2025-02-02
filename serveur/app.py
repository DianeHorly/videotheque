# Gestion du frondend de l'application 
from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
import os
import math
from functools import wraps
 
# Initialisation de l'application Flask
app = Flask(__name__)
# clé secrete pour garantir que les sessions restent valides même si le serveur est rechargé
#app.secret_key ="admin@&12?" 
app.secret_key = os.environ.get('SECRET_KEY', 'admin@&12?')

# URL de l'API ,lien vers l'api
API_URL = "http://api:5001"

# --- Décorateur pour sécuriser les routes protégées ---
def login_required(f):
    """ Décorateur permettant de vérifier si l'utilisateur est connecté avant d'accéder à une page protégée."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash("Veuillez vous connecter pour accéder à cette page.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- route vers la page d'accueil ---
@app.route('/')
def accueil():
    """Page d'accueil : liste tous les films présents dans la DB."""
    try:
        response = requests.get(f"{API_URL}/films")
        print("Statut HTTP:", response.status_code)
        print("Réponse API:", response.text)  # Voir la réponse brute

        if response.status_code == 200:
            data = response.json()
            print("Données JSON brutes:", data)  # Voir le format JSON

            # Vérifier si "films" est bien la clé contenant les films
            films = data.get("films", []) if isinstance(data, dict) else data
        else:
            flash("Erreur lors de la récupération des films.", "danger")
            films = []
    except requests.exceptions.RequestException as e:
        flash(f"Erreur de connexion à l'API : {e}", "danger")
        films = []

    return render_template("accueil.html", films=films)

# --- Route pour afficher les films avec pagination ---
@app.route("/films", methods=['GET'])
def films():
    """Affiche la liste de tous les films présents dans la base, avec la possibilité de les filtrer par titre."""
    try:
        # Récupération et validation des paramètres de pagination
        page = int(request.args.get('page', 1))
        per_page = 30  # Nombre de films par page
        title_query = request.args.get('Title', '').strip()  # Recherche par titre

        if page < 1:
            flash("Le numéro de page doit être positif.", "error")
            page = 1
    except ValueError:
        flash("La page doit être un entier.", "error")
        page = 1

    # Préparation des paramètres à envoyer à l'API
    params = {
        "page": page,
        "per_page": per_page
    }

    if title_query:
        params["Title"] = title_query  # Ajout du paramètre de recherche par titre

    headers = {}
    if 'token' in session:
        headers['Authorization'] = f"Bearer {session.get('token')}"

    try:
        # Requête à l'API avec les paramètres de pagination et de filtrage
        response = requests.get(f"{API_URL}/films", params=params, headers=headers)
        print("Statut : {}".format(response.status_code))

        if response.status_code == 200:
            data = response.json()
            films_paginated = data.get("films", [])
            total_films = data.get("total_films", len(films_paginated))
            total_pages = math.ceil(total_films / per_page)
        elif response.status_code == 404:
            data = response.json()
            flash(data.get("message", "Aucun film trouvé."), "info")
            films_paginated = []
            total_pages = 1
        else:
            flash("Erreur lors de la récupération des films.", "danger")
            films_paginated = []
            total_pages = 1
    except requests.exceptions.RequestException as e:
        flash(f"Erreur de connexion à l'API : {e}", "danger")
        films_paginated = []
        total_pages = 1
    
    # attribut le champ '_id' à 'id' pour chaque film
    for film in films_paginated:
        if '_id' in film:
            film['id'] = str(film['_id'])  # Convertir ObjectId en string

    return render_template(
        "films1.html",
        films=films_paginated,
        page=page,
        total_pages=total_pages,
        title_query=title_query
    )


# ---route vers la page de Connexion ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Permet de gérer la connexion des utilisateurs."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash("Tous les champs sont obligatoires.", "error")
            return redirect(url_for('login'))
        try:
            response = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
            if response.status_code == 200:
                token = response.json().get('token')
                session['token'] = token
                session['username'] = username
                flash("Connexion réussie.", "success")
                return redirect(url_for('accueil'))
            else:
                flash(response.json().get("error", "Identifiants incorrects."), "error")
        except requests.RequestException as e:
            flash(f"Erreur de connexion : {e}", "danger")
    return render_template('login1.html')

# --- Route vers la page d'inscription ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Permet de gérer l'inscription des utilisateurs."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        #email = request.form.get('email')
        if not username or not password:
            flash("Tous les champs sont obligatoires.", "error")
            return redirect(url_for('register'))
        try:
            # demande la liste des utilisateurs a l'api
            response = requests.post(f"{API_URL}/register", json={"username": username, "password": password})
            print("statut : {}".format(response.status_code))
            if response.status_code == 201:
                flash("Inscription réussie ! Bienvenu dans Ma videothèque", "success")
                return redirect(url_for('login'))
            # Si le statut n'est pas 201, vérifier si la réponse contient du JSON
            if 'application/json' in response.headers.get('Content-Type', ''):
                try:
                    # Décodage de la réponse en JSON
                    response_json = response.json()
                    flash(response_json.get("error", "Nom d'utilisateur déjà pris ou erreur lors de l'inscription."), "error")
                except ValueError:
                    flash("Erreur : La réponse n'est pas au format JSON.", "error")
            else:
                flash("Erreur : La réponse du serveur n'est pas en JSON.", "error")
        except requests.RequestException as e:
            flash(f"Erreur de connexion : {e}", "danger")
    return render_template('register.html')

# ---Route vers la page de déconnexion ---
@app.route('/logout')
def logout():
    session.pop('token', None)
    session.pop('username', None)
    flash("Déconnexion réussie.", "success")
    return redirect(url_for('login'))

# Fonction pour récupérer la liste des films depuis l'API
def get_all_films():
    token = session.get('token')  # On récupère le token depuis la session de l'utilisateur
    response = requests.get(f"{API_URL}/films", headers={'Authorization': f'Bearer {token}'}) # On envoie une requête GET à l'API pour récupérer la liste des films
    print("statut : {}".format(response.status_code))
    if response.status_code == 200:  # Si la requête réussit
        return response.json()  # Retourne la liste des films
    else:
        return []  # Si la requête échoue, retourne une liste vide



@app.route('/films/add_film', methods=['GET', 'POST'])
@login_required
def add_film():
    """Ajouter un film."""
    if request.method == 'POST':
        data = {
            "Title": request.form.get('title', '').strip(),
            "Year": request.form.get('year', '').strip(),
            "Runtime": request.form.get('runtime', '').strip(),
            "Genre": [genre.strip() for genre in request.form.get('genre', '').split(",")],
            "Writer": request.form.get('writer', '').strip(),
            "Actors": [actor.strip() for actor in request.form.get('actors', '').split(",")],
            "Plot": request.form.get('plot', '').strip(),
            "Language": [lang.strip() for lang in request.form.get('language', '').split(",")],
            "Poster": request.form.get('poster', '').strip(),
            "format": request.form.get('format', '').strip()
        }

        try:
            # Envoi de la requête POST avec les données et l'en-tête d'autorisation
            response = requests.post(
                f"{API_URL}/films/add_film",
                json=data,
                headers={
                    'Authorization': session.get('username')  # Inclure le nom d'utilisateur dans les headers
                }
            )

            # Afficher le code de statut HTTP et la réponse brute pour le débogage
            print("Code de statut HTTP : {}".format(response.status_code))
            print("Réponse brute : {}".format(response.text))

            # Vérification du code d'état de la réponse
            if response.status_code in [200, 201]:
                flash("Film ajouté avec succès.", "success")
                return redirect(url_for('films'))
            else:
                try:
                    response_json = response.json()
                    print("Réponse JSON de l'API : ", response_json)  # Pour débogage
                    error_message = response_json.get("error", "Erreur lors de l'ajout du film.")
                except ValueError:
                    error_message = f"Erreur lors du décodage de la réponse JSON : {response.text}"
                flash(error_message, "danger")
        except requests.RequestException as e:
            flash(f"Erreur de connexion : {e}", "danger")
    return render_template('add_film.html', username=session.get('username'))



# --- Route pour modifier un film ---
@app.route('/edit_film/<string:title>', methods=['GET', 'POST'])
@login_required
def edit_film(title):
    """Modifier un film."""
    token = session.get('token')
    if request.method == 'POST':
        data = {
            "Year": request.form.get('year', '').strip(),
            "Runtime": request.form.get('runtime', '').strip(),
            "Genre": [genre.strip() for genre in request.form.get('genre', '').split(",")],
            "Writer": request.form.get('writer', '').strip(),
            "Actors": [actor.strip() for actor in request.form.get('actors', '').split(",")],
            "Plot": request.form.get('plot', '').strip(),
            "Language": [lang.strip() for lang in request.form.get('language', '').split(",")],
            "Poster": request.form.get('poster', '').strip(),
            "format": request.form.get('format', '').strip()
        }
        try:
            response = requests.put(f"{API_URL}/films/{title}", json=data, headers={'Authorization': f'Bearer {token}'})
            if response.status_code == 200:
                flash("Film modifié avec succès.", "success")
                return redirect(url_for('accueil'))
            else:
                error_message = response.json().get("error", "Erreur lors de la modification.")
                flash(error_message, "danger")
        except requests.RequestException as e:
            flash(f"Erreur de connexion : {e}", "danger")
    else:
        try:
            response = requests.get(f"{API_URL}/films/{title}", headers={'Authorization': f'Bearer {token}'})
            if response.status_code == 200:
                film = response.json()
            else:
                flash("Film introuvable.", "danger")
                return redirect(url_for('accueil'))
        except requests.RequestException as e:
            flash(f"Erreur de connexion : {e}", "danger")
            return redirect(url_for('accueil'))
    return render_template("edit_film.html", film=film, username=session.get('username'))

# --- Route pour la Suppression d'un film ---
@app.route('/delete_film/<string:title>', methods=['POST'])
@login_required
def delete_film(title):
    """Supprimer un film."""
    token = session.get('token')
    try:
        response = requests.delete(f"{API_URL}/films/{title}", headers={'Authorization': f'Bearer {token}'})
        if response.status_code == 200:
            flash("Film supprimé avec succès.", "success")
        else:
            error_message = response.json().get("error", "Erreur lors de la suppression.")
            flash(error_message, "danger")
    except requests.RequestException as e:
        flash(f"Erreur de connexion : {e}", "danger")
    return redirect(url_for('accueil'))

# --- Route vers la page de Recherche de films ---
@app.route('/search', methods=['GET'])
@login_required
def search_films():
    """Permet de rechercher des films par titre, genre ou auteur."""
    query = request.args.get("query", "").strip()
    if not query:
        flash("Veuillez entrer votre recherche.", "error")
        return redirect(url_for('films'))
    token = session.get('token')
    headers = {'Authorization': f'Bearer {token}'} if token else {}

    try:
        # Requête à l'API pour rechercher les films avec le terme de recherche
        response = requests.get(f"{API_URL}/films/recherche", params={"query": query}, headers=headers)
        if response.status_code == 200:
            data = response.json()
            films = data.get("films", [])
            total_films = len(films)
            total_pages = 1  # Adjust if the API supports pagination for search
        else:
            flash("Erreur lors de la recherche des films.", "danger")
            films = []
            total_films = 0
            total_pages = 1
    except requests.RequestException as e:
        flash(f"Erreur de connexion à l'API : {e}", "danger")
        films = []
        total_films = 0
        total_pages = 1
    return render_template('film_detail.html', films=films, page=1, total_pages=total_pages, title_query=query)

#route pour afficher les détails d'un film
@app.route('/film/<string:title>', methods=['GET'])
def film_detail(title):
    """Afficher les détails d'un film spécifique."""
    headers = {}
    if 'token' in session:
        headers['Authorization'] = f"Bearer {session.get('token')}"

    try:
        response = requests.get(f"{API_URL}/films/{title}", headers=headers)
        print("Statut HTTP:", response.status_code)
        print("Réponse API:", response.text)  # Voir la réponse brute

        if response.status_code == 200:
            try:
                film = response.json()
                print("Données JSON brutes:", film)  # Voir le format JSON
                return render_template('film_detail.html', film=film)
            except ValueError:
                flash(f"Erreur lors du décodage de la réponse JSON : {response.text}", "danger")
        else:
            try:
                error_message = response.json().get("error", "Erreur lors de la récupération du film.")
            except ValueError:
                error_message = f"Erreur lors du décodage de la réponse JSON : {response.text}"
            flash(error_message, "danger")
    except requests.RequestException as e:
        flash(f"Erreur de connexion à l'API : {e}", "danger")
    return redirect(url_for('accueil'))


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5002)
