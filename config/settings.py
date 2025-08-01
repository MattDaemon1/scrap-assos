# Configuration
JOURNAL_OFFICIEL_URL = "https://www.journal-officiel.gouv.fr/associations"
HELLOASSO_URL = "https://www.helloasso.com"
ASSOCIATIONS_GOUV_URL = "https://www.data.associations.gouv.fr"

# Critères de ciblage
TARGET_SECTORS = [
    "formation", "education", "enseignement", "cours", "atelier",
    "culture", "festival", "theatre", "musique", "art",
    "caritatif", "solidarite", "aide", "social", "humanitaire",
    "protection animale", "environnement", "sport", "sante", "jeunesse"
]

# Budget ciblé (en euros)
MIN_BUDGET = 10000
MAX_BUDGET = 100000

# Taille ciblée (nombre de membres)
MIN_MEMBERS = 50
MAX_MEMBERS = 500

# Années d'activité récente
MIN_YEAR = 2020

# Régions prioritaires (codes départements)
TARGET_DEPARTMENTS = [
    "18", "28", "36", "37", "41", "45",              # Centre-Val de Loire
    "69", "01", "07", "26", "38", "42", "73", "74",  # Auvergne-Rhône-Alpes
    "13", "04", "05", "06", "83", "84",              # PACA
    "33", "24", "40", "47", "64",                    # Nouvelle-Aquitaine
    "75", "77", "78", "91", "92", "93", "94", "95",  # Île-de-France
]

PRIORITY_REGIONS = TARGET_DEPARTMENTS  # Alias pour compatibilité

# Email settings
EMAIL_PROVIDER = "sendgrid"  # ou "sendinblue"
DAILY_EMAIL_LIMIT = 300
EMAIL_SENDER_NAME = "Matthieu ALLART"
EMAIL_SENDER_EMAIL = "matthieu@mattkonnect.com"

# Configuration SMTP (à configurer selon votre fournisseur email)
EMAIL_SERVER = "smtp.gmail.com"  # Remplacez par votre serveur SMTP
EMAIL_PORT = 587
EMAIL_USERNAME = "matthieu@mattkonnect.com"  # Votre email
EMAIL_PASSWORD = ""  # À remplir avec votre mot de passe d'application

# Google Sheets settings
GOOGLE_SHEETS_ENABLED = True
GOOGLE_CREDENTIALS_FILE = "config/google_credentials.json"

# Paths
DATA_DIR = "data"
OUTPUT_DIR = "output"
TEMPLATES_DIR = "templates"
