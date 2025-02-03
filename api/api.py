from flask import Flask, jsonify, request, session
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
import json
import os
from bson import ObjectId

app = Flask(__name__)

# Configuration MongoDB
app.config["MONGO_URI"] = "mongodb://admin:admin123@mongodb:27017/videotheque?authSource=admin"
mongo = PyMongo(app)
bcrypt = Bcrypt(app)
app.secret_key = os.environ.get('SECRET_KEY', 'diane@&12?')


# Vérifier la connexion à MongoDB
try:
    mongo.db.command("ping")
    print(" Connexion à MongoDB réussie!")
except Exception as e:
    print("Échec de connexion à MongoDB: {}".format(e))

# Fonction pour insérer les films dans la base de données MongoDB
def importer_films():
    print("\n Importation des films...")

    try:
        # Lit le fichier JSON contenant les films
        with open('data/films.json', 'r', encoding="utf-8") as films_file:
            films_data = json.load(films_file)
        print("{} films chargés.".format(len(films_data)))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print("Erreur de lecture du fichier films.json: {}".format(e))
        return

    films_collection = mongo.db.films
    films_inseres = 0

    for film in films_data:
        if not films_collection.find_one({"Title": film.get("Title")}):
            films_collection.insert_one(film)
            films_inseres += 1
            print(" Film ajouté: {} " .format(film.get('Title', 'Titre inconnu')))

    print("\n {} Insertion  de films réusie !".format(films_inseres))

# ------ Fonction pour insérer les utilisateurs  ------------
def importer_utilisateurs():
    print("\n Importation des utilisateurs...")

    try:
        # Lit le fichier JSON contenant les utilisateurs
        with open('data/users.json', 'r', encoding="utf-8") as users_file:
            users_data = json.load(users_file)
        print(" utilisateurs chargés.".format(len(users_data)))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print("Erreur de lecture du fichier users.json:{}".format(e))
        return

    users_collection = mongo.db.users
    users_inseres = 0

    for user in users_data:
        # Vérifier si l'utilisateur existe déjà dans la base de données par son nom d'utilisateur
        if not users_collection.find_one({"username": user.get("username")}):
            # Hacher le mot de passe avant de l'insérer dans la base de données
            user["password"] = bcrypt.generate_password_hash(user["password"]).decode('utf-8')
            users_collection.insert_one(user)
            users_inseres += 1
            print(" Utilisateur ajouté : {}".format(user.get('username', 'Utilisateur inconnu')))

    print("{} utilisateurs insérés avec succès!".format(users_inseres))

# Lancer les deux importations de données
importer_films()
importer_utilisateurs()

# route pour obtenir les détails d'un film
@app.route('/films/<title>', methods=['GET'])
def film_detail(title):
    try:
        film = mongo.db.films.find_one({"Title": title}, {"_id": 0})
        if not film:
            return jsonify({"error": "Film non trouvé"}), 404
        return jsonify(film), 200
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la récupération du film : {e}"}), 500


# route pour vérifier si l'API fonctionne
@app.route('/')
def homepage():
    return jsonify({"message": "Bienvenu sur l'API de MA videothèque"})

# route permettant l'inscription
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if not data or 'username' not in data or 'password' not in data :
        return jsonify({"error": "Données manquantes"}), 400

    try:
        if mongo.db.users.find_one({"username": data['username']}):
            return jsonify({"error": "Nom d'utilisateur déjà utilisé"}), 400

        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        mongo.db.users.insert_one({"username": data['username'], "password": hashed_password})
        return jsonify({"message": "Bienvenu ! vous êtes à présent inscrit"}), 201
    except Exception as e:
        return jsonify({"error": f"Erreur lors de l'inscription : {e}"}), 500

# route permettant la connexion
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Données manquantes"}), 400

    try:
        user = mongo.db.users.find_one({"username": data['username']})
        if user and bcrypt.check_password_hash(user['password'], data['password']):
            session['username'] = data['username']
            return jsonify({"message": "Connexion réussie"}), 200
        return jsonify({"error": "Identifiants invalides"}), 401
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la connexion : {e}"}), 500

