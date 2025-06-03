# iot_server

_CPE IOT PROJECT - Python Communication Server_

## Prérequis

- Python 3.8 ou supérieur (idéalement 3.10+)
- `pip` (généralement inclus avec Python)
- (Optionnel mais recommandé) [venv](https://docs.python.org/fr/3/library/venv.html) pour créer un environnement virtuel

## Installation

1. **Cloner le dépôt**

```bash
git clone https://github.com/mathis-lambert/iot_server.git
cd iot_server
```

2. **Créer un environnement virtuel**

```bash
python -m venv .venv
```

3. **Activer l'environnement virtuel**

- Sur Linux/MacOS :
  ```bash
  source .venv/bin/activate
  ```
- Sur Windows :
  ```cmd
  .venv\Scripts\activate
  ```

4. **Installer les dépendances en mode développement**

```bash
pip install -e .
```

## Lancement du serveur

```bash
python src/iot_server/main.py
```

## Structure du projet

```
iot_server/
├── src/
│   └── iot_server/
│       └── main.py
├── pyproject.toml
├── README.md
└── ...
```

## Désactivation de l'environnement virtuel

```bash
deactivate
```

## Notes

- Pour toute contribution, veuillez suivre les bonnes pratiques de développement Python.
- N'hésitez pas à ouvrir une issue pour tout problème ou suggestion.

---