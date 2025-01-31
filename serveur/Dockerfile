FROM python:3.9

# Installez Python et pip, nettoyage de l'espace
RUN apt-get update && \
    apt-get install -y python3 python3-pip &&\
    apt-get clean 
    
# Créez et définissez le répertoire de travail
WORKDIR /app

# Copiez le fichier requirements.txt et installez les dépendances
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiez le reste de l'application
COPY app.py /app/app.py
COPY . /app

# Exposez le port sur lequel l'application Flask écoute
EXPOSE 5002

# Commande par défaut pour lancer l'application Flask
CMD ["python3", "app.py"]