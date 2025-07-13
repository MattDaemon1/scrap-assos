import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from email_manager.campaign_manager import EmailCampaignManager
from config.settings import *
from datetime import datetime

def test_send_email_to_mattkonnect():
    """Envoyer un email de test à matt@mattkonnect.com"""
    
    print("🚀 TEST D'ENVOI EMAIL - MATTKONNECT")
    print("=" * 50)
    
    # Initialiser le manager
    manager = EmailCampaignManager(use_google_sheets=False)
    
    # Données de test pour MattKonnect
    test_prospect = {
        'name': 'MattKonnect - Services Web',
        'email': 'matt@mattkonnect.com',
        'sector': 'services numériques',
        'department': '37',  # Indre-et-Loire
        'Nom': 'MattKonnect - Services Web',
        'Email': 'matt@mattkonnect.com',
        'Secteur_Detecte': 'services numériques',
        'Département': '37'
    }
    
    # Informations de l'expéditeur (vos vraies informations)
    sender_info = {
        'prenom': EMAIL_SENDER_NAME.split()[0] if EMAIL_SENDER_NAME else 'Matthieu',
        'nom': EMAIL_SENDER_NAME.split()[-1] if EMAIL_SENDER_NAME else 'ALLART',
        'telephone': '07.82.90.15.35',
        'email': EMAIL_SENDER_EMAIL or 'matthieu@mattkonnect.com'
    }
    
    print(f"📧 Destinataire: {test_prospect['email']}")
    print(f"👤 Expéditeur: {sender_info['prenom']} {sender_info['nom']}")
    print(f"📱 Contact: {sender_info['telephone']}")
    
    try:
        # Personnaliser l'email avec le template 1
        email_content = manager.personalize_email(1, test_prospect, sender_info)
        
        print(f"\n📝 CONTENU DE L'EMAIL")
        print("=" * 30)
        print(f"Sujet: {email_content['subject']}")
        print(f"Destinataire: {email_content['recipient']}")
        print(f"\nCorps du message:")
        print("-" * 40)
        print(email_content['body'])
        print("-" * 40)
        
        # Demander confirmation avant l'envoi
        print(f"\n❓ CONFIRMATION")
        print(f"Voulez-vous envoyer cet email de test à {test_prospect['email']} ?")
        print("1. Oui, envoyer l'email")
        print("2. Non, juste prévisualiser")
        
        choice = input("Votre choix (1 ou 2): ").strip()
        
        if choice == "1":
            print(f"\n📤 ENVOI EN COURS...")
            
            # Vérifier la configuration SMTP
            if not EMAIL_SERVER or not EMAIL_PORT:
                print("❌ Configuration SMTP manquante dans config/settings.py")
                print("Veuillez configurer:")
                print("- EMAIL_SERVER (ex: 'smtp.gmail.com')")
                print("- EMAIL_PORT (ex: 587)")
                print("- EMAIL_USERNAME et EMAIL_PASSWORD")
                return False
            
            # Tenter l'envoi (simulation pour le moment)
            print(f"🔧 Configuration SMTP:")
            print(f"  Serveur: {EMAIL_SERVER}:{EMAIL_PORT}")
            print(f"  Utilisateur: {EMAIL_USERNAME}")
            
            # Simuler l'envoi pour éviter les erreurs de config
            print(f"\n✅ EMAIL DE TEST PRÉPARÉ")
            print(f"📧 Pour envoyer réellement, configurez d'abord:")
            print(f"  1. Vos identifiants SMTP dans config/settings.py")
            print(f"  2. Autorisez l'app dans votre compte email")
            
            # Sauvegarder l'email de test
            test_data = {
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'destinataire': test_prospect['email'],
                'sujet': email_content['subject'],
                'expediteur': f"{sender_info['prenom']} {sender_info['nom']}",
                'statut': 'test_prepare'
            }
            
            print(f"\n📊 Email de test préparé avec succès !")
            return True
            
        else:
            print(f"\n👀 Prévisualisation terminée - Aucun email envoyé")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la préparation: {e}")
        return False

def check_email_config():
    """Vérifier la configuration email"""
    print("\n🔍 VÉRIFICATION CONFIGURATION EMAIL")
    print("=" * 40)
    
    config_items = [
        ('EMAIL_SERVER', EMAIL_SERVER),
        ('EMAIL_PORT', EMAIL_PORT),
        ('EMAIL_USERNAME', EMAIL_USERNAME),
        ('EMAIL_PASSWORD', '***' if EMAIL_PASSWORD else None),
        ('EMAIL_SENDER_EMAIL', EMAIL_SENDER_EMAIL),
        ('EMAIL_SENDER_NAME', EMAIL_SENDER_NAME)
    ]
    
    all_configured = True
    
    for name, value in config_items:
        status = "✅" if value else "❌"
        print(f"{status} {name}: {value if name != 'EMAIL_PASSWORD' else ('Configuré' if value else 'Non configuré')}")
        if not value:
            all_configured = False
    
    if not all_configured:
        print(f"\n⚠️ Configuration incomplète")
        print(f"Modifiez le fichier config/settings.py pour ajouter:")
        print(f"- EMAIL_SERVER = 'smtp.gmail.com'  # ou votre serveur SMTP")
        print(f"- EMAIL_PORT = 587")
        print(f"- EMAIL_USERNAME = 'votre.email@gmail.com'")
        print(f"- EMAIL_PASSWORD = 'votre_mot_de_passe_app'")
    else:
        print(f"\n✅ Configuration complète !")
    
    return all_configured

def main():
    """Fonction principale de test"""
    print("🧪 TEST EMAIL - MATTKONNECT.COM")
    print("=" * 50)
    
    # Vérifier la config
    config_ok = check_email_config()
    
    if not config_ok:
        print(f"\n❌ Veuillez d'abord configurer vos paramètres email")
        return
    
    # Lancer le test
    success = test_send_email_to_mattkonnect()
    
    if success:
        print(f"\n🎯 PROCHAINES ÉTAPES:")
        print(f"1. Configurez vos identifiants SMTP réels")
        print(f"2. Testez l'envoi vers votre propre email d'abord")
        print(f"3. Une fois validé, lancez: python email_manager/campaign_manager.py")
    
    return success

if __name__ == "__main__":
    main()
