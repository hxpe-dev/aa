# Abyssal Ascension

### Pour lancer le jeu :
```bash
cd src/
python launcher.py
# ou 
py launcher.py
```


### Commandes pour générer un éxécutable fonctionnel :
```bash
cd src/
pyinstaller --clean --noconsole --contents-directory "." --icon="assets/icon.ico" --add-data "assets;assets" --add-data "world;world" launcher.py
```


### Lancer le site internet localement

Ouvrir le fichier `docs/index.html` dans un navigateur internet.
