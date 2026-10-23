with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
idx = -1
for i, line in enumerate(lines):
    if '@app.route(\"/github\")' in line:
        idx = i
        break
if idx != -1:
    lines = lines[:idx]
    with open('app.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print('SUCCES: Ligne /github supprimee !')
else:
    print('La ligne n etait pas la. Le fichier est deja propre.')
