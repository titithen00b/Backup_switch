# 🔧 Backup Switch Configs (GUI)

**Backup_SW** est une application Python avec interface graphique (Tkinter) permettant de :
- Sauvegarder automatiquement la configuration de switches (Cisco, Dell, HPE, Aruba...)
- Se connecter par SSH via Netmiko
- Gérer les prompts complexes (ex: Dell avec enable)
- Exporter les configs localement
- Utiliser un `.env` externe pour stocker les identifiants (non inclus dans l’exe)

## 🖥️ Interface
- Interface graphique avec champ IP/plages d’IP
- Sélecteur de dossier de sauvegarde
- Logs détaillés par switch
- Barre de progression
- Compatible `.exe` Windows autonome (via PyInstaller)

---

## 🚀 Utilisation

### 🐍 Depuis Python (mode développeur)

```bash
pip install -r requirements.txt
python backup.py
```

### 📦 Depuis l'exécutable (Windows)

1. Compiler avec `build_backup.bat`
2. Copier `backup.env` dans le même dossier que `backup.exe` (ex: `release/`)
3. Lancer `backup.exe`

---

## ⚙️ Configuration `backup.env`

Le fichier `.env` **n'est pas inclus dans l'exécutable** pour des raisons de sécurité.

Tu dois le fournir **à côté du `.exe`** et il doit contenir :

```env
CISCO_USER=admin
CISCO_PASS=password

ARUBA_USER=admin
ARUBA_PASS=password

HPE_USER=admin
HPE_PASS=password

DELL_USER=admin
DELL_PASS=password
DELL_ENABLE_PASS=enablepass

GENERIC_USER=admin
GENERIC_PASS=password
```

---

## 📦 Compilation en `.exe`

```bash
pyinstaller --noconsole --onefile --icon=icon.ico backup.py
```

Ou simplement :

```bash
build_backup.bat
```

Cela générera un `.exe` propre dans `release/` sans fichiers temporaires.

---

## 🔐 Sécurité

- Le fichier `backup.env` **n’est jamais compilé dans le .exe**
- Il doit rester à côté de `backup.exe`
- Cela évite toute fuite de mots de passe dans l’exécutable compilé
- Pour plus de sécurité : restreindre les ACL Windows sur `backup.env`

---

## 📝 Licence

Ce projet est distribué sous licence MIT. Voir [`LICENSE`](LICENSE).
