import sys
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from email_manager.campaign_manager import EmailCampaignManager
from config.settings import *

def send_test_email_to_mattkonnect():
    """Envoyer un vrai email de test à matt@mattkonnect.com"""
    
    print("📧 ENVOI EMAIL TEST - MATTKONNECT.COM")
    print("=" * 50)
    
    # Configuration email directe pour le test
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "matthieu@mattkonnect.com"
    sender_password = input("🔑 Entrez votre mot de passe d'application Gmail: ").strip()
    
    if not sender_password:
        print("❌ Mot de passe requis pour l'envoi")
        return False
    
    # Créer l'email de test
    manager = EmailCampaignManager(use_google_sheets=False)
    
    # Données pour MattKonnect
    test_prospect = {
        'Nom': 'MattKonnect - Services Web',
        'Email': 'matt@mattkonnect.com',
        'Secteur_Detecte': 'services numériques',
        'Département': '37'
    }
    
    sender_info = {
        'prenom': 'Matthieu',
        'nom': 'ALLART',
        'telephone': '07.82.90.15.35',
        'email': 'matthieu@mattkonnect.com'
    }
    
    try:
        # Générer le contenu personnalisé
        email_content = manager.personalize_email(1, test_prospect, sender_info)
        
        # Créer le message email
        msg = MIMEMultipart()
        msg['From'] = f"{sender_info['prenom']} {sender_info['nom']} <{sender_email}>"
        msg['To'] = test_prospect['Email']
        msg['Subject'] = email_content['subject']
        
        # Corps du message
        body = email_content['body']
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        print(f"📮 Destinataire: {test_prospect['Email']}")
        print(f"📋 Sujet: {email_content['subject']}")
        print(f"📄 Taille: {len(body)} caractères")
        
        # Demander confirmation
        print(f"\n❓ Voulez-vous vraiment envoyer cet email ? (oui/non): ", end="")
        confirmation = input().strip().lower()
        
        if confirmation not in ['oui', 'o', 'yes', 'y']:
            print("❌ Envoi annulé")
            return False
        
        # Connexion SMTP et envoi
        print(f"\n📤 Connexion au serveur SMTP...")
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Activer le chiffrement
            server.login(sender_email, sender_password)
            
            print(f"✅ Authentification réussie")
            print(f"📬 Envoi en cours...")
            
            # Envoyer l'email
            text = msg.as_string()
            server.sendmail(sender_email, test_prospect['Email'], text)
            
            print(f"✅ EMAIL ENVOYÉ AVEC SUCCÈS!")
            print(f"📧 Destinataire: {test_prospect['Email']}")
            print(f"⏰ Heure: {datetime.now().strftime('%H:%M:%S')}")
            
            # Log de l'envoi
            log_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'destinataire': test_prospect['Email'],
                'sujet': email_content['subject'],
                'expediteur': sender_email,
                'statut': 'ENVOYE_SUCCESS',
                'taille': len(body)
            }
            
            print(f"\n📊 RÉSUMÉ DE L'ENVOI:")
            for key, value in log_data.items():
                print(f"  {key}: {value}")
            
            return True
            
    except smtplib.SMTPAuthenticationError:
        print("❌ Erreur d'authentification - Vérifiez votre mot de passe d'application")
        print("💡 Aide: https://support.google.com/accounts/answer/185833")
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ Erreur SMTP: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()
        return False

def preview_before_send():
    """Prévisualiser l'email avant envoi"""
    
    print("👀 PRÉVISUALISATION EMAIL - MATTKONNECT")
    print("=" * 45)
    
    manager = EmailCampaignManager(use_google_sheets=False)
    
    test_prospect = {
        'Nom': 'MattKonnect - Services Web',
        'Email': 'matt@mattkonnect.com',
        'Secteur_Detecte': 'services numériques',
        'Département': '37'
    }
    
    sender_info = {
        'prenom': 'Matthieu',
        'nom': 'ALLART',
        'telephone': '07.82.90.15.35',
        'email': 'matthieu@mattkonnect.com'
    }
    
    try:
        email_content = manager.personalize_email(1, test_prospect, sender_info)
        
        print(f"📬 DE: {sender_info['prenom']} {sender_info['nom']} <{sender_info['email']}>")
        print(f"📮 VERS: {email_content['recipient']}")
        print(f"📋 SUJET: {email_content['subject']}")
        print(f"📅 DATE: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print()
        print("📄 CORPS DU MESSAGE:")
        print("-" * 60)
        print(email_content['body'])
        print("-" * 60)
        
        print(f"\n📊 STATISTIQUES:")
        print(f"  Mots: {len(email_content['body'].split())}")
        print(f"  Caractères: {len(email_content['body'])}")
        print(f"  Lignes: {len(email_content['body'].split(chr(10)))}")
        
        return email_content
        
    except Exception as e:
        print(f"❌ Erreur de prévisualisation: {e}")
        return None

def main():
    """Menu principal"""
    print("🚀 GESTIONNAIRE EMAIL TEST - MATTKONNECT")
    print("=" * 50)
    
    while True:
        print(f"\n📋 QUE VOULEZ-VOUS FAIRE ?")
        print("1. 👀 Prévisualiser l'email")
        print("2. 📤 Envoyer l'email de test")
        print("3. 🚪 Quitter")
        
        choice = input("Votre choix (1-3): ").strip()
        
        if choice == "1":
            preview_before_send()
            
        elif choice == "2":
            # Prévisualiser d'abord
            email_content = preview_before_send()
            if email_content:
                print(f"\n❓ Confirmez-vous l'envoi de cet email ? (oui/non): ", end="")
                confirm = input().strip().lower()
                if confirm in ['oui', 'o', 'yes', 'y']:
                    success = send_test_email_to_mattkonnect()
                    if success:
                        print(f"\n🎉 Email envoyé avec succès à matt@mattkonnect.com!")
                        break
                else:
                    print("❌ Envoi annulé")
            
        elif choice == "3":
            print("👋 Au revoir!")
            break
            
        else:
            print("❌ Choix invalide")

if __name__ == "__main__":
    main()
