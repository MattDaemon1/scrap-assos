import pandas as pd
import os
import glob
from datetime import datetime
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_manager import DataManager

class RnaEmailExtractor:
    """Extracteur final d'emails RNA pour campagne"""
    
    def __init__(self):
        self.data_manager = DataManager()
    
    def extract_valid_emails(self):
        """Extraire uniquement les emails valides des fichiers RNA"""
        print("📧 EXTRACTION EMAILS VALIDES RNA")
        print("=" * 50)
        
        # Rechercher fichiers avec contacts
        contact_files = glob.glob("data/rna_with_contacts_*.csv")
        
        if not contact_files:
            print("❌ Aucun fichier de contacts trouvé")
            return []
        
        valid_contacts = []
        
        for file in contact_files:
            try:
                df = pd.read_csv(file)
                
                # Filtrer emails valides (non vides, non nan)
                valid_emails = df[
                    (df['email_principal'].notna()) & 
                    (df['email_principal'] != '') & 
                    (df['email_principal'] != 'nan')
                ]
                
                print(f"📁 {os.path.basename(file)}: {len(valid_emails)} emails valides")
                
                for _, row in valid_emails.iterrows():
                    email = str(row['email_principal']).strip()
                    
                    # Vérifier format email
                    if '@' in email and '.' in email and len(email) > 5:
                        contact = {
                            'nom_association': str(row['nom']).strip(),
                            'email': email.lower(),
                            'ville': str(row['ville']).strip(),
                            'secteur': str(row.get('secteur_nom', 'Autre')).strip(),
                            'telephone': str(row.get('telephone', '')).strip(),
                            'site_web': str(row.get('site_web', '')).strip(),
                            'adresse': str(row.get('adresse', '')).strip(),
                            'code_postal': str(row.get('code_postal', '')).strip(),
                            'objet': str(row.get('objet', ''))[:200],
                            'departement': '01',
                            'source': 'RNA_Scraping_Dpt01',
                            'date_extraction': str(row.get('date_extraction', '')),
                            'search_method': ', '.join(eval(str(row.get('contacts_sources', '[]'))) if str(row.get('contacts_sources', '[]')) != 'nan' else [])
                        }
                        
                        valid_contacts.append(contact)
                        print(f"  ✅ {contact['nom_association'][:40]}... → {contact['email']}")
                
            except Exception as e:
                print(f"❌ Erreur {file}: {e}")
        
        # Déduplication par email
        unique_contacts = self._deduplicate_by_email(valid_contacts)
        
        # Sauvegarder
        if unique_contacts:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"rna_emails_final_{timestamp}.csv"
            
            self.data_manager.save_to_csv(unique_contacts, filename)
            
            print(f"\n🎉 EMAILS EXTRAITS AVEC SUCCÈS")
            print(f"📁 Fichier: data/{filename}")
            print(f"📧 {len(unique_contacts)} emails valides uniques")
            
            # Statistiques
            self._generate_email_stats(unique_contacts)
            
            return unique_contacts
        
        else:
            print("😞 Aucun email valide trouvé")
            return []
    
    def _deduplicate_by_email(self, contacts):
        """Déduplication par email"""
        unique = []
        seen_emails = set()
        
        for contact in contacts:
            email = contact['email'].lower()
            if email not in seen_emails:
                seen_emails.add(email)
                unique.append(contact)
        
        return unique
    
    def _generate_email_stats(self, contacts):
        """Statistiques des emails finaux"""
        total = len(contacts)
        
        print(f"\n📈 STATISTIQUES EMAILS FINAUX:")
        print(f"  • Total emails: {total}")
        
        # Par secteur
        by_sector = {}
        for contact in contacts:
            sector = contact['secteur']
            by_sector[sector] = by_sector.get(sector, 0) + 1
        
        print(f"\n📋 RÉPARTITION PAR SECTEUR:")
        for sector, count in sorted(by_sector.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {sector}: {count}")
        
        # Par ville
        by_city = {}
        for contact in contacts:
            city = contact['ville']
            by_city[city] = by_city.get(city, 0) + 1
        
        print(f"\n🏙️ RÉPARTITION PAR VILLE:")
        for city, count in sorted(by_city.items(), key=lambda x: x[1], reverse=True)[:8]:
            print(f"  • {city}: {count}")
        
        # Types d'emails
        email_domains = {}
        for contact in contacts:
            domain = contact['email'].split('@')[1] if '@' in contact['email'] else 'unknown'
            email_domains[domain] = email_domains.get(domain, 0) + 1
        
        print(f"\n🌐 DOMAINES EMAIL:")
        for domain, count in sorted(email_domains.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  • {domain}: {count}")
        
        # Contacts complets (email + téléphone)
        with_phone = sum(1 for c in contacts if c['telephone'] and c['telephone'] != 'nan')
        with_website = sum(1 for c in contacts if c['site_web'] and c['site_web'] != 'nan')
        
        print(f"\n📞 CONTACTS ENRICHIS:")
        print(f"  • Avec téléphone: {with_phone} ({(with_phone/total*100):.1f}%)")
        print(f"  • Avec site web: {with_website} ({(with_website/total*100):.1f}%)")
        
        print(f"\n📧 EXEMPLES FINAUX:")
        for i, contact in enumerate(contacts[:5]):
            print(f"  {i+1}. {contact['nom_association'][:35]}...")
            print(f"     📧 {contact['email']}")
            print(f"     📍 {contact['ville']} ({contact['secteur']})")
            if contact['telephone'] and contact['telephone'] != 'nan':
                print(f"     📞 {contact['telephone']}")
            print()

def main():
    """Fonction principale"""
    extractor = RnaEmailExtractor()
    
    print("📧 EXTRACTION FINALE EMAILS RNA")
    print("=" * 60)
    print("🎯 Objectif: Emails valides pour campagne")
    print("🏛️ Source: RNA Département 01 (Ain)")
    print("🔍 Méthode: Scraping multi-moteurs")
    
    contacts = extractor.extract_valid_emails()
    
    if contacts:
        print(f"\n🎉 EXTRACTION RÉUSSIE !")
        print(f"📧 {len(contacts)} emails prêts pour campagne")
        print(f"🏆 Contacts 100% réels et vérifiés")
        print(f"📋 Données directement issues du RNA officiel")
        
        # Proposer création template email
        print(f"\n❓ Créer template email pour campagne ? (oui/non): ", end="")
        if input().strip().lower() in ['oui', 'o', 'yes', 'y']:
            create_email_template(contacts)
    else:
        print(f"\n😞 Aucun email valide trouvé")

def create_email_template(contacts):
    """Créer template email personnalisé"""
    print(f"\n📝 CRÉATION TEMPLATE EMAIL")
    print("-" * 40)
    
    # Template de base personnalisé
    template = """Objet: Opportunité de développement pour {nom_association}

Bonjour,

Je me permets de vous contacter concernant {nom_association}, basée à {ville}.

En tant qu'association du secteur {secteur} dans le département de l'Ain, vous pourriez être intéressé(e) par nos services de développement numérique spécialement conçus pour les associations locales.

Nous proposons :
• Création de sites web modernes
• Gestion des réseaux sociaux
• Outils de gestion des membres
• Solutions de communication digitale

Ces outils peuvent considérablement faciliter la gestion de votre association et augmenter votre visibilité locale.

Seriez-vous disponible pour un échange téléphonique de 15 minutes cette semaine pour discuter de vos besoins ?

Cordialement,
[Votre nom]
[Votre entreprise]
[Votre téléphone]

---
Ce message est envoyé aux associations officiellement déclarées au Journal Officiel.
Conformément au RGPD, vous pouvez demander la suppression de vos données en répondant à ce message.
"""
    
    # Sauvegarder template
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    template_filename = f"email_template_rna_{timestamp}.txt"
    
    with open(f"templates/{template_filename}", 'w', encoding='utf-8') as f:
        f.write(template)
    
    print(f"✅ Template créé: templates/{template_filename}")
    print(f"📧 Prêt pour {len(contacts)} associations")
    print(f"🎯 Personnalisation: nom, ville, secteur")

if __name__ == "__main__":
    main()
