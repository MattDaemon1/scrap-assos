# Guide d'utilisation - Générateur de Leads Associations

## Installation et premiers pas

### 1. Installation des dépendances
```bash
pip install -r requirements.txt
```

### 2. Configuration
1. Copiez `.env.example` vers `.env` et remplissez vos clés API
2. Modifiez `config/settings.py` pour ajuster les critères de ciblage

### 3. Utilisation

#### Option A: Mode guidé (recommandé)
```bash
python main.py
```
Puis suivez le menu interactif.

#### Option B: Scripts individuels

**Étape 1: Scraper des associations**
```bash
python scrapers/journal_officiel_scraper.py
```

**Étape 2: Analyser les sites web**
```bash
python analyzers/website_analyzer.py
```

**Étape 3: Créer une campagne email**
```bash
python email_manager/campaign_manager.py
```

## Workflow recommandé

### Semaine 1: Configuration et test
1. Configurer les critères dans `config/settings.py`
2. Tester le scraping sur 1-2 départements
3. Analyser quelques sites web
4. Créer les templates d'email personnalisés

### Semaine 2: Production
1. Scraper 3-5 départements prioritaires
2. Analyser tous les sites web récupérés
3. Exporter les prospects qualifiés
4. Lancer la première campagne email (50 contacts max)

### Hebdomadaire: Maintenance
1. Scraper 1 nouveau département
2. Analyser les nouveaux prospects
3. Relancer les prospects non-répondants
4. Suivre les réponses et conversions

## Critères de ciblage optimaux

### Associations à privilégier:
- **Budget**: 10 000 € - 100 000 € annuel
- **Taille**: 50-500 membres
- **Secteurs**: Formation, Culture, Caritatif
- **Localisation**: Départements Centre-Val de Loire en priorité
- **Activité**: Créées ou mises à jour depuis 2020

### Signaux d'opportunité:
✅ Pas de site web du tout  
✅ Site non-responsive (pre-2015)  
✅ Domaine non-sécurisé (HTTP)  
✅ Mention de subventions récentes  
✅ Organisation d'événements réguliers  

### Signaux d'évitement:
❌ Site web récent et moderne  
❌ Mention d'un webmaster/prestataire  
❌ Budget < 10k€ ou > 100k€  
❌ Association purement politique  
❌ Pas d'email de contact  

## Métriques de succès

### Objectifs mensuels:
- **Prospects scrapés**: 200-300
- **Prospects qualifiés**: 100-150
- **Emails envoyés**: 300-400
- **Taux de réponse**: 3-5%
- **Conversions**: 2-3 contrats
- **Revenus**: 800-1200€

### KPIs à suivre:
1. **Taux de scraping réussi**: > 80%
2. **Taux de sites analysés**: > 90%  
3. **Taux d'emails délivrés**: > 95%
4. **Taux d'ouverture**: > 20%
5. **Taux de réponse**: > 3%
6. **Taux de conversion**: > 2%

## Bonnes pratiques

### Scraping responsable:
- Respecter les délais entre requêtes (2-3 secondes)
- Limiter à 5 pages par département par jour
- Utiliser un User-Agent réaliste
- Ne pas surcharger les serveurs

### Email marketing éthique:
- Respecter la limite de 300 emails/jour
- Proposer un lien de désabonnement
- Personnaliser chaque message
- Suivre les règles RGPD

### Optimisation continue:
- A/B tester les templates d'email
- Analyser les taux de réponse par département
- Ajuster les critères selon les conversions
- Documenter les objections fréquentes

## Résolution de problèmes

### Erreurs de scraping:
- Vérifier la connexion internet
- Mettre à jour les sélecteurs CSS
- Réduire la fréquence des requêtes
- Changer le User-Agent

### Faible taux de réponse:
- Améliorer la personnalisation
- Tester de nouveaux templates
- Cibler d'autres départements
- Réduire le prix ou ajouter des services

### Blocages techniques:
- Utiliser un proxy/VPN
- Espacer davantage les requêtes
- Changer l'adresse IP d'envoi
- Utiliser plusieurs comptes email

## Support et évolution

### Améliorations prévues:
- [ ] Interface web pour le suivi
- [ ] API Instagram/Facebook pour enrichir les données
- [ ] IA pour qualifier automatiquement les prospects
- [ ] Intégration CRM (Airtable/Notion)
- [ ] Statistiques en temps réel

### Contact:
Pour toute question ou amélioration, documentez dans le fichier `issues.md`

## Tests et validation

### Exécuter les tests
```bash
# Tests manuels rapides (sans dépendances externes)
python tests/manual_tests.py

# Tests complets avec mocks
python tests/run_tests.py

# Test spécifique
python tests/run_tests.py --test test_data_manager.TestDataManager.test_save_and_load_csv

# Tests avec couverture de code
python tests/run_tests.py --coverage
```

### Types de tests disponibles

#### 1. Tests manuels (`manual_tests.py`)
- ✅ Vérification des imports
- ✅ Validation de la configuration  
- ✅ Test des fonctions de base
- ✅ Pas de dépendances externes

#### 2. Tests unitaires
- **`test_data_manager.py`** : Gestion des données CSV
- **`test_scraper.py`** : Extraction et filtrage
- **`test_website_analyzer.py`** : Analyse de sites web
- **`test_email_manager.py`** : Génération de campagnes
- **`test_integration.py`** : Workflow complet

### Résultats attendus
- **Taux de réussite** : > 90%
- **Couverture de code** : > 80%
- **Performance** : < 5s pour 1000 associations

### Debugging et résolution
```bash
# Analyser un test qui échoue
python -m unittest tests.test_data_manager.TestDataManager.test_save_and_load_csv -v

# Vérifier la configuration
python -c "from config.settings import *; print(f'Secteurs: {len(TARGET_SECTORS)}, Régions: {len(PRIORITY_REGIONS)}')"

# Test de connectivité
python -c "import requests; print('OK' if requests.get('https://httpbin.org/status/200').status_code == 200 else 'ERREUR')"
```
