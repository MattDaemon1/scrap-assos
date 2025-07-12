# Générateur de Leads pour Associations

Système automatisé de prospection d'associations françaises pour la création de sites web.

## Fonctionnalités

✅ **Scraping intelligent** des associations (Journal Officiel, HelloAsso)  
✅ **Analyse automatique** des sites web existants  
✅ **Génération de prospects qualifiés**  
✅ **Campagnes email personnalisées**  
✅ **Intégration Google Sheets** pour le suivi  
✅ **Templates email professionnels**  

## Installation rapide

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Configurer Google Sheets
python setup_google_sheets.py

# 3. Personnaliser vos informations
# Éditez config/sender_config.txt avec vos coordonnées

# 4. Lancer le générateur
python main.py
```

## Objectif
Cibler des associations ayant :
- Budget annuel : 10 000 € - 100 000 €
- Taille : 50-500 membres
- Secteurs : Éducation, Culture, Caritatif
- Présence en ligne faible/obsolète
- Activité récente (post-2020)

## Structure du projet
```
├── scrapers/           # Scripts de scraping
├── analyzers/          # Analyse des sites web
├── email_manager/      # Gestion des campagnes
├── utils/              # Google Sheets + utilitaires
├── config/             # Configuration
├── templates/          # Templates d'emails
└── tests/              # Suite de tests
```

## Workflow automatisé

1. **Scraping** : Extraction associations par département
2. **Analyse** : Vérification qualité sites web
3. **Qualification** : Export prospects avec besoin
4. **Campagne** : Envoi emails personnalisés
5. **Suivi** : Synchronisation Google Sheets

## Objectif mensuel
- 200-300 prospects scrapés
- 100-150 prospects qualifiés  
- 2-3 contrats/mois à 400€ = **800-1200€/mois**
