import pandas as pd
import re
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_manager import DataManager

class EmailCleaner:
    """Nettoyeur d'emails RNA"""
    
    def __init__(self):
        self.data_manager = DataManager()
    
    def clean_email_file(self, filename):
        """Nettoyer fichier d'emails"""
        print("🧹 NETTOYAGE EMAILS RNA")
        print("=" * 40)
        
        try:
            df = pd.read_csv(f"data/{filename}")
            print(f"📁 Fichier: {filename}")
            print(f"📧 Emails bruts: {len(df)}")
            
            # Nettoyer chaque email
            cleaned_emails = []
            
            for _, row in df.iterrows():
                email = str(row['email']).strip().lower()
                
                # Nettoyer email
                clean_email = self._clean_email(email)
                
                if clean_email and self._is_valid_email(clean_email):
                    # Créer contact nettoyé
                    contact = {
                        'nom_association': str(row['nom_association']).strip(),
                        'email': clean_email,
                        'ville': str(row['ville']).strip(),
                        'secteur': str(row['secteur']).strip(),
                        'telephone': self._clean_phone(str(row['telephone'])),
                        'site_web': str(row.get('site_web', '')).strip(),
                        'adresse': str(row.get('adresse', '')).strip(),
                        'code_postal': str(row.get('code_postal', '')).strip(),
                        'objet': str(row.get('objet', ''))[:200],
                        'departement': '01',
                        'source': 'RNA_Cleaned',
                        'date_extraction': datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'search_method': str(row.get('search_method', ''))
                    }
                    
                    cleaned_emails.append(contact)
                    print(f"  ✅ {contact['nom_association'][:35]}... → {contact['email']}")
                else:
                    print(f"  ❌ Email invalide supprimé: {email}")
            
            # Sauvegarder emails nettoyés
            if cleaned_emails:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M')
                clean_filename = f"rna_emails_clean_{timestamp}.csv"
                
                self.data_manager.save_to_csv(cleaned_emails, clean_filename)
                
                print(f"\n🎉 NETTOYAGE TERMINÉ")
                print(f"📁 Fichier propre: data/{clean_filename}")
                print(f"📧 Emails valides: {len(cleaned_emails)}")
                
                # Afficher résumé
                self._display_summary(cleaned_emails)
                
                return clean_filename
            else:
                print("😞 Aucun email valide après nettoyage")
                return None
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return None
    
    def _clean_email(self, email):
        """Nettoyer un email"""
        if not email or email == 'nan':
            return None
        
        # Supprimer texte après email invalide
        if 'orange.frinfonethttps' in email:
            return 'thierco@orange.fr'
        
        if 'mairie-serrieresdebriord.frmanquant' in email:
            return 'contact@mairie-serrieresdebriord.fr'
        
        # Supprimer caractères invalides
        email = re.sub(r'[^\w@.-]', '', email)
        
        # Vérifier format basique
        if '@' not in email or '.' not in email:
            return None
        
        return email.strip().lower()
    
    def _clean_phone(self, phone):
        """Nettoyer numéro de téléphone"""
        if not phone or phone == 'nan':
            return ''
        
        # Supprimer .0 final
        phone = str(phone).replace('.0', '')
        
        # Formater téléphone français
        phone = re.sub(r'[^\d]', '', phone)
        
        if len(phone) == 9:
            phone = '0' + phone
        
        if len(phone) == 10 and phone.startswith('0'):
            return f"{phone[:2]} {phone[2:4]} {phone[4:6]} {phone[6:8]} {phone[8:10]}"
        
        return phone
    
    def _is_valid_email(self, email):
        """Vérifier validité email"""
        if not email:
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _display_summary(self, contacts):
        """Afficher résumé final"""
        print(f"\n📊 RÉSUMÉ FINAL:")
        print(f"  • Total emails valides: {len(contacts)}")
        
        # Domaines
        domains = {}
        for contact in contacts:
            domain = contact['email'].split('@')[1]
            domains[domain] = domains.get(domain, 0) + 1
        
        print(f"\n🌐 DOMAINES:")
        for domain, count in domains.items():
            print(f"  • {domain}: {count}")
        
        print(f"\n📧 EMAILS FINAUX PRÊTS POUR CAMPAGNE:")
        for i, contact in enumerate(contacts, 1):
            print(f"  {i}. {contact['email']} ({contact['nom_association'][:30]}...)")

def main():
    """Fonction principale"""
    cleaner = EmailCleaner()
    
    # Rechercher dernier fichier d'emails
    import glob
    email_files = glob.glob("data/rna_emails_final_*.csv")
    
    if not email_files:
        print("❌ Aucun fichier d'emails trouvé")
        return
    
    # Prendre le plus récent
    latest_file = max(email_files, key=os.path.getctime)
    filename = os.path.basename(latest_file)
    
    print(f"🧹 NETTOYAGE EMAILS RNA")
    print(f"📁 Fichier: {filename}")
    
    clean_filename = cleaner.clean_email_file(filename)
    
    if clean_filename:
        print(f"\n🎯 PRÊT POUR CAMPAGNE EMAIL !")
        print(f"📁 Utiliser: data/{clean_filename}")

if __name__ == "__main__":
    main()
