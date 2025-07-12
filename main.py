#!/usr/bin/env python3
"""
Script principal pour exécuter le générateur de leads d'associations
"""

import sys
import os
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.journal_officiel_scraper import JournalOfficielScraper
from analyzers.website_analyzer import WebsiteAnalyzer
from email_manager.campaign_manager import EmailCampaignManager
from utils.data_manager import DataManager
from config.settings import PRIORITY_REGIONS, TARGET_SECTORS

def main():
    print("=== GÉNÉRATEUR DE LEADS POUR ASSOCIATIONS ===")
    print("1. Scraper des associations")
    print("2. Analyser les sites web")
    print("3. Créer une campagne email")
    print("4. Fusionner les données")
    print("5. Voir les statistiques")
    print("0. Quitter")
    
    choice = input("\nVotre choix: ")
    
    if choice == "1":
        run_scraping()
    elif choice == "2":
        run_website_analysis()
    elif choice == "3":
        run_email_campaign()
    elif choice == "4":
        merge_data()
    elif choice == "5":
        show_statistics()
    elif choice == "0":
        print("Au revoir!")
    else:
        print("Choix invalide")

def run_scraping():
    """Exécuter le scraping d'associations"""
    print("\n=== SCRAPING D'ASSOCIATIONS ===")
    scraper = JournalOfficielScraper()
    
    # Choisir le département
    print("Départements prioritaires disponibles:")
    for i, dept in enumerate(PRIORITY_REGIONS[:10]):  # Limiter l'affichage
        print(f"{i+1}. {dept}")
    
    dept_choice = input("Entrez le numéro du département (ou 'all' pour tous): ")
    
    if dept_choice.lower() == 'all':
        departments = PRIORITY_REGIONS[:5]  # Limiter pour éviter les bannissements
    elif dept_choice.isdigit() and 1 <= int(dept_choice) <= len(PRIORITY_REGIONS):
        departments = [PRIORITY_REGIONS[int(dept_choice)-1]]
    else:
        print("Choix invalide")
        return
    
    # Paramètres de scraping
    max_pages = int(input("Nombre de pages à scraper par département (1-5): ") or "2")
    
    for dept in departments:
        print(f"\n--- Scraping département {dept} ---")
        associations = scraper.scrape_associations(
            department=dept,
            sector_keywords=TARGET_SECTORS,
            max_pages=max_pages
        )
        
        if associations:
            filename = f"associations_{dept}_{datetime.now().strftime('%Y%m%d')}.csv"
            scraper.data_manager.save_to_csv(associations, filename)
            print(f"✓ {len(associations)} associations sauvegardées dans {filename}")
        else:
            print("✗ Aucune association trouvée")

def run_website_analysis():
    """Exécuter l'analyse des sites web"""
    print("\n=== ANALYSE DES SITES WEB ===")
    analyzer = WebsiteAnalyzer()
    data_manager = DataManager()
    
    # Lister les fichiers disponibles
    csv_files = []
    if os.path.exists("data"):
        csv_files = [f for f in os.listdir("data") if f.endswith('.csv')]
    
    if not csv_files:
        print("Aucun fichier d'associations trouvé. Exécutez d'abord le scraping.")
        return
    
    print("Fichiers disponibles:")
    for i, filename in enumerate(csv_files):
        print(f"{i+1}. {filename}")
    
    choice = input("Entrez le numéro du fichier à analyser: ")
    if choice.isdigit() and 1 <= int(choice) <= len(csv_files):
        selected_file = csv_files[int(choice)-1]
        print(f"Analyse de {selected_file}...")
        analyzer.batch_analyze(selected_file)
    else:
        print("Choix invalide")

def run_email_campaign():
    """Créer une campagne email"""
    print("\n=== CRÉATION DE CAMPAGNE EMAIL ===")
    campaign_manager = EmailCampaignManager()
    
    # Chercher les fichiers de prospects
    prospect_files = []
    if os.path.exists("output"):
        prospect_files = [f for f in os.listdir("output") if f.startswith("prospects_") and f.endswith(".csv")]
    
    if not prospect_files:
        print("Aucun fichier de prospects trouvé.")
        print("Exécutez d'abord l'analyse des sites web pour générer des prospects.")
        return
    
    print("Fichiers de prospects disponibles:")
    for i, filename in enumerate(prospect_files):
        print(f"{i+1}. {filename}")
    
    choice = input("Entrez le numéro du fichier: ")
    if choice.isdigit() and 1 <= int(choice) <= len(prospect_files):
        selected_file = prospect_files[int(choice)-1]
        
        # Créer le plan de campagne
        campaign_plan = campaign_manager.create_campaign_plan(selected_file)
        
        if campaign_plan:
            print(f"\n✓ Plan de campagne créé pour {len(campaign_plan)} prospects")
            print("⚠️  IMPORTANT: Configurez vos informations dans config/sender_config.txt avant d'envoyer")
            
            # Générer la config si nécessaire
            if not os.path.exists("config/sender_config.txt"):
                campaign_manager.generate_sender_config()
    else:
        print("Choix invalide")

def merge_data():
    """Fusionner tous les fichiers de données"""
    print("\n=== FUSION DES DONNÉES ===")
    data_manager = DataManager()
    
    merged_data = data_manager.merge_csv_files("all_associations_merged.csv")
    
    if merged_data:
        print(f"✓ {len(merged_data)} associations fusionnées")
        
        # Exporter pour prospection
        prospects = [a for a in merged_data if a.get('email')]
        if prospects:
            data_manager.export_for_outreach(prospects, "all_prospects.csv")
            print(f"✓ {len(prospects)} prospects exportés")
    else:
        print("Aucune donnée à fusionner")

def show_statistics():
    """Afficher les statistiques"""
    print("\n=== STATISTIQUES ===")
    data_manager = DataManager()
    
    # Stats sur les données brutes
    if os.path.exists("data"):
        csv_files = [f for f in os.listdir("data") if f.endswith('.csv')]
        total_associations = 0
        
        for filename in csv_files:
            data = data_manager.load_from_csv(filename)
            total_associations += len(data)
        
        print(f"Fichiers de données: {len(csv_files)}")
        print(f"Total associations scrapées: {total_associations}")
    
    # Stats sur les prospects
    if os.path.exists("output"):
        prospect_files = [f for f in os.listdir("output") if f.startswith("prospects_") and f.endswith(".csv")]
        total_prospects = 0
        
        for filename in prospect_files:
            file_path = os.path.join("output", filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = sum(1 for line in f) - 1  # -1 pour l'en-tête
                    total_prospects += lines
                    print(f"{filename}: {lines} prospects")
            except:
                pass
        
        print(f"\nTotal prospects qualifiés: {total_prospects}")
        print(f"Potentiel revenus (à 400€/contrat, 2% conversion): {total_prospects * 0.02 * 400:.0f}€")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nArrêt du programme par l'utilisateur")
    except Exception as e:
        print(f"\nErreur: {e}")
        print("Pour plus d'informations, consultez les logs ou contactez le support")
