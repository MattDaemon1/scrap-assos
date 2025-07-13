import sys
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import configparser

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from email_manager.campaign_manager import EmailCampaignManager

def load_sender_config():
    """Charger la configuration depuis sender_config.txt"""
    config = configparser.ConfigParser()
    config_path = "config/sender_config.txt"
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Fichier de configuration non trouvé: {config_path}")
    
    config.read(config_path, encoding='utf-8')
    
    # Extraire les informations
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

def send_real_email_to_mattkonnect():
    """Envoyer un vrai email de test à matt@mattkonnect.com avec la config chargée"""
    
    print("📧 ENVOI EMAIL RÉEL - MATTKONNECT.COM")
    print("=" * 50)
    
    try:
        # Charger la configuration
        print("🔧 Chargement de la configuration...")
        sender_info, smtp_config = load_sender_config()
        
        print(f"✅ Configuration chargée:")
        print(f"   Expéditeur: {sender_info['prenom']} {sender_info['nom']}")
        print(f"   Email: {sender_info['email']}")
        print(f"   Serveur: {smtp_config['server']}:{smtp_config['port']}")
        print(f"   SSL: {'Oui' if smtp_config['use_ssl'] else 'Non (TLS)'}")
        
        # Créer l'email avec le manager
        manager = EmailCampaignManager(use_google_sheets=False)
        
        # Données pour MattKonnect
        test_prospect = {
            'Nom': 'MattKonnect - Services Web',
            'Email': 'matt@mattkonnect.com',
            'Secteur_Detecte': 'services numériques',
            'Département': '37'
        }
        
        print(f"\n📝 Génération du contenu...")
        email_content = manager.personalize_email(1, test_prospect, sender_info)
        
        # Prévisualisation
        print(f"\n👀 PRÉVISUALISATION:")
        print(f"📮 Vers: {email_content['recipient']}")
        print(f"📋 Sujet: {email_content['subject']}")
        print(f"📄 Taille: {len(email_content['body'])} caractères")
        
        # Afficher le début du message
        preview_lines = email_content['body'].split('\n')[:5]
        print(f"📖 Début: {' '.join(preview_lines)[:100]}...")
        
        # Demander confirmation
        print(f"\n❓ CONFIRMATION")
        print(f"Envoyer cet email à {test_prospect['Email']} ? (oui/non): ", end="")
        confirmation = input().strip().lower()
        
        if confirmation not in ['oui', 'o', 'yes', 'y']:
            print("❌ Envoi annulé par l'utilisateur")
            return False
        
        # Créer le message MIME
        print(f"\n📤 Préparation de l'email...")
        msg = MIMEMultipart()
        msg['From'] = f"{sender_info['prenom']} {sender_info['nom']} <{sender_info['email']}>"
        msg['To'] = test_prospect['Email']
        msg['Subject'] = email_content['subject']
        
        # Ajouter le corps
        msg.attach(MIMEText(email_content['body'], 'plain', 'utf-8'))
        
        # Connexion et envoi
        print(f"🔗 Connexion au serveur SMTP...")
        
        if smtp_config['use_ssl']:
            # Connexion SSL directe (port 465)
            server = smtplib.SMTP_SSL(smtp_config['server'], smtp_config['port'])
        else:
            # Connexion normale puis TLS (port 587)
            server = smtplib.SMTP(smtp_config['server'], smtp_config['port'])
            server.starttls()
        
        print(f"🔑 Authentification...")
        server.login(sender_info['email'], smtp_config['password'])
        
        print(f"📬 Envoi en cours...")
        server.send_message(msg)
        server.quit()
        
        # Succès !
        print(f"\n🎉 EMAIL ENVOYÉ AVEC SUCCÈS!")
        print(f"📧 Destinataire: {test_prospect['Email']}")
        print(f"📋 Sujet: {email_content['subject']}")
        print(f"⏰ Heure d'envoi: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        # Log de l'envoi
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': 'EMAIL_SENT',
            'destinataire': test_prospect['Email'],
            'sujet': email_content['subject'],
            'expediteur': sender_info['email'],
            'serveur': f"{smtp_config['server']}:{smtp_config['port']}",
            'statut': 'SUCCESS'
        }
        
        print(f"\n📊 LOG DÉTAILLÉ:")
        for key, value in log_entry.items():
            print(f"  {key}: {value}")
        
        return True
        
    except configparser.Error as e:
        print(f"❌ Erreur de configuration: {e}")
        print("💡 Vérifiez le fichier config/sender_config.txt")
        return False
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Erreur d'authentification SMTP: {e}")
        print("💡 Vérifiez vos identifiants email dans sender_config.txt")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"❌ Impossible de se connecter au serveur SMTP: {e}")
        print(f"💡 Vérifiez l'adresse du serveur: {smtp_config.get('server', 'N/A')}")
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ Erreur SMTP: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_smtp_connection():
    """Tester uniquement la connexion SMTP"""
    
    print("🔍 TEST DE CONNEXION SMTP")
    print("=" * 30)
    
    try:
        sender_info, smtp_config = load_sender_config()
        
        print(f"🔧 Test de connexion vers {smtp_config['server']}:{smtp_config['port']}")
        
        if smtp_config['use_ssl']:
            server = smtplib.SMTP_SSL(smtp_config['server'], smtp_config['port'])
            print(f"✅ Connexion SSL établie")
        else:
            server = smtplib.SMTP(smtp_config['server'], smtp_config['port'])
            server.starttls()
            print(f"✅ Connexion TLS établie")
        
        print(f"🔑 Test d'authentification...")
        server.login(sender_info['email'], smtp_config['password'])
        print(f"✅ Authentification réussie")
        
        server.quit()
        print(f"✅ Test de connexion SMTP réussi !")
        return True
        
    except Exception as e:
        print(f"❌ Test de connexion échoué: {e}")
        return False

