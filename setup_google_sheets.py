#!/usr/bin/env python3
"""
Script de configuration pour Google Sheets
"""

import os
import json
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.google_sheets_manager import GoogleSheetsManager

def setup_google_sheets():
    """Configuration interactive de Google Sheets"""
    print("🔧 CONFIGURATION GOOGLE SHEETS")
    print("=" * 50)
    
    gs_manager = GoogleSheetsManager()
    
    # Vérifier si les credentials existent
    credentials_file = "config/google_credentials.json"
    
    if not os.path.exists(credentials_file):
        print("❌ Fichier credentials non trouvé")
        print("\n📝 ÉTAPES DE CONFIGURATION:")
        print("1. Allez sur https://console.cloud.google.com/")
        print("2. Créez un nouveau projet ou sélectionnez un existant")
        print("3. Activez l'API Google Sheets et Google Drive:")
        print("   - Recherchez 'Google Sheets API' et activez-la")
        print("   - Recherchez 'Google Drive API' et activez-la")
        print("4. Créez un compte de service:")
        print("   - IAM & Admin > Comptes de service > Créer un compte de service")
        print("   - Donnez un nom (ex: 'leads-generator')")
        print("   - Rôle: Éditeur de projet")
        print("5. Créez une clé:")
        print("   - Cliquez sur le compte créé > Clés > Ajouter une clé > JSON")
        print("   - Téléchargez le fichier JSON")
        print("6. Renommez le fichier en 'google_credentials.json'")
        print("7. Placez-le dans le dossier 'config/'")
        
        # Générer le template
        gs_manager.generate_credentials_template()
        print(f"\n✅ Template généré dans {credentials_file.replace('.json', '_template.json')}")
        return False
    
    # Tester la connexion
    print("🔄 Test de connexion...")
    if gs_manager.setup_credentials():
        print("✅ Connexion réussie!")
        
        # Proposer de créer une feuille
        create_sheet = input("\nVoulez-vous créer une nouvelle feuille de leads? (y/N): ")
        if create_sheet.lower() in ['y', 'yes', 'oui']:
            sheet_name = input("Nom de la feuille (défaut: 'Leads Associations'): ") or "Leads Associations"
            
            print(f"🔄 Création de la feuille '{sheet_name}'...")
            sheet_url = gs_manager.create_leads_sheet(sheet_name)
            
            if sheet_url:
                print(f"✅ Feuille créée avec succès!")
                print(f"🔗 URL: {sheet_url}")
                
                # Sauvegarder l'URL dans .env
                save_url = input("\nVoulez-vous sauvegarder cette URL dans .env? (Y/n): ")
                if save_url.lower() not in ['n', 'no', 'non']:
                    update_env_file(sheet_url)
                
                return True
        else:
            # Demander l'URL d'une feuille existante
            existing_url = input("\nURL de votre feuille Google Sheets existante (optionnel): ")
            if existing_url:
                if gs_manager.connect_to_sheet(existing_url):
                    print("✅ Connexion à la feuille existante réussie!")
                    update_env_file(existing_url)
                    return True
                else:
                    print("❌ Impossible de se connecter à cette feuille")
            
            return True
    else:
        print("❌ Échec de la connexion")
        print("Vérifiez que:")
        print("- Le fichier google_credentials.json est présent")
        print("- Les APIs Google Sheets et Drive sont activées")
        print("- Le compte de service a les bonnes permissions")
        return False

def update_env_file(sheet_url):
    """Mettre à jour le fichier .env avec l'URL de la feuille"""
    env_file = ".env"
    
    # Lire le fichier .env existant ou créer
    lines = []
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    
    # Mettre à jour ou ajouter GOOGLE_SHEETS_URL
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('GOOGLE_SHEETS_URL='):
            lines[i] = f'GOOGLE_SHEETS_URL={sheet_url}\n'
            updated = True
            break
    
    if not updated:
        lines.append(f'GOOGLE_SHEETS_URL={sheet_url}\n')
    
    # Sauvegarder
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"✅ URL sauvegardée dans {env_file}")

def test_google_sheets():
    """Tester l'intégration Google Sheets"""
    print("🧪 TEST GOOGLE SHEETS")
    print("=" * 30)
    
    gs_manager = GoogleSheetsManager()
    
    if not gs_manager.setup_credentials():
        print("❌ Échec du test - Credentials non configurés")
        return False
    
    # Test avec des données factices
    test_data = [
        {
            'Nom': 'Association Test',
            'Email': 'test@example.com',
            'Département': '18',
            'Secteur_Detecte': 'education',
            'needs_website': True,
            'website_quality': 'poor'
        }
    ]
    
    # Créer une feuille de test
    sheet_url = gs_manager.create_leads_sheet("Test Configuration")
    if sheet_url:
        print(f"✅ Feuille de test créée: {sheet_url}")
        
        # Ajouter des données de test
        if gs_manager.add_leads(test_data):
            print("✅ Données de test ajoutées")
            
            # Test de mise à jour
            if gs_manager.update_contact_status('test@example.com', 'Contacté', 'Template 1', notes='Test de configuration'):
                print("✅ Mise à jour de statut testée")
                
                # Statistiques
                stats = gs_manager.export_statistics()
                if stats:
                    print("✅ Export de statistiques testé")
                    print(f"Total leads dans la feuille: {stats.get('Total leads', 0)}")
                    
                    print("\n🎉 Tous les tests passés! Google Sheets est correctement configuré.")
                    return True
    
    print("❌ Échec des tests")
    return False

def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Configuration Google Sheets")
    parser.add_argument('--test', action='store_true', help="Tester la configuration")
    
    args = parser.parse_args()
    
    if args.test:
        success = test_google_sheets()
    else:
        success = setup_google_sheets()
    
    if success:
        print("\n✅ Configuration terminée avec succès!")
        print("Vous pouvez maintenant utiliser Google Sheets avec le générateur de leads.")
    else:
        print("\n❌ Configuration incomplète.")
        print("Consultez la documentation pour plus d'aide.")

if __name__ == "__main__":
    main()
