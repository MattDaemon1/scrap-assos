import requests
from bs4 import BeautifulSoup
import csv
import re
import time
from datetime import datetime
import os
from urllib.parse import urljoin, urlparse
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import *
from utils.data_manager import DataManager

class JournalOfficielScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.data_manager = DataManager()
        
    def scrape_associations(self, department=None, sector_keywords=None, max_pages=5):
        """
        Scrape associations from journal-officiel.gouv.fr
        """
        associations = []
        
        try:
            for page in range(1, max_pages + 1):
                print(f"Scraping page {page}...")
                
                # Construire l'URL avec filtres
                url = f"{JOURNAL_OFFICIEL_URL}/recherche"
                params = {
                    'page': page,
                    'type': 'association'
                }
                
                if department:
                    params['departement'] = department
                    
                response = self.session.get(url, params=params)
                if response.status_code != 200:
                    print(f"Erreur HTTP {response.status_code} pour la page {page}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extraire les associations de la page
                association_items = soup.find_all('div', class_='association-item')
                
                if not association_items:
                    print("Aucune association trouvée sur cette page")
                    break
                
                for item in association_items:
                    association = self.extract_association_data(item, sector_keywords)
                    if association:
                        associations.append(association)
                
                # Pause entre les pages
                time.sleep(2)
                
        except Exception as e:
            print(f"Erreur lors du scraping: {e}")
            
        return associations
    
    def extract_association_data(self, item, sector_keywords=None):
        """
        Extraire les données d'une association
        """
        try:
            # Nom de l'association
            name_elem = item.find('h3') or item.find('h2') or item.find('a')
            name = name_elem.get_text(strip=True) if name_elem else "Nom non trouvé"
            
            # Description/Objet
            desc_elem = item.find('p', class_='description') or item.find('div', class_='objet')
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            # Filtrage par secteur si spécifié
            if sector_keywords:
                found_keyword = False
                full_text = (name + " " + description).lower()
                for keyword in sector_keywords:
                    if keyword.lower() in full_text:
                        found_keyword = True
                        break
                if not found_keyword:
                    return None
            
            # Adresse/Localisation
            address_elem = item.find('div', class_='adresse') or item.find('span', class_='ville')
            address = address_elem.get_text(strip=True) if address_elem else ""
            
            # Département depuis l'adresse
            department = self.extract_department(address)
            
            # Date de création/publication
            date_elem = item.find('span', class_='date') or item.find('div', class_='publication')
            date_str = date_elem.get_text(strip=True) if date_elem else ""
            
            # Email (si présent)
            email = self.extract_email(item.get_text())
            
            # URL de la fiche détaillée
            link_elem = item.find('a')
            detail_url = urljoin(JOURNAL_OFFICIEL_URL, link_elem['href']) if link_elem and link_elem.get('href') else ""
            
            association = {
                'name': name,
                'description': description,
                'address': address,
                'department': department,
                'email': email,
                'date_found': date_str,
                'source_url': detail_url,
                'scraping_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'new'
            }
            
            return association
            
        except Exception as e:
            print(f"Erreur lors de l'extraction: {e}")
            return None
    
    def extract_email(self, text):
        """Extraire l'email du texte"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else ""
    
    def extract_department(self, address):
        """Extraire le département de l'adresse"""
        # Pattern pour code postal français
        postal_pattern = r'\b(\d{5})\b'
        match = re.search(postal_pattern, address)
        if match:
            postal_code = match.group(1)
            return postal_code[:2]  # Les 2 premiers chiffres = département
        return ""
    
    def scrape_detailed_info(self, detail_url):
        """
        Scraper les informations détaillées d'une association
        """
        try:
            response = self.session.get(detail_url)
            if response.status_code != 200:
                return {}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            details = {}
            
            # Rechercher plus d'emails
            all_text = soup.get_text()
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', all_text)
            if emails:
                details['emails'] = list(set(emails))
            
            # Rechercher des URLs de sites web
            links = soup.find_all('a', href=True)
            websites = []
            for link in links:
                href = link['href']
                if any(domain in href for domain in ['.fr', '.com', '.org', '.net']):
                    if not any(social in href for social in ['facebook', 'twitter', 'linkedin', 'instagram']):
                        websites.append(href)
            
            if websites:
                details['websites'] = list(set(websites))
            
            return details
            
        except Exception as e:
            print(f"Erreur lors du scraping détaillé: {e}")
            return {}

def main():
    scraper = JournalOfficielScraper()
    
    # Scraper par départements prioritaires
    for dept in PRIORITY_REGIONS[:3]:  # Limiter pour les tests
        print(f"\n=== Scraping département {dept} ===")
        associations = scraper.scrape_associations(
            department=dept,
            sector_keywords=TARGET_SECTORS,
            max_pages=2  # Limiter pour les tests
        )
        
        if associations:
            # Sauvegarder les données
            filename = f"associations_{dept}_{datetime.now().strftime('%Y%m%d')}.csv"
            scraper.data_manager.save_to_csv(associations, filename)
            print(f"Sauvegardé {len(associations)} associations dans {filename}")
        else:
            print("Aucune association trouvée")

if __name__ == "__main__":
    main()