def main():
    """Menu principal"""
    print("🚀 ENVOI EMAIL AVEC CONFIGURATION MATTKONNECT")
    print("=" * 55)
    
    while True:
        print(f"\n📋 OPTIONS DISPONIBLES:")
        print("1. 🔍 Tester la connexion SMTP")
        print("2. 📧 Envoyer l'email de test à matt@mattkonnect.com")
        print("3. 👀 Prévisualiser l'email sans envoyer")
        print("4. 🚪 Quitter")
        
        choice = input("\nVotre choix (1-4): ").strip()
        
        if choice == "1":
            print(f"\n" + "="*40)
            test_smtp_connection()
            
        elif choice == "2":
            print(f"\n" + "="*40)
            success = send_real_email_to_mattkonnect()
            if success:
                print(f"\n🎯 Email envoyé ! Vérifiez la boîte de matt@mattkonnect.com")
                break
            
        elif choice == "3":
            print(f"\n" + "="*40)
            try:
                sender_info, _ = load_sender_config()
                manager = EmailCampaignManager(use_google_sheets=False)
                
                test_prospect = {
                    'Nom': 'MattKonnect - Services Web',
                    'Email': 'matt@mattkonnect.com',
                    'Secteur_Detecte': 'services numériques',
                    'Département': '37'
                }
                
                email_content = manager.personalize_email(1, test_prospect, sender_info)
                
                print("👀 PRÉVISUALISATION COMPLÈTE:")
                print(f"📮 Vers: {email_content['recipient']}")
                print(f"📋 Sujet: {email_content['subject']}")
                print(f"\n📄 Corps du message:")
                print("-" * 50)
                print(email_content['body'])
                print("-" * 50)
                
            except Exception as e:
                print(f"❌ Erreur de prévisualisation: {e}")
            
        elif choice == "4":
            print("👋 Au revoir !")
            break
            
        else:
            print("❌ Choix invalide. Utilisez 1, 2, 3 ou 4.")

if __name__ == "__main__":
    main()
