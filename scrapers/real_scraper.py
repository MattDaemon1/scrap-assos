import requests
from bs4 import BeautifulSoup
import csv
import re
import time
from datetime import datetime
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import TARGET_DEPARTMENTS, TARGET_SECTORS, MIN_BUDGET, MAX_BUDGET
from utils.data_manager import DataManager

class RealAssociationScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.data_manager = DataManager()
        
    def scrape_hello_asso(self, department, max_pages=3):
        """Scraper HelloAsso pour trouver de vraies associations"""
        associations = []
        
        try:
            for page in range(1, max_pages + 1):
                print(f"  Scraping HelloAsso page {page}...")
                
                # URL de recherche HelloAsso avec géolocalisation
                url = "https://www.helloasso.com/associations/recherche"
                params = {
                    'page': page,
                    'location': f"département {department}",
                    'q': 'culture formation caritatif'  # Mots-clés ciblés
                }
                
                response = self.session.get(url, params=params, timeout=10)
                if response.status_code != 200:
                    print(f"    Erreur HTTP {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extraire les associations
                assoc_cards = soup.find_all(['div', 'article'], class_=re.compile(r'association|card|result'))
                
                if not assoc_cards:
                    print(f"    Aucune association trouvée (structure HTML changée)")
                    break
                
                for card in assoc_cards:
                    association = self.extract_association_from_helloasso(card, department)
                    if association:
                        associations.append(association)
                
                time.sleep(2)  # Respecter le site
                
        except Exception as e:
            print(f"  Erreur HelloAsso: {e}")
        
        return associations
    
    def scrape_data_gouv_associations(self, department, max_results=50):
        """Scraper l'API officielle data.gouv.fr des associations"""
        associations = []
        
        try:
            print(f"  Scraping API data.gouv.fr...")
            
            # API officielle des associations
            url = "https://entreprise.data.gouv.fr/api/sirene/v3/etablissements"
            params = {
                'code_postal': f"{department}*",
                'activite_principale': '94.99Z',  # Autres organisations fonctionnant par adhésion volontaire
                'per_page': max_results,
                'cursor': '*'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                
                for etablissement in data.get('etablissements', [])[:max_results]:
                    association = self.extract_association_from_sirene(etablissement)
                    if association:
                        associations.append(association)
            else:
                print(f"    API indisponible: {response.status_code}")
                
        except Exception as e:
            print(f"  Erreur API SIRENE: {e}")
        
        return associations
    
    def scrape_journal_officiel_real(self, department, max_pages=2):
        """Scraper le vrai Journal Officiel avec des patterns réels"""
        associations = []
        
        try:
            print(f"  Scraping Journal Officiel...")
            
            # Différentes URLs possibles du Journal Officiel
            base_urls = [
                "https://www.journal-officiel.gouv.fr/pages/associations-detail",
                "https://www.data.gouv.fr/fr/datasets/repertoire-national-des-associations",
                "https://www.service-public.fr/associations/vosdroits/N31931"
            ]
            
            for url in base_urls:
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Chercher des patterns d'associations
                        text_content = soup.get_text()
                        emails_found = self.extract_emails_from_text(text_content)
                        
                        for email in emails_found[:5]:  # Max 5 par source
                            association = {
                                'nom': self.generate_name_from_email(email),
                                'email': email,
                                'departement': department,
                                'source': 'journal_officiel',
                                'secteur': self.guess_sector_from_email(email),
                                'date_found': datetime.now().strftime('%Y-%m-%d')
                            }
                            associations.append(association)
                        
                        if emails_found:
                            break  # Arrêter si on a trouvé des emails
                            
                except Exception as e:
                    print(f"    Erreur URL {url}: {e}")
                    continue
                    
        except Exception as e:
            print(f"  Erreur Journal Officiel: {e}")
        
        return associations
    
    def extract_association_from_helloasso(self, card, department):
        """Extraire une association depuis HelloAsso"""
        try:
            # Nom de l'association
            name_elem = card.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'title|name|association'))
            if not name_elem:
                name_elem = card.find('a')
            
            name = name_elem.get_text(strip=True) if name_elem else None
            if not name or len(name) < 3:
                return None
            
            # Description
            desc_elem = card.find(['p', 'div'], class_=re.compile(r'description|summary|excerpt'))
            description = desc_elem.get_text(strip=True)[:200] if desc_elem else ""
            
            # URL de la page de l'association
            link_elem = card.find('a', href=True)
            url = link_elem['href'] if link_elem else ""
            if url and not url.startswith('http'):
                url = 'https://www.helloasso.com' + url
            
            # Extraire plus d'infos depuis la page de l'association
            email, phone, address = self.get_detailed_info_from_url(url) if url else ("", "", "")
            
            association = {
                'nom': name,
                'description': description,
                'email': email,
                'telephone': phone,
                'adresse': address or f"Département {department}",
                'departement': department,
                'site_web': url,
                'secteur': self.detect_sector_from_text(name + " " + description),
                'source': 'helloasso',
                'date_found': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'nouveau'
            }
            
            return association
            
        except Exception as e:
            print(f"    Erreur extraction HelloAsso: {e}")
            return None
    
    def extract_association_from_sirene(self, etablissement):
        """Extraire une association depuis l'API SIRENE"""
        try:
            unite_legale = etablissement.get('unite_legale', {})
            adresse = etablissement.get('adresse', {})
            
            nom = unite_legale.get('denomination', '').strip()
            if not nom or len(nom) < 3:
                return None
            
            # Construire l'adresse
            numero = adresse.get('numero_voie', '')
            type_voie = adresse.get('type_voie', '')
            libelle_voie = adresse.get('libelle_voie', '')
            code_postal = adresse.get('code_postal', '')
            commune = adresse.get('libelle_commune', '')
            
            adresse_complete = f"{numero} {type_voie} {libelle_voie}, {code_postal} {commune}".strip()
            
            # Département depuis le code postal
            departement = code_postal[:2] if len(code_postal) >= 2 else ''
            
            association = {
                'nom': nom,
                'description': f"Association {unite_legale.get('activite_principale_libelle', '')}",
                'email': '',  # À chercher via d'autres moyens
                'telephone': '',
                'adresse': adresse_complete,
                'departement': departement,
                'site_web': '',
                'secteur': self.detect_sector_from_text(nom),
                'source': 'sirene',
                'date_creation': unite_legale.get('date_creation', ''),
                'date_found': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'nouveau'
            }
            
            return association
            
        except Exception as e:
            print(f"    Erreur extraction SIRENE: {e}")
            return None
    
    def get_detailed_info_from_url(self, url):
        """Récupérer les détails depuis l'URL de l'association"""
        try:
            response = self.session.get(url, timeout=8)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                text_content = soup.get_text()
                
                # Extraire email
                emails = self.extract_emails_from_text(text_content)
                email = emails[0] if emails else ""
                
                # Extraire téléphone
                phones = re.findall(r'(\d{2}\.?\d{2}\.?\d{2}\.?\d{2}\.?\d{2})', text_content)
                phone = phones[0] if phones else ""
                
                # Extraire adresse (approximative)
                address_patterns = [
                    r'(\d+[^\\n]*(?:rue|avenue|place|boulevard)[^\\n]*)',
                    r'(\d{5}\s+[A-Z][a-z]+)'
                ]
                address = ""
                for pattern in address_patterns:
                    matches = re.findall(pattern, text_content)
                    if matches:
                        address = matches[0]
                        break
                
                return email, phone, address
                
        except Exception as e:
            print(f"    Erreur détails URL: {e}")
        
        return "", "", ""
    
    def extract_emails_from_text(self, text):
        """Extraire tous les emails d'un texte"""
        if not text:
            return []
        
        email_pattern = r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b'
        emails = re.findall(email_pattern, text)
        
        # Filtrer les emails non pertinents
        filtered_emails = []
        excluded_domains = ['example.com', 'test.com', 'gmail.com', 'outlook.com', 'hotmail.com']
        
        for email in emails:
            domain = email.split('@')[1].lower()
            if domain not in excluded_domains and len(email) > 5:
                filtered_emails.append(email)
        
        return filtered_emails[:5]  # Max 5 emails
    
    def detect_sector_from_text(self, text):
        """Détecter le secteur depuis le texte"""
        if not text:
            return 'autre'
        
        text_lower = text.lower()
        
        sector_keywords = {
            'culture': ['culture', 'art', 'musique', 'théâtre', 'festival', 'concert', 'exposition'],
            'formation': ['formation', 'éducation', 'enseignement', 'cours', 'école', 'apprentissage'],
            'caritatif': ['solidarité', 'aide', 'social', 'caritatif', 'humanitaire', 'bénévole'],
            'sport': ['sport', 'football', 'tennis', 'club', 'équipe', 'compétition'],
            'environnement': ['environnement', 'écologie', 'nature', 'protection', 'vert']
        }
        
        for sector, keywords in sector_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return sector
        
        return 'autre'
    
    def generate_name_from_email(self, email):
        """Générer un nom d'association depuis l'email"""
        if not email or '@' not in email:
            return "Association"
        
        local_part = email.split('@')[0]
        # Nettoyer et capitaliser
        name_parts = re.split(r'[._-]', local_part)
        name = ' '.join(word.capitalize() for word in name_parts if len(word) > 2)
        
        return f"Association {name}" if name else "Association"
    
    def guess_sector_from_email(self, email):
        """Deviner le secteur depuis l'email"""
        if not email:
            return 'autre'
        
        email_lower = email.lower()
        
        if any(word in email_lower for word in ['culture', 'art', 'music', 'festival']):
            return 'culture'
        elif any(word in email_lower for word in ['formation', 'education', 'school', 'cours']):
            return 'formation'
        elif any(word in email_lower for word in ['social', 'aide', 'solidarite', 'help']):
            return 'caritatif'
        else:
            return 'autre'

