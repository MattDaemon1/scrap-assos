"""
Tests de validation manuelle pour vérifier le bon fonctionnement
des composants sans dépendances externes
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Tester que tous les modules s'importent correctement"""
    print("🔍 Test d'import des modules...")
    
    try:
        from config.settings import TARGET_SECTORS, PRIORITY_REGIONS
        print("✅ config.settings - OK")
    except Exception as e:
        print(f"❌ config.settings - Erreur: {e}")
        return False
    
    try:
        from utils.data_manager import DataManager
        print("✅ utils.data_manager - OK")
    except Exception as e:
        print(f"❌ utils.data_manager - Erreur: {e}")
        return False
    
    try:
        from scrapers.journal_officiel_scraper import JournalOfficielScraper
        print("✅ scrapers.journal_officiel_scraper - OK")
    except Exception as e:
        print(f"❌ scrapers.journal_officiel_scraper - Erreur: {e}")
        return False
    
    try:
        from analyzers.website_analyzer import WebsiteAnalyzer
        print("✅ analyzers.website_analyzer - OK")
    except Exception as e:
        print(f"❌ analyzers.website_analyzer - Erreur: {e}")
        return False
    
    try:
        from email_manager.campaign_manager import EmailCampaignManager
        print("✅ email_manager.campaign_manager - OK")
    except Exception as e:
        print(f"❌ email_manager.campaign_manager - Erreur: {e}")
        return False
    
    return True

def test_configuration():
    """Tester la configuration"""
    print("\n🔧 Test de la configuration...")
    
    from config.settings import TARGET_SECTORS, PRIORITY_REGIONS, MIN_BUDGET, MAX_BUDGET
    
    # Test des secteurs cibles
    if not TARGET_SECTORS or len(TARGET_SECTORS) == 0:
        print("❌ TARGET_SECTORS vide")
        return False
    print(f"✅ TARGET_SECTORS: {len(TARGET_SECTORS)} secteurs définis")
    
    # Test des régions prioritaires
    if not PRIORITY_REGIONS or len(PRIORITY_REGIONS) == 0:
        print("❌ PRIORITY_REGIONS vide")
        return False
    print(f"✅ PRIORITY_REGIONS: {len(PRIORITY_REGIONS)} départements définis")
    
    # Test des budgets
    if MIN_BUDGET >= MAX_BUDGET:
        print(f"❌ Budget incohérent: MIN={MIN_BUDGET}, MAX={MAX_BUDGET}")
        return False
    print(f"✅ Budget: {MIN_BUDGET}€ - {MAX_BUDGET}€")
    
    return True

def test_data_manager():
    """Tester le gestionnaire de données"""
    print("\n📊 Test du gestionnaire de données...")
    
    from utils.data_manager import DataManager
    
    try:
        # Initialisation
        dm = DataManager("test_manual")
        print("✅ Initialisation DataManager")
        
        # Test de données
        test_data = [
            {
                'name': 'Test Association',
                'email': 'test@example.com',
                'department': '18',
                'description': 'Association de test pour formation'
            }
        ]
        
        # Sauvegarde
        dm.save_to_csv(test_data, "manual_test.csv")
        print("✅ Sauvegarde CSV")
        
        # Chargement
        loaded = dm.load_from_csv("manual_test.csv")
        if len(loaded) == 1 and loaded[0]['name'] == 'Test Association':
            print("✅ Chargement CSV")
        else:
            print("❌ Problème de chargement CSV")
            return False
        
        # Détection de secteur
        sector = dm.detect_sector(test_data[0])
        if sector in ['education', 'culture', 'caritatif', 'environnement', 'autre']:
            print(f"✅ Détection secteur: {sector}")
        else:
            print(f"❌ Secteur détecté invalide: {sector}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur DataManager: {e}")
        return False

def test_website_analyzer():
    """Tester l'analyseur de sites web"""
    print("\n🌐 Test de l'analyseur de sites web...")
    
    from analyzers.website_analyzer import WebsiteAnalyzer
    
    try:
        analyzer = WebsiteAnalyzer()
        print("✅ Initialisation WebsiteAnalyzer")
        
        # Test génération URLs
        test_assoc = {'name': 'Association de Formation'}
        urls = analyzer.generate_possible_urls(test_assoc)
        
        if len(urls) > 0 and all(('.fr' in url or '.org' in url) for url in urls):
            print(f"✅ Génération URLs: {len(urls)} URLs générées")
        else:
            print(f"❌ Problème génération URLs: {urls}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur WebsiteAnalyzer: {e}")
        return False

def test_email_manager():
    """Tester le gestionnaire d'emails"""
    print("\n📧 Test du gestionnaire d'emails...")
    
    from email_manager.campaign_manager import EmailCampaignManager
    
    try:
        manager = EmailCampaignManager()
        print("✅ Initialisation EmailCampaignManager")
        
        # Test chargement templates
        templates = manager.templates
        if len(templates) > 0:
            print(f"✅ Templates chargés: {len(templates)} templates")
        else:
            print("⚠️  Aucun template chargé (normal si fichiers absents)")
        
        # Test conversion département
        dept_name = manager.get_department_name('18')
        if 'Cher' in dept_name or '18' in dept_name:
            print(f"✅ Conversion département: {dept_name}")
        else:
            print(f"❌ Conversion département échouée: {dept_name}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur EmailCampaignManager: {e}")
        return False

def test_scraper():
    """Tester le scraper"""
    print("\n🔍 Test du scraper...")
    
    from scrapers.journal_officiel_scraper import JournalOfficielScraper
    
    try:
        scraper = JournalOfficielScraper()
        print("✅ Initialisation JournalOfficielScraper")
        
        # Test extraction email
        email = scraper.extract_email("Contactez contact@test.fr pour infos")
        if email == "contact@test.fr":
            print("✅ Extraction email")
        else:
            print(f"❌ Extraction email échouée: {email}")
            return False
        
        # Test extraction département
        dept = scraper.extract_department("Adresse 18000 Bourges")
        if dept == "18":
            print("✅ Extraction département")
        else:
            print(f"❌ Extraction département échouée: {dept}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur JournalOfficielScraper: {e}")
        return False

def main():
    """Exécuter tous les tests manuels"""
    print("🧪 TESTS MANUELS - GÉNÉRATEUR DE LEADS ASSOCIATIONS")
    print("=" * 60)
    
    tests = [
        ("Import des modules", test_imports),
        ("Configuration", test_configuration),
        ("Data Manager", test_data_manager),
        ("Website Analyzer", test_website_analyzer),
        ("Email Manager", test_email_manager),
        ("Scraper", test_scraper)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"💥 Erreur critique dans {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS MANUELS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSÉ" if result else "❌ ÉCHOUÉ"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Résultat: {passed}/{total} tests réussis ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 Tous les tests manuels sont passés! Le système est opérationnel.")
    elif passed >= total * 0.8:
        print("⚠️  La plupart des tests passent, quelques ajustements peuvent être nécessaires.")
    else:
        print("🚨 Plusieurs tests échouent, des corrections sont nécessaires.")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
