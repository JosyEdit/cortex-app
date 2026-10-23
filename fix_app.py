with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Si 'app = Flask' n'est pas présent au début, on l'ajoute
if 'app = Flask' not in content:
    content = 'from flask import Flask\napp = Flask(__name__)\n' + content

# Si 'application = ' est présent, on crée un alias 'app'
if 'application = ' in content and 'app = application' not in content:
    content += '\napp = application\n'

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Fichier app.py réparé !')
