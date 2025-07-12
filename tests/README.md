# Tests - Générateur de Leads Associations

## Vue d'ensemble

Le système dispose d'une suite de tests complète pour valider tous les composants :

- ✅ **Tests manuels** : Validation rapide sans dépendances
- ✅ **Tests unitaires** : Tests détaillés avec mocks
- ✅ **Tests d'intégration** : Workflow complet
- ✅ **Tests de performance** : Scalabilité et vitesse

## Exécution des tests

### Tests rapides (recommandé)
```bash
python tests/manual_tests.py
```
**Durée** : ~10 secondes  
**Objectif** : Vérifier que le système est opérationnel

### Tests complets
```bash
python tests/run_tests.py
```
**Durée** : ~60 secondes  
**Objectif** : Validation exhaustive avec mocks

### Tests avec couverture
```bash
python tests/run_tests.py --coverage
```
**Prérequis** : `pip install coverage`

## Description des tests

### 1. Tests manuels (`manual_tests.py`)

| Test | Description | Validation |
|------|-------------|------------|
| **Import modules** | Vérification des imports | Tous les modules se chargent |
| **Configuration** | Validation des paramètres | Secteurs, régions, budgets cohérents |
| **Data Manager** | Gestion des données CSV | Sauvegarde/chargement/filtrage |
| **Website Analyzer** | Génération d'URLs | URLs valides générées |
| **Email Manager** | Templates et personnalisation | Templates chargés, variables remplacées |
| **Scraper** | Extraction de données | Email et département extraits |

### 2. Tests unitaires

#### `test_data_manager.py`
- ✅ Sauvegarde/chargement CSV
- ✅ Filtrage par département/secteur/email
- ✅ Détection automatique de secteur
- ✅ Export pour prospection
- ✅ Génération de statistiques

#### `test_scraper.py`
- ✅ Extraction d'emails (regex)
- ✅ Extraction de départements (codes postaux)
- ✅ Filtrage par secteur d'activité
- ✅ Gestion des erreurs HTTP
- ✅ Scraping d'informations détaillées

#### `test_website_analyzer.py`
- ✅ Génération d'URLs possibles
- ✅ Vérification d'existence de sites
- ✅ Analyse de qualité (SSL, responsive, technologies)
- ✅ Détection de sites modernes vs obsolètes
- ✅ Gestion des timeouts et erreurs

#### `test_email_manager.py`
- ✅ Chargement des templates
- ✅ Personnalisation des emails
- ✅ Conversion codes départements
- ✅ Planification de campagnes
- ✅ Respect des limites quotidiennes

#### `test_integration.py`
- ✅ Workflow complet (scraping → analyse → email)
- ✅ Cohérence des données
- ✅ Validation de la configuration
- ✅ Gestion d'erreurs globale
- ✅ Tests de performance (1000 associations)

## Métriques de qualité

### Objectifs de tests
- **Couverture de code** : > 80%
- **Taux de réussite** : > 95%
- **Performance** : < 5s pour 1000 associations
- **Fiabilité** : Zéro crash sur données valides

### Critères de validation

#### ✅ Tests passés si :
- Tous les modules s'importent
- Configuration cohérente
- Fonctions de base opérationnelles
- Workflow complet fonctionnel

#### ❌ Tests échoués si :
- Erreurs d'import ou de syntaxe
- Configuration incohérente
- Fonctions qui plantent
- Performance dégradée

## Debugging

### Commandes utiles
```bash
# Test spécifique
python -m unittest tests.test_data_manager.TestDataManager.test_save_and_load_csv -v

# Debug configuration
python -c "from config.settings import *; print(f'OK: {len(TARGET_SECTORS)} secteurs, {len(PRIORITY_REGIONS)} régions')"

# Test connectivité
python -c "import requests; print('Connexion:', 'OK' if requests.get('https://httpbin.org/status/200', timeout=5).status_code == 200 else 'KO')"

# Validation modules
python -c "from scrapers.journal_officiel_scraper import JournalOfficielScraper; print('Scraper: OK')"
```

### Problèmes fréquents

#### Import errors
```bash
# Solution : Vérifier le PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
# Ou sur Windows
set PYTHONPATH=%PYTHONPATH%;%CD%
```

#### Tests qui échouent
1. **Erreur de configuration** : Vérifier `config/settings.py`
2. **Problème de dépendances** : `pip install -r requirements.txt`
3. **Erreur de réseau** : Tests unitaires utilisent des mocks
4. **Données corrompues** : Nettoyer le dossier `data/`

#### Performance lente
1. **Réduire les datasets de test**
2. **Utiliser les tests manuels** (plus rapides)
3. **Vérifier l'espace disque**

## Intégration continue

### Pre-commit hooks
```bash
# Avant chaque commit
python tests/manual_tests.py && echo "✅ Tests OK, prêt pour commit"
```

### Validation avant déploiement
```bash
# Suite complète
python tests/run_tests.py --quick
python tests/manual_tests.py
python main.py  # Test du workflow principal
```

## Métriques de réussite

### Résultats attendus (tests manuels)
```
Import des modules............ ✅ PASSÉ
Configuration................. ✅ PASSÉ  
Data Manager.................. ✅ PASSÉ
Website Analyzer.............. ✅ PASSÉ
Email Manager................. ✅ PASSÉ
Scraper....................... ✅ PASSÉ

🎯 Résultat: 6/6 tests réussis (100.0%)
🎉 Tous les tests manuels sont passés! Le système est opérationnel.
```

### Résultats attendus (tests complets)
```
Tests réussis: 25+
Tests échoués: 0
Erreurs: 0
Taux de réussite: > 95%
🎉 Excellent! Le système est prêt pour la production
```

---

**Note** : Les tests sont conçus pour être exécutés sans dépendances externes (pas de scraping réel, utilisation de mocks). Cela permet une validation rapide et fiable du système.