def main():
    """Fonction principale pour scraper de vraies associations"""
    scraper = RealAssociationScraper()
    data_manager = DataManager()
    
    print("🔍 SCRAPING RÉEL D'ASSOCIATIONS FRANÇAISES")
    print("=" * 50)
    
    all_associations = []
    target_departments = TARGET_DEPARTMENTS[:3]  # Test sur 3 départements
    
    for department in target_departments:
        print(f"\\n=== Département {department} ===")
        
        department_associations = []
        
        # 1. HelloAsso (associations actives)
        print("1. Recherche HelloAsso...")
        try:
            helloasso_results = scraper.scrape_hello_asso(department, max_pages=2)
            department_associations.extend(helloasso_results)
            print(f"   ✅ {len(helloasso_results)} associations HelloAsso")
        except Exception as e:
            print(f"   ❌ Erreur HelloAsso: {e}")
        
        # 2. API SIRENE (données officielles)
        print("2. Recherche API SIRENE...")
        try:
            sirene_results = scraper.scrape_data_gouv_associations(department, max_results=20)
            department_associations.extend(sirene_results)
            print(f"   ✅ {len(sirene_results)} associations SIRENE")
        except Exception as e:
            print(f"   ❌ Erreur SIRENE: {e}")
        
        # 3. Journal Officiel (backup)
        print("3. Recherche Journal Officiel...")
        try:
            jo_results = scraper.scrape_journal_officiel_real(department, max_pages=1)
            department_associations.extend(jo_results)
            print(f"   ✅ {len(jo_results)} associations Journal Officiel")
        except Exception as e:
            print(f"   ❌ Erreur Journal Officiel: {e}")
        
        # Filtrer les doublons par nom
        unique_associations = []
        seen_names = set()
        
        for assoc in department_associations:
            name_key = assoc.get('nom', '').lower().strip()
            if name_key and name_key not in seen_names:
                seen_names.add(name_key)
                unique_associations.append(assoc)
        
        all_associations.extend(unique_associations)
        print(f"   📊 Total unique: {len(unique_associations)}")
        
        time.sleep(3)  # Pause entre départements
    
    print(f"\\n📊 RÉSULTATS TOTAUX")
    print("=" * 30)
    print(f"Total associations: {len(all_associations)}")
    
    if all_associations:
        # Sauvegarder
        data_manager.save_to_csv(all_associations, 'real_associations.csv')
        output_file = os.path.join(data_manager.data_dir, 'real_associations.csv')
        print(f"✅ Sauvegardé: {output_file}")
        
        # Statistiques
        with_email = sum(1 for a in all_associations if a.get('email', '').strip())
        by_source = {}
        by_sector = {}
        
        for assoc in all_associations:
            source = assoc.get('source', 'unknown')
            sector = assoc.get('secteur', 'autre')
            by_source[source] = by_source.get(source, 0) + 1
            by_sector[sector] = by_sector.get(sector, 0) + 1
        
        print(f"\\nAvec email: {with_email}")
        print("\\nPar source:")
        for source, count in by_source.items():
            print(f"  - {source}: {count}")
        print("\\nPar secteur:")
        for sector, count in by_sector.items():
            print(f"  - {sector}: {count}")
        
        print(f"\\n🎯 Prochaine étape: Analyser les sites web existants")
        print("   Commande: python analyzers/website_analyzer_v2.py")
    
    return len(all_associations)

if __name__ == "__main__":
    main()
