import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import csv
import time
from datetime import datetime, timedelta
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_manager import DataManager
from utils.google_sheets_manager import GoogleSheetsManager
from config.settings import *

class EmailCampaignManager:
    def __init__(self, use_google_sheets=True):
        self.data_manager = DataManager()
        self.templates = self.load_templates()
        self.use_google_sheets = use_google_sheets
        self.gs_manager = GoogleSheetsManager() if use_google_sheets else None
        
    def load_templates(self):
        """Charger les templates d'email"""
        templates = {}
        template_dir = "templates"
        
        template_files = {
            1: "email_template_1.txt",
            2: "email_template_2.txt", 
            3: "email_template_3.txt"
        }
        
        for num, filename in template_files.items():
            filepath = os.path.join(template_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Séparer subject et body
                    lines = content.split('\n')
                    subject = lines[0].replace('Subject: ', '') if lines[0].startswith('Subject:') else f"Template {num}"
                    body = '\n'.join(lines[1:]).strip()
                    templates[num] = {'subject': subject, 'body': body}
            else:
                print(f"Template {filename} non trouvé")
        
        return templates
    
    def personalize_email(self, template_num, association, sender_info):
        """Personnaliser un email avec les données de l'association"""
        if template_num not in self.templates:
            raise ValueError(f"Template {template_num} non trouvé")
        
        template = self.templates[template_num]
        
        # Variables de personnalisation
        variables = {
            'nom_association': association.get('Nom', association.get('name', 'Votre association')),
            'departement': self.get_department_name(association.get('Département', association.get('department', ''))),
            'secteur_detecte': association.get('Secteur_Detecte', association.get('sector', 'associatif')),
            'prenom': sender_info.get('prenom', 'Jean'),
            'nom': sender_info.get('nom', 'Dupont'),
            'telephone': sender_info.get('telephone', '06.XX.XX.XX.XX'),
            'email': sender_info.get('email', 'contact@example.com'),
            'date_limite': (datetime.now() + timedelta(days=7)).strftime('%d/%m/%Y')
        }
        
        # Remplacer les variables dans le subject et body
        subject = template['subject']
        body = template['body']
        
        for var, value in variables.items():
            placeholder = '{{' + var + '}}'
            subject = subject.replace(placeholder, str(value))
            body = body.replace(placeholder, str(value))
        
        return {
            'subject': subject,
            'body': body,
            'recipient': association.get('Email', association.get('email', '')),
            'recipient_name': variables['nom_association']
        }
    
    def get_department_name(self, dept_code):
        """Convertir le code département en nom"""
        dept_names = {
            '18': 'Cher', '28': 'Eure-et-Loir', '36': 'Indre', 
            '37': 'Indre-et-Loire', '41': 'Loir-et-Cher', '45': 'Loiret',
            '75': 'Paris', '77': 'Seine-et-Marne', '78': 'Yvelines',
            '91': 'Essonne', '92': 'Hauts-de-Seine', '93': 'Seine-Saint-Denis',
            '94': 'Val-de-Marne', '95': 'Val-d\'Oise'
        }
        return dept_names.get(dept_code, f'département {dept_code}')
    
    def create_campaign_plan(self, prospects_file):
        """Créer un plan de campagne email"""
        prospects = self.data_manager.load_from_csv(prospects_file)
        
        if not prospects:
            print("Aucun prospect trouvé")
            return
        
        # Filtrer les prospects avec email
        valid_prospects = [p for p in prospects if p.get('Email') or p.get('email')]
        
        print(f"Prospects valides: {len(valid_prospects)}")
        
        # Planifier les envois (respecter la limite quotidienne)
        campaign_plan = []
        daily_limit = DAILY_EMAIL_LIMIT
        current_date = datetime.now()
        
        for i, prospect in enumerate(valid_prospects):
            day_offset = i // daily_limit
            send_date = current_date + timedelta(days=day_offset)
            
            campaign_plan.append({
                'prospect': prospect,
                'template': 1,  # Commencer par le template 1
                'send_date': send_date.strftime('%Y-%m-%d'),
                'status': 'planned'
            })
        
        # Sauvegarder le plan
        plan_filename = f"campaign_plan_{datetime.now().strftime('%Y%m%d')}.csv"
        self.save_campaign_plan(campaign_plan, plan_filename)
        
        return campaign_plan
    
    def save_campaign_plan(self, plan, filename):
        """Sauvegarder le plan de campagne"""
        output_data = []
        
        for item in plan:
            prospect = item['prospect']
            output_data.append({
                'Nom_Association': prospect.get('Nom', prospect.get('name', '')),
                'Email': prospect.get('Email', prospect.get('email', '')),
                'Departement': prospect.get('Département', prospect.get('department', '')),
                'Secteur': prospect.get('Secteur_Detecte', prospect.get('sector', '')),
                'Template': item['template'],
                'Date_Envoi': item['send_date'],
                'Statut': item['status'],
                'Date_Reponse': '',
                'Notes': ''
            })
        
        output_path = os.path.join("output", filename)
        self.data_manager.save_to_csv_direct(output_data, output_path)
        print(f"Plan de campagne sauvegardé: {output_path}")
    
    def preview_emails(self, campaign_plan, sender_info, max_preview=5):
        """Prévisualiser les emails avant envoi"""
        print("\n=== PRÉVISUALISATION DES EMAILS ===")
        
        for i, item in enumerate(campaign_plan[:max_preview]):
            prospect = item['prospect']
            template_num = item['template']
            
            print(f"\n--- Email {i+1} ---")
            print(f"Pour: {prospect.get('Nom', prospect.get('name', ''))}")
            print(f"Email: {prospect.get('Email', prospect.get('email', ''))}")
            
            try:
                email_content = self.personalize_email(template_num, prospect, sender_info)
                print(f"Sujet: {email_content['subject']}")
                print(f"Aperçu: {email_content['body'][:200]}...")
            except Exception as e:
                print(f"Erreur: {e}")
    
    def generate_sender_config(self):
        """Générer un fichier de config pour l'expéditeur"""
        config_content = """# Configuration de l'expéditeur
# Modifiez ces informations avant d'utiliser le système d'envoi

[SENDER_INFO]
prenom = Votre_Prenom
nom = Votre_Nom
telephone = 06.XX.XX.XX.XX
email = votre.email@example.com

[EMAIL_SMTP]
# Pour Gmail
smtp_server = smtp.gmail.com
smtp_port = 587
email_password = votre_mot_de_passe_app

# Pour Outlook/Hotmail
# smtp_server = smtp-mail.outlook.com
# smtp_port = 587

[CAMPAIGN_SETTINGS]
daily_limit = 50
delay_between_emails = 30
max_retries = 3
"""
        
        config_path = "config/sender_config.txt"
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print(f"Fichier de configuration créé: {config_path}")
        print("IMPORTANT: Modifiez ce fichier avec vos vraies informations avant d'envoyer des emails")
    
    def sync_to_google_sheets(self, campaign_plan, sheet_url=None):
        """Synchroniser le plan de campagne avec Google Sheets"""
        if not self.use_google_sheets or not self.gs_manager:
            print("⚠️  Google Sheets non configuré")
            return False
        
        try:
            # Se connecter à la feuille ou en créer une nouvelle
            if sheet_url:
                if not self.gs_manager.connect_to_sheet(sheet_url):
                    return False
            else:
                sheet_url = self.gs_manager.create_leads_sheet(f"Campagne {datetime.now().strftime('%Y%m%d')}")
                if not sheet_url:
                    return False
            
            # Préparer les données pour Google Sheets
            leads_data = []
            for item in campaign_plan:
                prospect = item['prospect']
                leads_data.append({
                    'Nom': prospect.get('Nom', prospect.get('name', '')),
                    'Email': prospect.get('Email', prospect.get('email', '')),
                    'Adresse': prospect.get('Adresse', prospect.get('address', '')),
                    'Département': prospect.get('Département', prospect.get('department', '')),
                    'Secteur_Detecte': prospect.get('Secteur_Detecte', prospect.get('sector', '')),
                    'Description': prospect.get('Description', prospect.get('description', '')),
                    'needs_website': True,  # Tous les prospects dans la campagne ont besoin d'un site
                    'website_quality': prospect.get('website_quality', 'poor')
                })
            
            # Ajouter à Google Sheets
            if self.gs_manager.add_leads(leads_data):
                print(f"✅ {len(leads_data)} prospects synchronisés avec Google Sheets")
                print(f"🔗 URL: {sheet_url}")
                return sheet_url
            
        except Exception as e:
            print(f"❌ Erreur synchronisation Google Sheets: {e}")
            return False
    
    def update_contact_status_in_sheets(self, email, status, template_used=None, response=None, notes=None):
        """Mettre à jour le statut de contact dans Google Sheets"""
        if not self.use_google_sheets or not self.gs_manager:
            return False
        
        return self.gs_manager.update_contact_status(
            email=email,
            status=status,
            template_used=template_used,
            response=response,
            notes=notes
        )

def main():
    manager = EmailCampaignManager()
    
    # Générer la config si elle n'existe pas
    if not os.path.exists("config/sender_config.txt"):
        manager.generate_sender_config()
    
    # Informations temporaires pour la démo
    sender_info = {
        'prenom': 'Jean',
        'nom': 'Dupont', 
        'telephone': '06.12.34.56.78',
        'email': 'jean.dupont@example.com'
    }
    
    # Chercher des fichiers de prospects
    output_dir = "output"
    if os.path.exists(output_dir):
        csv_files = [f for f in os.listdir(output_dir) if f.startswith("prospects_") and f.endswith(".csv")]
        
        if csv_files:
            print("Fichiers de prospects disponibles:")
            for i, filename in enumerate(csv_files):
                print(f"{i+1}. {filename}")
            
            choice = input("Entrez le numéro du fichier pour créer une campagne: ")
            if choice.isdigit() and 1 <= int(choice) <= len(csv_files):
                selected_file = csv_files[int(choice)-1]
                file_path = os.path.join(output_dir, selected_file)
                
                # Créer le plan de campagne
                campaign_plan = manager.create_campaign_plan(selected_file)
                if campaign_plan:
                    manager.preview_emails(campaign_plan, sender_info)
                    
                    print(f"\nCampagne préparée pour {len(campaign_plan)} prospects")
                    print("ATTENTION: Configurez d'abord vos informations dans config/sender_config.txt")
            else:
                print("Choix invalide")
        else:
            print("Aucun fichier de prospects trouvé dans output/")
            print("Exécutez d'abord l'analyseur de sites web pour générer des prospects")
    else:
        print("Dossier output/ non trouvé")

if __name__ == "__main__":
    main()
