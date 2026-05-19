# Abyssal Ascension


### Commandes pour générer un éxécutable fonctionnel :
```bash
cd src
pyinstaller --clean --noconsole --contents-directory "." --icon="assets/icon.ico" --add-data "assets;assets" --add-data "world;world" launcher.py
```