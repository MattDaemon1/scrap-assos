import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import os
from datetime import datetime
import json

class GoogleSheetsManager:
    """Gestionnaire pour l'intégration avec Google Sheets"""
    
    def __init__(self, credentials_file=None, sheet_url=None):
        self.credentials_file = credentials_file or "config/google_credentials.json"
        self.sheet_url = sheet_url
        self.client = None
        self.current_sheet = None
        
    def setup_credentials(self):
        """Configurer les credentials Google Sheets"""
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        try:
            if os.path.exists(self.credentials_file):
                credentials = Credentials.from_service_account_file(
                    self.credentials_file, scopes=scopes
                )
                self.client = gspread.authorize(credentials)
                print(f"✅ Connexion Google Sheets réussie")
                return True
            else:
                print(f"❌ Fichier credentials non trouvé: {self.credentials_file}")
                return False
        except Exception as e:
            print(f"❌ Erreur connexion Google Sheets: {e}")
            return False
    
    def create_leads_sheet(self, sheet_name="Leads Associations"):
        """Créer une nouvelle feuille pour les leads"""
        if not self.client:
            if not self.setup_credentials():
                return None
        
        try:
            # Créer un nouveau spreadsheet
            spreadsheet = self.client.create(sheet_name)
            
            # Partager avec votre email (optionnel)
            spreadsheet.share('matthieu@mattkonnect.com', perm_type='user', role='writer')
            
            # Obtenir la première feuille
            worksheet = spreadsheet.sheet1
            
            # Configurer les en-têtes
            headers = [
                'Nom Association', 'Email', 'Telephone', 'Adresse', 'Département',
                'Secteur', 'Description', 'Site Web Actuel', 'Qualité Site',
                'Besoin Site', 'Statut Contact', 'Date Premier Contact',
                'Date Dernier Contact', 'Template Utilisé', 'Réponse',
                'Notes', 'Score Priorité', 'Date Création'
            ]
            
            worksheet.update('A1', [headers])
            
            # Formater les en-têtes
            worksheet.format('A1:R1', {
                'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 1.0},
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
            })
            
            print(f"✅ Feuille créée: {spreadsheet.url}")
            self.current_sheet = worksheet
            return spreadsheet.url
            
        except Exception as e:
            print(f"❌ Erreur création feuille: {e}")
            return None
    
    def connect_to_sheet(self, sheet_url):
        """Se connecter à une feuille existante"""
        if not self.client:
            if not self.setup_credentials():
                return False
        
        try:
            spreadsheet = self.client.open_by_url(sheet_url)
            self.current_sheet = spreadsheet.sheet1
            print(f"✅ Connexion à la feuille réussie")
            return True
        except Exception as e:
            print(f"❌ Erreur connexion feuille: {e}")
            return False
    
    def add_leads(self, leads_data):
        """Ajouter des leads dans la feuille"""
        if not self.current_sheet:
            print("❌ Aucune feuille connectée")
            return False
        
        try:
            # Préparer les données
            rows_to_add = []
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for lead in leads_data:
                row = [
                    lead.get('Nom', lead.get('name', '')),
                    lead.get('Email', lead.get('email', '')),
                    lead.get('Telephone', ''),
                    lead.get('Adresse', lead.get('address', '')),
                    lead.get('Département', lead.get('department', '')),
                    lead.get('Secteur_Detecte', lead.get('sector', '')),
                    lead.get('Description', lead.get('description', ''))[:200],  # Limiter
                    lead.get('website_url', ''),
                    lead.get('website_quality', ''),
                    'Oui' if lead.get('needs_website') else 'Non',
                    'Nouveau',  # Statut contact
                    '',  # Date premier contact
                    '',  # Date dernier contact
                    '',  # Template utilisé
                    '',  # Réponse
                    '',  # Notes
                    self.calculate_priority_score(lead),
                    current_time
                ]
                rows_to_add.append(row)
            
            # Ajouter à la feuille
            if rows_to_add:
                self.current_sheet.append_rows(rows_to_add)
                print(f"✅ {len(rows_to_add)} leads ajoutés à Google Sheets")
                return True
            
        except Exception as e:
            print(f"❌ Erreur ajout leads: {e}")
            return False
    
    def update_contact_status(self, email, status, template_used=None, response=None, notes=None):
        """Mettre à jour le statut de contact d'un lead"""
        if not self.current_sheet:
            return False
        
        try:
            # Trouver la ligne avec cet email
            all_records = self.current_sheet.get_all_records()
            
            for i, record in enumerate(all_records):
                if record.get('Email') == email:
                    row_num = i + 2  # +2 car commence à 1 et skip header
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Mettre à jour les colonnes
                    updates = []
                    if status:
                        updates.append({'range': f'K{row_num}', 'values': [[status]]})  # Statut Contact
                    
                    if not record.get('Date Premier Contact'):
                        updates.append({'range': f'L{row_num}', 'values': [[current_time]]})  # Date Premier Contact
                    
                    updates.append({'range': f'M{row_num}', 'values': [[current_time]]})  # Date Dernier Contact
                    
                    if template_used:
                        updates.append({'range': f'N{row_num}', 'values': [[template_used]]})  # Template
                    
                    if response:
                        updates.append({'range': f'O{row_num}', 'values': [[response]]})  # Réponse
                    
                    if notes:
                        current_notes = record.get('Notes', '')
                        new_notes = f"{current_notes}\n{current_time}: {notes}" if current_notes else f"{current_time}: {notes}"
                        updates.append({'range': f'P{row_num}', 'values': [[new_notes]]})  # Notes
                    
                    # Appliquer toutes les mises à jour
                    if updates:
                        self.current_sheet.batch_update(updates)
                        print(f"✅ Statut mis à jour pour {email}")
                        return True
            
            print(f"❌ Email non trouvé: {email}")
            return False
            
        except Exception as e:
            print(f"❌ Erreur mise à jour: {e}")
            return False
    
    def get_leads_to_contact(self, status_filter=None):
        """Récupérer les leads à contacter"""
        if not self.current_sheet:
            return []
        
        try:
            all_records = self.current_sheet.get_all_records()
            
            # Filtrer selon le statut
            if status_filter:
                filtered_records = [r for r in all_records if r.get('Statut Contact') in status_filter]
            else:
                filtered_records = [r for r in all_records if r.get('Statut Contact') in ['Nouveau', 'À relancer']]
            
            return filtered_records
            
        except Exception as e:
            print(f"❌ Erreur récupération leads: {e}")
            return []
    
    def calculate_priority_score(self, lead):
        """Calculer un score de priorité pour le lead"""
        score = 5  # Score de base
        
        # Bonus si email présent
        if lead.get('Email') or lead.get('email'):
            score += 3
        
        # Bonus si besoin de site web
        if lead.get('needs_website'):
            score += 2
        
        # Bonus selon le secteur
        sector = (lead.get('Secteur_Detecte') or lead.get('sector', '')).lower()
        if 'formation' in sector or 'education' in sector:
            score += 2
        elif 'culture' in sector:
            score += 1
        
        # Malus si site moderne existant
        if lead.get('website_quality') == 'good':
            score -= 2
        
        return min(max(score, 1), 10)  # Entre 1 et 10
    
    def export_statistics(self):
        """Exporter des statistiques vers une nouvelle feuille"""
        if not self.current_sheet:
            return False
        
        try:
            # Récupérer toutes les données
            all_records = self.current_sheet.get_all_records()
            
            # Calculer les statistiques
            stats = {
                'Total leads': len(all_records),
                'Avec email': len([r for r in all_records if r.get('Email')]),
                'Besoin site web': len([r for r in all_records if r.get('Besoin Site') == 'Oui']),
                'Contactés': len([r for r in all_records if r.get('Date Premier Contact')]),
                'Réponses': len([r for r in all_records if r.get('Réponse')]),
            }
            
            # Par secteur
            sectors = {}
            for record in all_records:
                sector = record.get('Secteur', 'Autre')
                sectors[sector] = sectors.get(sector, 0) + 1
            
            # Par département
            departments = {}
            for record in all_records:
                dept = record.get('Département', 'Inconnu')
                departments[dept] = departments.get(dept, 0) + 1
            
            print("\n📊 STATISTIQUES GOOGLE SHEETS")
            print("=" * 40)
            for key, value in stats.items():
                print(f"{key}: {value}")
            
            print(f"\nTop 5 secteurs:")
            for sector, count in sorted(sectors.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {sector}: {count}")
            
            print(f"\nTop 5 départements:")
            for dept, count in sorted(departments.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {dept}: {count}")
            
            return stats
            
        except Exception as e:
            print(f"❌ Erreur export statistiques: {e}")
            return None
    
    def generate_credentials_template(self):
        """Générer un template pour les credentials Google"""
        template = {
            "type": "service_account",
            "project_id": "votre-projet-id",
            "private_key_id": "votre-private-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\nvotre-private-key\n-----END PRIVATE KEY-----\n",
            "client_email": "votre-service-account@votre-projet.iam.gserviceaccount.com",
            "client_id": "votre-client-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/votre-service-account%40votre-projet.iam.gserviceaccount.com"
        }
        
        template_path = "config/google_credentials_template.json"
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2)
        
        print(f"✅ Template credentials créé: {template_path}")
        print("\n📝 INSTRUCTIONS:")
        print("1. Allez sur https://console.cloud.google.com/")
        print("2. Créez un nouveau projet ou sélectionnez un existant")
        print("3. Activez l'API Google Sheets et Google Drive")
        print("4. Créez un compte de service")
        print("5. Téléchargez le fichier JSON des credentials")
        print("6. Renommez-le en 'google_credentials.json' dans le dossier config/")

def main():
    """Test du gestionnaire Google Sheets"""
    gs_manager = GoogleSheetsManager()
    
    # Tester la connexion
    if gs_manager.setup_credentials():
        print("Connexion réussie!")
        
        # Créer une feuille de test
        sheet_url = gs_manager.create_leads_sheet("Test Leads Associations")
        if sheet_url:
            print(f"Feuille créée: {sheet_url}")
    else:
        print("Génération du template...")
        gs_manager.generate_credentials_template()

if __name__ == "__main__":
    main()
