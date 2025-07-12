# Générateur de Leads pour Associations

Système automatisé de prospection d'associations françaises pour la création de sites web.

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
├── data/              # Stockage des données
├── templates/         # Templates d'emails
├── config/            # Configuration
└── utils/             # Utilitaires
```

## Installation
```bash
pip install -r requirements.txt
```

## Utilisation
1. Configuration : `python config/setup.py`
2. Scraping : `python scrapers/journal_officiel_scraper.py`
3. Analyse : `python analyzers/website_analyzer.py`
4. Export : `python utils/export_leads.py`

## Objectif mensuel
- 50 contacts scrapés/semaine
- 100 emails envoyés/semaine  
- 2-3 contrats/mois à 400€ = 800-1200€/mois
