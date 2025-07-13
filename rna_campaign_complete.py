#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RNA CAMPAIGN COMPLETE - Campagne complète avec suivi
===================================================
Envoi + tracking + gestion des retours intégrée
"""

import pandas as pd
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import sys
import os
from datetime import datetime
import configparser

# Importer le tracker
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from campaign_tracker import CampaignTracker

class RNACampaignComplete:
    """Campagne email RNA complète avec suivi"""
    
    def __init__(self):
        self.tracker = CampaignTracker()
        self.smtp_config = self._load_smtp_config()
        self.email_template = self._load_email_template()
        self.contacts = self._load_contacts()
        
        # Importer contacts dans le tracker
        self.tracker.import_rna_contacts()
        
    def _load_smtp_config(self):
        """Charger configuration SMTP"""
        try:
            config = configparser.ConfigParser()
            config.read("config/sender_config.txt", encoding='utf-8')
            
            smtp_config = {
                'server': config.get('EMAIL_SMTP', 'smtp_server'),
                'port': config.getint('EMAIL_SMTP', 'smtp_port'),
                'email': config.get('SENDER_INFO', 'email'),
                'password': config.get('EMAIL_SMTP', 'email_password'),
                'use_ssl': config.getboolean('EMAIL_SMTP', 'use_ssl')
            }
            
            self.sender_info = {
                'prenom': config.get('SENDER_INFO', 'prenom'),
                'nom': config.get('SENDER_INFO', 'nom'),
                'telephone': config.get('SENDER_INFO', 'telephone'),
                'email': config.get('SENDER_INFO', 'email')
            }
            
            print(f"✅ Configuration SMTP chargée")
            return smtp_config
            
        except Exception as e:
            print(f"❌ Erreur configuration SMTP: {e}")
            sys.exit(1)
    
    def _load_email_template(self):
        """Charger template email"""
        try:
            with open("templates/email_template_1.txt", 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extraire objet et corps
            lines = content.split('\n')
            subject = "Opportunité de développement"
            body_start = 0
            
            for i, line in enumerate(lines):
                if line.startswith('Objet:') or line.startswith('Objet :'):
                    subject = line.replace('Objet:', '').replace('Objet :', '').strip()
                    body_start = i + 1
                    break
            
            body_lines = lines[body_start:]
            while body_lines and not body_lines[0].strip():
                body_lines.pop(0)
            
            body = '\n'.join(body_lines)
            
            print(f"✅ Template chargé")
            return {'subject': subject, 'body': body}
            
        except Exception as e:
            print(f"❌ Erreur template: {e}")
            sys.exit(1)
    
    def _load_contacts(self):
        """Charger contacts RNA"""
        try:
            df = pd.read_csv("data/rna_emails_clean_20250713_1608.csv")
            contacts = df.to_dict('records')
            print(f"✅ {len(contacts)} contacts chargés")
            return contacts
            
        except Exception as e:
            print(f"❌ Erreur contacts: {e}")
            sys.exit(1)
    
    def _personalize_email(self, contact):
        """Personnaliser email pour un contact"""
        try:
            # Données pour personnalisation
            data = {
                'nom_association': contact['nom_association'].replace("'", "").replace("é", "e"),
                'prenom_contact': 'Responsable',  # Par défaut
                'secteur_detecte': contact['secteur'],
                'departement': f"département de l'Ain ({contact['ville']})",
                'telephone': self.sender_info['telephone'],
                'prenom': self.sender_info['prenom'],
                'nom': self.sender_info['nom'],
                'email': self.sender_info['email']
            }
            
            # Personnaliser template
            subject_clean = self.email_template['subject'].replace('{{', '{').replace('}}', '}')
            body_clean = self.email_template['body'].replace('{{', '{').replace('}}', '}')
            
            subject = subject_clean.format(**data)
            body = body_clean.format(**data)
            
            return subject, body
            
        except Exception as e:
            print(f"❌ Erreur personnalisation: {e}")
            return None, None
    
    def send_campaign_with_tracking(self, test_mode=True, max_emails=None, delay_seconds=3):
        """Envoyer campagne avec suivi intégré"""
        print(f"\n🚀 CAMPAGNE RNA AVEC SUIVI")
        print(f"=" * 50)
        print(f"📧 Contacts: {len(self.contacts)}")
        print(f"🧪 Mode test: {'OUI' if test_mode else 'NON'}")
        print(f"⏱️  Délai entre envois: {delay_seconds}s")
        
        if max_emails:
            print(f"📊 Limite: {max_emails} emails")
        
        if test_mode:
            print(f"⚠️  MODE TEST - Emails vers matt@mattkonnect.com")
        
        # Confirmation
        if not test_mode:
            confirm = input(f"\n❓ Confirmer envoi réel ? (oui/non): ")
            if confirm.lower() not in ['oui', 'o', 'yes', 'y']:
                print("❌ Campagne annulée")
                return
        
        # Connexion SMTP
        try:
            print(f"\n🔗 Connexion SMTP...")
            if self.smtp_config['use_ssl']:
                server = smtplib.SMTP_SSL(self.smtp_config['server'], self.smtp_config['port'])
            else:
                server = smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port'])
                server.starttls()
            
            server.login(self.smtp_config['email'], self.smtp_config['password'])
            print(f"✅ Connexion établie")
            
        except Exception as e:
            print(f"❌ Erreur connexion: {e}")
            return
        
        # Envoi avec tracking
        sent_count = 0
        error_count = 0
        contacts_to_send = self.contacts[:max_emails] if max_emails else self.contacts
        
        print(f"\n📤 ENVOI EN COURS...")
        
        for i, contact in enumerate(contacts_to_send, 1):
            try:
                # Personnaliser
                subject, body = self._personalize_email(contact)
                if not subject or not body:
                    error_count += 1
                    continue
                
                # Créer message
                msg = MIMEMultipart()
                msg['From'] = f"{self.sender_info['prenom']} {self.sender_info['nom']} <{self.smtp_config['email']}>"
                
                # Destination
                dest_email = "matt@mattkonnect.com" if test_mode else contact['email']
                msg['To'] = dest_email
                msg['Subject'] = subject
                
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
                
                # Envoyer
                server.send_message(msg)
                
                # Enregistrer dans le tracker
                envoi_id = self.tracker.log_email_sent(contact['email'], subject, "email_template_1")
                
                sent_count += 1
                print(f"  ✅ {i:2d}/{len(contacts_to_send)} - {contact['nom_association'][:35]}... → {dest_email}")
                
                # Délai
                if i < len(contacts_to_send):
                    time.sleep(delay_seconds)
                
            except Exception as e:
                error_count += 1
                print(f"  ❌ {i:2d}/{len(contacts_to_send)} - Erreur: {e}")
        
        server.quit()
        
        # Résumé avec dashboard
        print(f"\n🎉 CAMPAGNE TERMINÉE")
        print(f"✅ Emails envoyés: {sent_count}")
        print(f"❌ Erreurs: {error_count}")
        print(f"📊 Taux de succès: {(sent_count/(sent_count+error_count)*100):.1f}%")
        
        # Afficher dashboard mis à jour
        print(f"\n" + "="*50)
        self.tracker.get_dashboard()
        
        print(f"\n💡 PROCHAINES ÉTAPES:")
        print(f"  1. 💬 Surveiller les réponses")
        print(f"  2. 📊 Utiliser response_handler.py pour traiter les retours")
        print(f"  3. 📞 Suivre les leads chauds")
        print(f"  4. 📈 Analyser les performances")

def main():
    """Menu principal"""
    campaign = RNACampaignComplete()
    
    print(f"🎯 RNA CAMPAIGN COMPLETE")
    print(f"=" * 40)
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"🏛️ Source: RNA Département 01")
    print(f"📧 {len(campaign.contacts)} contacts disponibles")
    
    print(f"\n📋 OPTIONS:")
    print(f"  1. 🧪 Test (1 email)")
    print(f"  2. 🧪 Test limité (3 emails)")
    print(f"  3. 🚀 Campagne complète")
    print(f"  4. 📊 Dashboard actuel")
    print(f"  5. 💬 Gérer les réponses")
    print(f"  6. 🚪 Quitter")
    
    choice = input(f"\n❓ Votre choix (1-6): ").strip()
    
    if choice == '1':
        campaign.send_campaign_with_tracking(test_mode=True, max_emails=1)
    elif choice == '2':
        campaign.send_campaign_with_tracking(test_mode=True, max_emails=3)
    elif choice == '3':
        campaign.send_campaign_with_tracking(test_mode=False)
    elif choice == '4':
        campaign.tracker.get_dashboard()
    elif choice == '5':
        print(f"\n💡 Lancez: python response_handler.py")
    elif choice == '6':
        print(f"👋 Au revoir!")
    else:
        print(f"❌ Choix invalide")

if __name__ == "__main__":
    main()
