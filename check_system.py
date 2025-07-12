#!/usr/bin/env python3
"""
Script de vérification rapide du système
Contrôle que tous les composants sont fonctionnels
"""

import sys
import os
from pathlib import Path

def check_files():
    """Vérification des fichiers critiques"""
    print("🔍 Vérification des fichiers...")
    
    critical_files = [
        'main.py',
        'config/settings.py',
        'scrapers/journal_officiel_scraper.py',
        'analyzers/website_analyzer.py',
        'email_manager/campaign_manager.py',
        'utils/data_manager.py',
        'utils/google_sheets_manager.py',
        'requirements.txt'
    ]
    
    missing = []
    for file in critical_files:
        if not Path(file).exists():
            missing.append(file)
    
    if missing:
        print(f"❌ Fichiers manquants: {missing}")
        return False
    
    print("✅ Tous les fichiers critiques présents")
    return True

def check_imports():
    """Vérification des imports Python"""
    print("\n🐍 Vérification des imports...")
    
    try:
        import config.settings
        print("✅ config.settings")
        
        from scrapers.journal_officiel_scraper import JournalOfficielScraper
        print("✅ scrapers.journal_officiel_scraper")
        
        from analyzers.website_analyzer import WebsiteAnalyzer
        print("✅ analyzers.website_analyzer")
        
        from email_manager.campaign_manager import CampaignManager
        print("✅ email_manager.campaign_manager")
        
        from utils.data_manager import DataManager
        print("✅ utils.data_manager")
        
        from utils.google_sheets_manager import GoogleSheetsManager
        print("✅ utils.google_sheets_manager")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False

def check_config():
    """Vérification de la configuration"""
    print("\n⚙️ Vérification de la configuration...")
    
    try:
        from config.settings import (
            TARGET_DEPARTMENTS,
            TARGET_SECTORS,
            MIN_BUDGET,
            MAX_BUDGET,
            PRIORITY_REGIONS,
            EMAIL_SENDER_NAME,
            EMAIL_SENDER_EMAIL
        )
        
        print(f"✅ Départements ciblés: {len(TARGET_DEPARTMENTS)}")
        print(f"✅ Secteurs ciblés: {len(TARGET_SECTORS)}")
        print(f"✅ Budget: {MIN_BUDGET:,}€ - {MAX_BUDGET:,}€")
        print(f"✅ Email configuré: {EMAIL_SENDER_NAME} <{EMAIL_SENDER_EMAIL}>")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur de configuration: {e}")
        return False

def check_google_sheets():
    """Vérification de Google Sheets"""
    print("\n📊 Vérification Google Sheets...")
    
    if Path("google_credentials.json").exists():
        print("✅ Fichier credentials présent")
        try:
            from utils.google_sheets_manager import GoogleSheetsManager
            # Test de connection sans erreur
            print("✅ Google Sheets Manager importé")
            return True
        except Exception as e:
            print(f"⚠️ Erreur Google Sheets: {e}")
            return False
    else:
        print("⚠️ Fichier google_credentials.json manquant")
        print("   Exécutez: python setup_google_sheets.py")
        return False

def check_templates():
    """Vérification des templates"""
    print("\n📧 Vérification des templates...")
    
    templates = list(Path("templates").glob("*.txt"))
    if len(templates) >= 3:
        print(f"✅ {len(templates)} templates trouvés")
        return True
    else:
        print(f"⚠️ Seulement {len(templates)} templates trouvés")
        return False

def main():
    """Fonction principale"""
    print("🚀 VÉRIFICATION DU SYSTÈME LEAD GENERATOR")
    print("=" * 50)
    
    checks = [
        check_files(),
        check_imports(),
        check_config(),
        check_google_sheets(),
        check_templates()
    ]
    
    success_count = sum(checks)
    total_count = len(checks)
    
    print("\n" + "=" * 50)
    print(f"📊 RÉSULTAT: {success_count}/{total_count} vérifications réussies")
    
    if success_count == total_count:
        print("🎉 Système prêt ! Exécutez: python main.py")
    elif success_count >= 3:
        print("⚠️ Système partiellement prêt")
        print("   Corrigez les erreurs puis relancez le check")
    else:
        print("❌ Système non fonctionnel")
        print("   Installez les dépendances: pip install -r requirements.txt")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