# route permettant la déconnexion
@app.route('/users/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({"message": "Déconnexion réussie"}), 200

# fonction pour vérifier si l'utilisateur est connecté
def verifier_connexion():
    if 'username' not in session:
        return {"error": "Veuillez vous connecter"}, 401
    return session['username'], 200

# route pour ajouter un film
"""@app.route('/films/add_film', methods=['POST'])
def add_film():
    username = verifier_connexion()
    
    data = request.json
    print("************************************************")

    if not data or "Title" not in data:
        return jsonify({"error": "Titre du film manquant"}), 400

    try:
        if mongo.db.films.find_one({"Title": data["Title"]}):
            return jsonify({"error": "Ce film existe déjà"}), 400
        # Ajout de l'utilisateur qui ajoute le film
        data["add_by"] = username
        mongo.db.films.insert_one(data)
        return jsonify({"message": "Film ajouté avec succès", "film": data}), 201
    except Exception as e:
        return jsonify({"error": f"Erreur lors de l'ajout du film : {e}"}), 500
"""
from bson import ObjectId

@app.route('/films/add_film', methods=['POST'])
def add_film():
    username = session.get('username')
    data = request.json
    print("************************************************")
    print(data)
    print("************************************************")
    if not data or "Title" not in data:
        return jsonify({"error": "Titre du film manquant"}), 400

    try:
        if mongo.db.films.find_one({"Title": data["Title"]}):
            return jsonify({"error": "Ce film existe déjà"}), 400
        # Ajout de l'utilisateur qui ajoute le film
        data["add_by"] = username
        result = mongo.db.films.insert_one(data)
        data["_id"] = str(result.inserted_id)  # Convert ObjectId to string
        return jsonify({"message": "Film ajouté avec succès", "film": data}), 201
    except Exception as e:
        print(f"Erreur lors de l'ajout du film : {e}")
        return jsonify({"error": f"Erreur lors de l'ajout du film : {e}"}), 500
# route pour visualiser la liste des films
@app.route('/films', methods=['GET'])
def consulter_films():
    try:
        # Récupération et validation des paramètres de pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        if page < 1 or per_page < 1:
            return jsonify({"error": "Les paramètres 'page' et 'per_page' doivent être positifs."}), 400
    except ValueError:
        return jsonify({"error": "Les paramètres 'page' et 'per_page' doivent être des entiers."}), 400

    skip = (page - 1) * per_page

    try:
        # Récupération des films avec pagination directement via MongoDB
        films_cursor = mongo.db.films.find({}, {"_id": 0}).skip(skip).limit(per_page)
        films = list(films_cursor)  # Conversion du curseur en liste

        if not films:
            return jsonify({"message": "Aucun film trouvé"}), 404

        return jsonify({
            "films": films,
            "page": page,
            "per_page": per_page
        }), 200
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la récupération des films : {e}"}), 500

@app.route('/films/recherche', methods=['GET'])
def recherche_film():
    query = request.args.get("query", "").strip()
    if not query:
        return jsonify({"error": "Le paramètre 'query' est requis."}), 400
    if len(query) > 100:
        return jsonify({"error": "Le paramètre 'query' est trop long."}), 400

    try:
        # Recherche des films par titre, réalisateur ou genre avec une limite de résultats
        films_cursor = mongo.db.films.find({
            "$or": [
                {"Title": {"$regex": query, "$options": "i"}},
                {"Director": {"$regex": query, "$options": "i"}},
                {"Genre": {"$regex": query, "$options": "i"}}
            ]
        }, {"_id": 0}).limit(50)  # Limite des résultats pour éviter les surcharges

        films = list(films_cursor)  # Conversion du curseur en liste

        if not films:
            return jsonify({"message": "Aucun film correspondant à la recherche."}), 404

        return jsonify({
            "films": films,
            "count": len(films)
        }), 200
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la recherche du film : {e}"}), 500

"""
# route pour visualiser la liste des films
@app.route('/films', methods=['GET'])
def consulter_films():
    page = int(request.args.get('page', 1)) 
    per_page = int(request.args.get('per_page', 10))  
    skip = (page - 1) * per_page
    try:
        films = list(mongo.db.films.find({}, {"_id": 0}).skip(skip).limit(per_page))
        if not films:
            return jsonify({"message": "Aucun film trouvé"}), 404
        return jsonify(films), 200
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la récupération des films : {e}"}), 500

# route pour rechercher un film
@app.route('/films/recherche', methods=['GET'])
def recherche_film():
    query = request.args.get("query", "")
    try:
        films = list(mongo.db.films.find({"$or": [
            {"Title": {"$regex": query, "$options": "i"}},
            {"Director": {"$regex": query, "$options": "i"}},
            {"Genre": {"$regex": query, "$options": "i"}}
        ]}, {"_id": 0}))
        return jsonify(films), 200
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la recherche du film : {e}"}), 500
"""
# route pour modifier un film
@app.route('/films/<string:title>', methods=['PUT'])
def modifie_film(title):
    username = verifier_connexion()
    data = request.json
    if not data:
        return jsonify({"error": "Données manquantes"}), 400

    try:
        film = mongo.db.films.find_one({"Title": title})
        if not film:
            return jsonify({"error": "Film introuvable"}), 404

        if film["add_by"] != username:
            return jsonify({"error": "Vous n'avez pas les droits pour modifier ce film"}), 403

        mongo.db.films.update_one({"Title": title}, {"$set": data})
        updated_film = mongo.db.films.find_one({"Title": title}, {"_id": 0})
        return jsonify({"message": "Film mis à jour", "film": updated_film}), 200
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la modification du film : {e}"}), 500

# route pour supprimer un film
@app.route('/films/<string:title>', methods=['DELETE'])
def supprime_film(title):
    username = verifier_connexion()
    try:
        film = mongo.films.find_one({"Title": title})
        if not film:
            return jsonify({"error": "Film introuvable"}), 404

        if film["add_by"] != username:
            return jsonify({"error": "Vous n'avez pas les droits pour supprimer ce film"}), 403

        mongo.db.films.delete_one({"Title": title})
        return jsonify({"message": "Film supprimé avec succès"}), 200
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la suppression du film : {e}"}), 500

# Lance l'application Flask pour l'API
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
