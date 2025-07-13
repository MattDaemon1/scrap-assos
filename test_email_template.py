#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST EMAIL SIMPLE - Template personnalisé
========================================
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import configparser
import os

def load_sender_config():
    """Charger la configuration SMTP"""
    config = configparser.ConfigParser()
    config_path = "config/sender_config.txt"
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Fichier de configuration non trouvé: {config_path}")
    
    config.read(config_path, encoding='utf-8')
    
    sender_info = {
        'prenom': config.get('SENDER_INFO', 'prenom'),
        'nom': config.get('SENDER_INFO', 'nom'),
        'telephone': config.get('SENDER_INFO', 'telephone'),
        'email': config.get('SENDER_INFO', 'email')
    }
    
    smtp_config = {
        'server': config.get('EMAIL_SMTP', 'smtp_server'),
        'port': config.getint('EMAIL_SMTP', 'smtp_port'),
        'password': config.get('EMAIL_SMTP', 'email_password'),
        'use_ssl': config.getboolean('EMAIL_SMTP', 'use_ssl')
    }
    
    return sender_info, smtp_config

def load_template(template_file):
    """Charger le template email"""
    with open(template_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extraire l'objet
    lines = content.split('\n')
    subject = "Test Email"  # Par défaut
    body_start = 0
    
    for i, line in enumerate(lines):
        if line.startswith('Objet:') or line.startswith('Objet :'):
            subject = line.replace('Objet:', '').replace('Objet :', '').strip()
            body_start = i + 1
            break
    
    # Corps de l'email (après l'objet)
    body_lines = lines[body_start:]
    # Supprimer les lignes vides au début
    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)
    
    body = '\n'.join(body_lines)
    
    return subject, body

def send_test_email():
    """Envoyer email de test avec template personnalisé"""
    
    print("📧 TEST EMAIL AVEC TEMPLATE PERSONNALISÉ")
    print("=" * 50)
    
    try:
        # Charger configuration
        print("🔧 Chargement configuration...")
        sender_info, smtp_config = load_sender_config()
        
        print(f"✅ Configuration chargée:")
        print(f"   Expéditeur: {sender_info['prenom']} {sender_info['nom']}")
        print(f"   Email: {sender_info['email']}")
        print(f"   Serveur: {smtp_config['server']}:{smtp_config['port']}")
        
        # Charger template
        print("📝 Chargement template...")
        subject_template, body_template = load_template("templates/email_template_1.txt")
        
        # Données de test pour personnalisation
        test_data = {
            'nom_association': 'Association Test',
            'prenom_contact': 'Matthieu',
            'secteur_detecte': 'développement web',
            'departement': 'département du Rhône',
            'telephone': sender_info['telephone'],
            'prenom': sender_info['prenom'],
            'nom': sender_info['nom'],
            'email': sender_info['email']
        }
        
        # Personnaliser le contenu (remplacer les variables {{}} par {})
        subject_clean = subject_template.replace('{{', '{').replace('}}', '}')
        body_clean = body_template.replace('{{', '{').replace('}}', '}')
        
        try:
            subject = subject_clean.format(**test_data)
            body = body_clean.format(**test_data)
        except KeyError as e:
            print(f"⚠️  Variable manquante: {e}")
            # Utiliser les templates sans personnalisation si erreur
            subject = subject_template
            body = body_template
        
        # Prévisualisation
        print(f"\n👀 PRÉVISUALISATION:")
        print(f"📮 Destinataire: matt@mattkonnect.com")
        print(f"📋 Sujet: {subject}")
        print(f"📄 Taille: {len(body)} caractères")
        print(f"📖 Début: {body[:100]}...")
        
        # Confirmation
        print(f"\n❓ CONFIRMATION")
        confirm = input(f"Envoyer cet email à matt@mattkonnect.com ? (oui/non): ").strip().lower()
        
        if confirm not in ['oui', 'o', 'yes', 'y']:
            print("❌ Envoi annulé")
            return False
        
        # Créer message
        print(f"\n📤 Préparation email...")
        msg = MIMEMultipart()
        msg['From'] = f"{sender_info['prenom']} {sender_info['nom']} <{sender_info['email']}>"
        msg['To'] = "matt@mattkonnect.com"
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Connexion SMTP
        print(f"🔗 Connexion SMTP...")
        
        if smtp_config['use_ssl']:
            server = smtplib.SMTP_SSL(smtp_config['server'], smtp_config['port'])
        else:
            server = smtplib.SMTP(smtp_config['server'], smtp_config['port'])
            server.starttls()
        
        print(f"🔑 Authentification...")
        server.login(sender_info['email'], smtp_config['password'])
        
        print(f"📬 Envoi...")
        server.send_message(msg)
        server.quit()
        
        # Succès
        print(f"\n🎉 EMAIL ENVOYÉ AVEC SUCCÈS!")
        print(f"📧 Destinataire: matt@mattkonnect.com")
        print(f"📋 Sujet: {subject}")
        print(f"⏰ Heure: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Fonction principale"""
    print(f"📧 TEST EMAIL TEMPLATE PERSONNALISÉ")
    print(f"📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"📁 Template: templates/email_template_1.txt")
    
    success = send_test_email()
    
    if success:
        print(f"\n✅ Test terminé avec succès!")
        print(f"📬 Vérifiez matt@mattkonnect.com")
    else:
        print(f"\n❌ Test échoué")

if __name__ == "__main__":
    main()
