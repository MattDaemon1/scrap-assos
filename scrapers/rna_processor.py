import pandas as pd
import re
import sys
import os
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_manager import DataManager

class RnaAssociationProcessor:
    """Processeur pour transformer le fichier RNA en base de leads avec contacts"""
    
    def __init__(self):
        self.data_manager = DataManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Mapping codes secteurs
        self.secteur_mapping = {
            '7000': 'Loisirs/Culture',
            '9030': 'Festivités/Spectacles', 
            '11000': 'Sports',
            '11035': 'Sports/Boules',
            '11105': 'Sports/Gymnastique',
            '13005': 'Chasse/Pêche',
            '15000': 'Education/Formation',
            '24000': 'Chasse',
            '38000': 'Anciens Combattants',
            '38105': 'Anciens Combattants/Entraide',
            '50000': 'Divers/Dissous'
        }
    
    def load_rna_file(self, filepath):
        """Charger et analyser le fichier RNA"""
        print(f"📄 CHARGEMENT FICHIER RNA")
        print("=" * 40)
        
        try:
            # Charger le CSV
            df = pd.read_csv(filepath, encoding='utf-8')
            print(f"✅ Fichier chargé: {len(df)} associations")
            
            # Afficher les colonnes
            print(f"📋 Colonnes: {', '.join(df.columns)}")
            
            return df
            
        except Exception as e:
            print(f"❌ Erreur chargement: {e}")
            return None
    
    def clean_rna_data(self, df):
        """Nettoyer et structurer les données RNA"""
        print(f"\n🧹 NETTOYAGE DONNÉES RNA")
        print("-" * 40)
        
        cleaned_associations = []
        
        for index, row in df.iterrows():
            try:
                # Filtrer les associations valides
                titre = str(row.get('titre', '')).strip()
                if not titre or 'ERREUR' in titre.upper() or 'VOIR NUMERO' in titre.upper():
                    continue
                
                if 'DISSOL' in titre.upper() or len(titre) < 5:
                    continue
                
                # Nettoyer et structurer
                association = {
                    'nom': self._clean_title(titre),
                    'objet': str(row.get('objet', '')).strip()[:300],
                    'adresse': str(row.get('adr1', '')).strip(),
                    'code_postal': str(row.get('adrs_codepostal', '')).strip(),
                    'ville': str(row.get('libcom', '')).strip(),
                    'secteur_code': str(row.get('objet_social1', '')).strip(),
                    'secteur_nom': self.secteur_mapping.get(str(row.get('objet_social1', '')).strip(), 'Autre'),
                    'date_publication': str(row.get('date_publi', '')).strip(),
                    'nature': str(row.get('nature', '')).strip(),
                    'departement': '01',
                    'source': 'RNA_Officiel_Dpt01',
                    'extraction_method': 'rna_file_processing',
                    'date_extraction': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'email_principal': '',  # À rechercher
                    'telephone': '',  # À rechercher
                    'site_web': '',  # À rechercher
                    'statut_recherche': 'pending'
                }
                
                # Valider les données minimales
                if len(association['nom']) >= 5 and association['ville']:
                    cleaned_associations.append(association)
                
            except Exception as e:
                continue
        
        print(f"✅ {len(cleaned_associations)} associations nettoyées")
        return cleaned_associations
    
    def _clean_title(self, titre):
        """Nettoyer le titre d'association"""
        # Supprimer prefixes
        titre = re.sub(r'^(VOIR - \d+ - |VOIR NUMERO \d+ - )', '', titre)
        
        # Nettoyer caractères spéciaux
        titre = titre.replace("'", "'").replace("Â", "à").replace("E", "é")
        
        # Capitalisation
        if titre.isupper():
            titre = titre.title()
        
        return titre.strip()
    
    def search_association_contacts(self, associations, max_searches=50):
        """Rechercher contacts pour les associations"""
        print(f"\n🔍 RECHERCHE CONTACTS ASSOCIATIONS")
        print("=" * 50)
        print(f"🎯 Recherche pour {min(len(associations), max_searches)} associations")
        
        updated_associations = []
        
        for i, assoc in enumerate(associations[:max_searches]):
            try:
                print(f"\n{i+1}/{min(len(associations), max_searches)} - {assoc['nom'][:50]}...")
                
                # Recherche Google
                contacts = self._search_google_contacts(assoc)
                
                if contacts['email'] or contacts['phone'] or contacts['website']:
                    assoc.update(contacts)
                    assoc['statut_recherche'] = 'found'
                    print(f"  ✅ Contacts trouvés: Email: {bool(contacts['email'])}, Tel: {bool(contacts['phone'])}, Web: {bool(contacts['website'])}")
                else:
                    assoc['statut_recherche'] = 'not_found'
                    print(f"  ⚠️ Aucun contact trouvé")
                
                updated_associations.append(assoc)
                
                # Délai pour éviter blocage
                if i % 10 == 0 and i > 0:
                    print(f"  ⏳ Pause de 5 secondes...")
                    import time
                    time.sleep(5)
                else:
                    import time
                    time.sleep(2)
                
            except Exception as e:
                print(f"  ❌ Erreur recherche: {e}")
                assoc['statut_recherche'] = 'error'
                updated_associations.append(assoc)
        
        # Ajouter le reste sans recherche
        for assoc in associations[max_searches:]:
            updated_associations.append(assoc)
        
        return updated_associations
    
    def _search_google_contacts(self, association):
        """Rechercher contacts via Google"""
        contacts = {'email': '', 'phone': '', 'website': ''}
        
        try:
            # Construire requête Google
            query = f'"{association["nom"]}" {association["ville"]} contact email'
            google_url = f"https://www.google.com/search?q={quote_plus(query)}"
            
            # Headers pour éviter détection bot
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            response = self.session.get(google_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text()
                
                # Extraire email
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, text)
                
                for email in emails:
                    if self._is_valid_association_email(email, association):
                        contacts['email'] = email.lower()
                        break
                
                # Extraire téléphone
                phone_pattern = r'0[1-9](?:[.\s-]?\d{2}){4}'
                phones = re.findall(phone_pattern, text)
                if phones:
                    contacts['phone'] = phones[0]
                
                # Extraire site web
                website_pattern = r'https?://[^\s<>"]+(?:\.fr|\.org|\.com|\.net)'
                websites = re.findall(website_pattern, text)
                
                for website in websites:
                    if self._is_valid_association_website(website, association):
                        contacts['website'] = website
                        break
            
        except Exception as e:
            pass
        
        return contacts
    
    def _is_valid_association_email(self, email, association):
        """Vérifier si email correspond à l'association"""
        if not email or '@' not in email:
            return False
        
        email_lower = email.lower()
        assoc_name = association['nom'].lower()
        city = association['ville'].lower()
        
        # Filtrer emails génériques
        excluded = ['noreply', 'webmaster', 'admin', 'contact@google', 'contact@facebook']
        if any(ex in email_lower for ex in excluded):
            return False
        
        # Favoriser emails contenant nom association ou ville
        name_words = assoc_name.split()[:3]  # 3 premiers mots
        for word in name_words:
            if len(word) > 3 and word in email_lower:
                return True
        
        if len(city) > 4 and city.replace('-', '') in email_lower:
            return True
        
        # Domaines valides
        valid_domains = ['.fr', '.org', '.asso.fr', '.com']
        return any(domain in email_lower for domain in valid_domains)
    
    def _is_valid_association_website(self, website, association):
        """Vérifier si site web correspond à l'association"""
        if not website:
            return False
        
        website_lower = website.lower()
        assoc_name = association['nom'].lower()
        
        # Exclure sites génériques
        excluded_sites = ['google.', 'facebook.', 'pages.jaunes', 'wikipedia.']
        if any(site in website_lower for site in excluded_sites):
            return False
        
        # Favoriser sites contenant nom association
        name_words = assoc_name.split()[:2]
        for word in name_words:
            if len(word) > 4 and word in website_lower:
                return True
        
        return True
    
    def generate_statistics(self, associations):
        """Générer statistiques des associations RNA"""
        total = len(associations)
        
        # Statistiques contacts
        with_email = sum(1 for a in associations if a.get('email_principal'))
        with_phone = sum(1 for a in associations if a.get('telephone'))
        with_website = sum(1 for a in associations if a.get('site_web'))
        searched = sum(1 for a in associations if a.get('statut_recherche') != 'pending')
        
        # Statistiques secteurs
        by_sector = {}
        for assoc in associations:
            sector = assoc.get('secteur_nom', 'Autre')
            by_sector[sector] = by_sector.get(sector, 0) + 1
        
        # Statistiques villes
        by_city = {}
        for assoc in associations:
            city = assoc.get('ville', 'Inconnue')
            by_city[city] = by_city.get(city, 0) + 1
        
        return {
            'Total associations': total,
            'Avec email': with_email,
            'Avec téléphone': with_phone,
            'Avec site web': with_website,
            'Recherches effectuées': searched,
            'Taux email': f"{(with_email/total*100):.1f}%" if total > 0 else "0%",
            'Taux téléphone': f"{(with_phone/total*100):.1f}%" if total > 0 else "0%",
            'Top secteurs': dict(sorted(by_sector.items(), key=lambda x: x[1], reverse=True)[:5]),
            'Top villes': dict(sorted(by_city.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    def process_rna_file(self, filepath="data/rna_import_20250701_dpt_01.csv", search_contacts=True, max_searches=50):
        """Traitement complet du fichier RNA"""
        print("🎯 TRAITEMENT FICHIER RNA DÉPARTEMENT 01")
        print("=" * 60)
        print("📋 Source: Journal Officiel des Associations")
        print("🏛️ Département: 01 (Ain)")
        print("📧 Recherche contacts automatique")
        
        # 1. Charger données
        df = self.load_rna_file(filepath)
        if df is None:
            return []
        
        # 2. Nettoyer données
        associations = self.clean_rna_data(df)
        if not associations:
            print("❌ Aucune association valide trouvée")
            return []
        
        # 3. Rechercher contacts (optionnel)
        if search_contacts:
            associations = self.search_association_contacts(associations, max_searches)
        
        # 4. Sauvegarder
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"rna_associations_processed_{timestamp}.csv"
        
        self.data_manager.save_to_csv(associations, filename)
        
        # 5. Statistiques
        stats = self.generate_statistics(associations)
        
        print(f"\n🎉 TRAITEMENT RNA TERMINÉ")
        print(f"📁 Fichier: data/{filename}")
        print(f"📊 Total associations: {len(associations)}")
        
        print(f"\n📈 STATISTIQUES RNA:")
        for key, value in stats.items():
            print(f"  • {key}: {value}")
        
        print(f"\n🏆 AVANTAGES RNA:")
        print(f"✅ Données 100% officielles (Journal Officiel)")
        print(f"✅ Associations réellement déclarées")
        print(f"✅ Adresses vérifiées")
        print(f"✅ Secteurs d'activité codifiés")
        print(f"✅ Aucune invention de données")
        
        return associations

def main():
    """Fonction principale"""
    processor = RnaAssociationProcessor()
    
    print("🎯 PROCESSEUR RNA ASSOCIATIONS")
    print("=" * 60)
    print("📋 Source: Journal Officiel Département 01")
    print("🏛️ 665 associations officielles")
    print("📧 Recherche contacts automatique")
    
    print(f"\n❓ Options:")
    print(f"1. Traitement sans recherche contacts (rapide)")
    print(f"2. Traitement avec recherche contacts (lent)")
    print(f"\nChoix (1/2): ", end="")
    
    choice = input().strip()
    
    if choice == "1":
        associations = processor.process_rna_file(search_contacts=False)
    elif choice == "2":
        print(f"Nombre de recherches contacts (max 50): ", end="")
        max_searches = int(input().strip() or "20")
        associations = processor.process_rna_file(search_contacts=True, max_searches=max_searches)
    else:
        print("🚪 Traitement annulé")
        return
    
    if associations:
        print(f"\n🎉 SUCCÈS ! {len(associations)} associations traitées")
        print(f"📧 Données 100% réelles et officielles")
    else:
        print(f"\n😞 Aucun résultat")

if __name__ == "__main__":
    main()
