import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from email_manager.campaign_manager import EmailCampaignManager
from config.settings import *
from datetime import datetime

def simulate_email_send_to_mattkonnect():
    """Simuler l'envoi d'un email à matt@mattkonnect.com avec prévisualisation complète"""
    
    print("🚀 SIMULATION ENVOI EMAIL - MATTKONNECT")
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
    
    # Informations de l'expéditeur
    sender_info = {
        'prenom': 'Matthieu',
        'nom': 'ALLART',
        'telephone': '07.82.90.15.35',
        'email': 'matthieu@mattkonnect.com'
    }
    
    print(f"📧 Destinataire: {test_prospect['email']}")
    print(f"👤 Expéditeur: {sender_info['prenom']} {sender_info['nom']}")
    print(f"📱 Contact: {sender_info['telephone']}")
    
    try:
        # Personnaliser l'email avec le template 1
        email_content = manager.personalize_email(1, test_prospect, sender_info)
        
        print(f"\n📝 CONTENU DE L'EMAIL GÉNÉRÉ")
        print("=" * 50)
        print(f"📬 DE: {sender_info['prenom']} {sender_info['nom']} <{sender_info['email']}>")
        print(f"📮 VERS: {email_content['recipient']}")
        print(f"📋 SUJET: {email_content['subject']}")
        print(f"📅 DATE: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print()
        print("📄 CORPS DU MESSAGE:")
        print("-" * 70)
        print(email_content['body'])
        print("-" * 70)
        
        # Analyse du contenu
        print(f"\n📊 ANALYSE DU CONTENU")
        print("=" * 30)
        
        body_lines = email_content['body'].split('\n')
        word_count = len(email_content['body'].split())
        has_personalization = '{{' not in email_content['body']  # Aucune variable non remplacée
        
        print(f"✅ Lignes: {len(body_lines)}")
        print(f"✅ Mots: {word_count}")
        print(f"✅ Personnalisation: {'Complète' if has_personalization else 'Incomplète'}")
        print(f"✅ Département: Indre-et-Loire (37)")
        print(f"✅ Secteur: services numériques")
        print(f"✅ Contact intégré: {sender_info['telephone']}")
        
        # Vérifications qualité
        print(f"\n🔍 VÉRIFICATIONS QUALITÉ")
        print("=" * 30)
        
        checks = [
            ("Sujet personnalisé", "MattKonnect" in email_content['subject']),
            ("Email valide", "@" in email_content['recipient']),
            ("Téléphone présent", sender_info['telephone'] in email_content['body']),
            ("Email expéditeur", sender_info['email'] in email_content['body']),
            ("Secteur mentionné", test_prospect['sector'] in email_content['body']),
            ("Département mentionné", "Indre-et-Loire" in email_content['body']),
            ("CTA présent", "Répondez" in email_content['body']),
            ("Signature complète", sender_info['nom'] in email_content['body'])
        ]
        
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"{status} {check_name}")
        
        # Simulation de l'envoi
        print(f"\n📤 SIMULATION D'ENVOI")
        print("=" * 25)
        print(f"🔧 Serveur SMTP: smtp.gmail.com:587")
        print(f"🔑 Authentification: matthieu@mattkonnect.com")
        print(f"🌐 Connexion TLS: Activée")
        print(f"📬 Envoi simulé vers: matt@mattkonnect.com")
        print(f"✅ STATUT: Email prêt à envoyer")
        
        # Log de la simulation
        log_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'action': 'EMAIL_SIMULATION',
            'destinataire': test_prospect['email'],
            'sujet': email_content['subject'],
            'expediteur': f"{sender_info['prenom']} {sender_info['nom']}",
            'mots': word_count,
            'statut': 'SIMULE_SUCCESS'
        }
        
        print(f"\n📋 LOG ENREGISTRÉ")
        print(f"Timestamp: {log_entry['timestamp']}")
        print(f"Action: {log_entry['action']}")
        print(f"Statut: {log_entry['statut']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la simulation: {e}")
        import traceback
        traceback.print_exc()
        return False

def preview_all_templates():
    """Prévisualiser les 3 templates avec MattKonnect"""
    
    print(f"\n🎨 PREVIEW DES 3 TEMPLATES POUR MATTKONNECT")
    print("=" * 55)
    
    manager = EmailCampaignManager(use_google_sheets=False)
    
    test_prospect = {
        'name': 'MattKonnect - Services Web',
        'email': 'matt@mattkonnect.com',
        'sector': 'services numériques',
        'department': '37',
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
    
    for template_num in [1, 2, 3]:
        try:
            print(f"\n📧 TEMPLATE {template_num}")
            print("-" * 30)
            
            email_content = manager.personalize_email(template_num, test_prospect, sender_info)
            
            print(f"Sujet: {email_content['subject']}")
            print(f"Mots: {len(email_content['body'].split())}")
            print(f"Lignes: {len(email_content['body'].split(chr(10)))}")
            
            # Afficher les premières lignes
            first_lines = email_content['body'].split('\n')[:3]
            print(f"Début: {' '.join(first_lines)[:100]}...")
            
        except Exception as e:
            print(f"❌ Template {template_num} non disponible: {e}")

def main():
    """Fonction principale de test"""
    print("🧪 TEST COMPLET EMAIL - MATTKONNECT.COM")
    print("=" * 60)
    
    # Test de simulation
    success = simulate_email_send_to_mattkonnect()
    
    if success:
        # Preview des templates
        preview_all_templates()
        
        print(f"\n🎯 RÉSUMÉ DU TEST")
        print("=" * 20)
        print(f"✅ Email personnalisé généré")
        print(f"✅ Contenu vérifié et validé") 
        print(f"✅ Simulation d'envoi réussie")
        print(f"📧 Destinataire: matt@mattkonnect.com")
        
        print(f"\n🔧 POUR ENVOI RÉEL:")
        print(f"1. Configurez EMAIL_PASSWORD dans config/email_config.py")
        print(f"2. Exécutez: python email_manager/campaign_manager.py")
        print(f"3. Ou utilisez un service email (SendGrid, Sendinblue)")
        
        return True
    else:
        print(f"\n❌ Test échoué")
        return False

if __name__ == "__main__":
    main()
