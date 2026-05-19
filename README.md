# Abyssal Ascension


### Commandes pour générer un éxécutable fonctionnel :
```bash
cd src
pyinstaller --clean --noconsole --contents-directory "." --add-data "assets;assets" --add-data "world;world" --add-data "saves;saves" launcher.py
```