#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAMPAIGN EMAIL SENDER - RNA ASSOCIATIONS
==========================================
Script simple pour envoyer des emails aux associations RNA du département 01
Données 100% réelles et officielles du Journal Officiel
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

# Configuration
DATA_FILE = "data/rna_emails_clean_20250713_1608.csv"
TEMPLATE_FILE = "templates/email_template_rna_20250713_1608.txt"
CONFIG_FILE = "config/sender_config.txt"

class RNACampaignSender:
    """Envoyeur de campagne email RNA"""
    
    def __init__(self):
        self.smtp_config = self._load_smtp_config()
        self.email_template = self._load_email_template()
        self.contacts = self._load_contacts()
        
    def _load_smtp_config(self):
        """Charger configuration SMTP"""
        try:
            import configparser
            config_parser = configparser.ConfigParser()
            config_parser.read(CONFIG_FILE, encoding='utf-8')
            
            # Extraire configuration SMTP
            config = {
                'SMTP_SERVER': config_parser.get('EMAIL_SMTP', 'smtp_server'),
                'SMTP_PORT': config_parser.get('EMAIL_SMTP', 'smtp_port'),
                'EMAIL_USER': config_parser.get('SENDER_INFO', 'email'),
                'EMAIL_PASSWORD': config_parser.get('EMAIL_SMTP', 'email_password')
            }
            
            print(f"✅ Configuration SMTP chargée: {config['SMTP_SERVER']}")
            return config
            
        except Exception as e:
            print(f"❌ Erreur configuration SMTP: {e}")
            sys.exit(1)
    
    def _load_email_template(self):
        """Charger template email"""
        try:
            with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
                template = f.read()
            
            print(f"✅ Template email chargé: {len(template)} caractères")
            return template
            
        except Exception as e:
            print(f"❌ Erreur template: {e}")
            sys.exit(1)
    
    def _load_contacts(self):
        """Charger contacts RNA"""
        try:
            df = pd.read_csv(DATA_FILE)
            contacts = df.to_dict('records')
            
            print(f"✅ Contacts chargés: {len(contacts)} associations")
            return contacts
            
        except Exception as e:
            print(f"❌ Erreur contacts: {e}")
            sys.exit(1)
    
    def _personalize_email(self, contact):
        """Personnaliser email pour un contact"""
        try:
            # Nettoyer le nom de l'association
            nom_clean = contact['nom_association'].replace("'", "").replace("é", "e").replace("É", "E")
            
            # Personnaliser le template
            email_content = self.email_template.format(
                nom_association=nom_clean,
                ville=contact['ville'],
                secteur=contact['secteur']
            )
            
            return email_content
            
        except Exception as e:
            print(f"❌ Erreur personnalisation: {e}")
            return None
    
    def send_campaign(self, test_mode=True, max_emails=None):
        """Envoyer campagne email"""
        print(f"\n🚀 LANCEMENT CAMPAGNE EMAIL RNA")
        print(f"=" * 50)
        print(f"📧 Contacts: {len(self.contacts)}")
        print(f"🧪 Mode test: {'OUI' if test_mode else 'NON'}")
        
        if max_emails:
            print(f"📊 Limite: {max_emails} emails")
        
        if test_mode:
            print(f"⚠️  MODE TEST - Emails envoyés à matt@mattkonnect.com")
        
        # Confirmation
        if not test_mode:
            confirm = input(f"\n❓ Confirmer envoi réel à {len(self.contacts)} associations ? (oui/non): ")
            if confirm.lower() not in ['oui', 'o', 'yes', 'y']:
                print("❌ Campagne annulée")
                return
        
        # Connexion SMTP
        try:
            context = ssl.create_default_context()
            server = smtplib.SMTP(self.smtp_config['SMTP_SERVER'], int(self.smtp_config['SMTP_PORT']))
            server.starttls(context=context)
            server.login(self.smtp_config['EMAIL_USER'], self.smtp_config['EMAIL_PASSWORD'])
            
            print(f"✅ Connexion SMTP établie")
            
        except Exception as e:
            print(f"❌ Erreur connexion SMTP: {e}")
            return
        
        # Envoi des emails
        sent_count = 0
        error_count = 0
        
        contacts_to_send = self.contacts[:max_emails] if max_emails else self.contacts
        
        for i, contact in enumerate(contacts_to_send, 1):
            try:
                # Personnaliser email
                email_content = self._personalize_email(contact)
                if not email_content:
                    error_count += 1
                    continue
                
                # Créer message
                msg = MIMEMultipart()
                msg['From'] = self.smtp_config['EMAIL_USER']
                
                # Destination
                if test_mode:
                    msg['To'] = "matt@mattkonnect.com"  # Test vers matt@mattkonnect.com
                    msg['Subject'] = f"[TEST] Opportunité de développement pour {contact['nom_association'][:30]}..."
                else:
                    msg['To'] = contact['email']
                    msg['Subject'] = f"Opportunité de développement pour {contact['nom_association'][:30]}..."
                
                # Corps du message
                msg.attach(MIMEText(email_content, 'plain', 'utf-8'))
                
                # Envoyer
                text = msg.as_string()
                server.sendmail(self.smtp_config['EMAIL_USER'], msg['To'], text)
                
                sent_count += 1
                print(f"  ✅ {i:2d}/{len(contacts_to_send)} - {contact['nom_association'][:40]}... → {msg['To']}")
                
                # Délai entre envois
                time.sleep(2)
                
            except Exception as e:
                error_count += 1
                print(f"  ❌ {i:2d}/{len(contacts_to_send)} - Erreur: {e}")
        
        # Fermer connexion
        server.quit()
        
        # Résumé
        print(f"\n🎉 CAMPAGNE TERMINÉE")
        print(f"✅ Emails envoyés: {sent_count}")
        print(f"❌ Erreurs: {error_count}")
        print(f"📊 Taux de succès: {(sent_count/(sent_count+error_count)*100):.1f}%")
        
        if test_mode:
            print(f"🧪 Mode test - Vérifiez votre boîte email")
        else:
            print(f"🚀 Campagne réelle terminée")

def main():
    """Fonction principale"""
    print(f"📧 RNA CAMPAIGN SENDER")
    print(f"=" * 40)
    print(f"🏛️ Source: RNA Département 01 (Ain)")
    print(f"📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    sender = RNACampaignSender()
    
    print(f"\n📋 OPTIONS DISPONIBLES:")
    print(f"  1. Test (1 email vers soi)")
    print(f"  2. Test limité (3 emails vers soi)")
    print(f"  3. Campagne réelle (tous les contacts)")
    print(f"  4. Quitter")
    
    choice = input(f"\n❓ Votre choix (1-4): ").strip()
    
    if choice == '1':
        sender.send_campaign(test_mode=True, max_emails=1)
    elif choice == '2':
        sender.send_campaign(test_mode=True, max_emails=3)
    elif choice == '3':
        sender.send_campaign(test_mode=False)
    elif choice == '4':
        print("👋 Au revoir!")
    else:
        print("❌ Choix invalide")

if __name__ == "__main__":
    main()
