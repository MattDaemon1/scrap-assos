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
from config.settings import TARGET_DEPARTMENTS, TARGET_SECTORS, MIN_BUDGET, MAX_BUDGET
from utils.data_manager import DataManager

class JournalOfficielScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.data_manager = DataManager()
        
    def scrape_associations(self, department=None, sector_keywords=None, max_pages=3):
        """
        Scrape associations - Version de test avec données réalistes
        """
        print(f"Scraping associations pour le département {department}...")
        
        # Pour le moment, générons des données de test réalistes
        associations = self._generate_realistic_test_data(department)
        
        print(f"✅ {len(associations)} associations trouvées pour le département {department}")
        return associations
    
    def _generate_realistic_test_data(self, department):
        """Générer des données de test réalistes basées sur le département"""
        
        # Données de base par département du Centre-Val de Loire
        dept_info = {
            "18": {"ville": "Bourges", "region": "Cher"},
            "28": {"ville": "Chartres", "region": "Eure-et-Loir"},
            "36": {"ville": "Châteauroux", "region": "Indre"},
            "37": {"ville": "Tours", "region": "Indre-et-Loire"},
            "41": {"ville": "Blois", "region": "Loir-et-Cher"},
            "45": {"ville": "Orléans", "region": "Loiret"}
        }
        
        ville_principale = dept_info.get(department, {}).get("ville", "Ville")
        region_nom = dept_info.get(department, {}).get("region", "Région")
        
        # Templates d'associations réalistes
        templates = [
            {
                'nom': f'Association Culturelle de {ville_principale}',
                'secteur': 'culture',
                'description': 'Promotion des arts et de la culture locale, organisation d\'événements culturels',
                'budget_estime': 35000,
                'besoin_site': True,
                'priorite': 8
            },
            {
                'nom': f'Centre de Formation {region_nom}',
                'secteur': 'formation',
                'description': 'Formation professionnelle continue et insertion professionnelle',
                'budget_estime': 65000,
                'besoin_site': True,
                'priorite': 9
            },
            {
                'nom': f'Solidarité et Entraide {ville_principale}',
                'secteur': 'caritatif',
                'description': 'Aide alimentaire et accompagnement social des familles en difficulté',
                'budget_estime': 28000,
                'besoin_site': True,
                'priorite': 7
            },
            {
                'nom': f'Club Sportif {ville_principale}',
                'secteur': 'sport',
                'description': 'Promotion du sport pour tous, encadrement jeunesse',
                'budget_estime': 42000,
                'besoin_site': False,
                'priorite': 5
            },
            {
                'nom': f'Association Environnement {region_nom}',
                'secteur': 'environnement',
                'description': 'Protection de l\'environnement et sensibilisation écologique',
                'budget_estime': 25000,
                'besoin_site': True,
                'priorite': 6
            },
            {
                'nom': f'Théâtre Amateur {ville_principale}',
                'secteur': 'culture',
                'description': 'Troupe de théâtre amateur, ateliers et représentations',
                'budget_estime': 18000,
                'besoin_site': True,
                'priorite': 7
            }
        ]
        
        associations = []
        
        for i, template in enumerate(templates):
            # Générer email et téléphone réalistes
            nom_clean = template['nom'].lower().replace(' ', '').replace('é', 'e').replace('è', 'e')
            nom_clean = re.sub(r'[^a-z0-9]', '', nom_clean)[:15]
            
            # Quelques associations sans email pour tester l'analyse
            has_email = i % 3 != 0  # 2/3 ont un email
            
            association = {
                'nom': template['nom'],
                'adresse': f"{10 + i*5} Rue de la {template['secteur'].title()}, {department}00{i} {ville_principale}",
                'departement': department,
                'secteur': template['secteur'],
                'description': template['description'],
                'email': f"contact@{nom_clean}.fr" if has_email else '',
                'telephone': f"02.{department}.{10+i:02d}.{20+i:02d}.{30+i:02d}",
                'site_web': f"http://www.{nom_clean}.fr" if i % 4 == 0 else '',  # 1/4 ont déjà un site
                'date_creation': f"20{20-i}-{3+i:02d}-15",
                'budget_estime': template['budget_estime'],
                'besoin_site': template['besoin_site'],
                'priorite': template['priorite'],
                'status': 'nouveau',
                'scraping_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            associations.append(association)
        
        return associations
    
    def filter_association(self, association, sector_keywords=None):
        """Filtrer les associations selon les critères"""
        if not association:
            return False
        
        # Vérifier le budget
        budget = association.get('budget_estime', 0)
        if budget < MIN_BUDGET or budget > MAX_BUDGET:
            return False
        
        # Vérifier le secteur si spécifié
        if sector_keywords:
            secteur = association.get('secteur', '').lower()
            description = association.get('description', '').lower()
            text_complet = f"{secteur} {description}"
            
            found_keyword = any(keyword.lower() in text_complet for keyword in sector_keywords)
            if not found_keyword:
                return False
        
        return True
    
    def extract_email_from_text(self, text):
        """Extraire email du texte"""
        if not text:
            return ''
        
        email_pattern = r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b'
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else ''
    
    def extract_department(self, address):
        """Extraire le département de l'adresse"""
        if not address:
            return ''
        
        # Chercher un code postal
        postal_match = re.search(r'\\b(\\d{5})\\b', address)
        if postal_match:
            postal_code = postal_match.group(1)
            return postal_code[:2]
        
        return ''

def main():
    """Fonction principale pour tester le scraper"""
    scraper = JournalOfficielScraper()
    data_manager = DataManager()
    
    print("🔍 DÉMARRAGE DU SCRAPING DES ASSOCIATIONS")
    print("=" * 50)
    
    all_associations = []
    
    # Scraper chaque département prioritaire
    for department in TARGET_DEPARTMENTS[:6]:  # Seulement Centre-Val de Loire pour le test
        print(f"\\n=== Scraping département {department} ===")
        
        try:
            associations = scraper.scrape_associations(
                department=department,
                sector_keywords=TARGET_SECTORS,
                max_pages=2
            )
            
            # Filtrer les associations
            filtered_associations = [
                assoc for assoc in associations 
                if scraper.filter_association(assoc, TARGET_SECTORS)
            ]
            
            all_associations.extend(filtered_associations)
            print(f"✅ {len(filtered_associations)} associations qualifiées")
            
        except Exception as e:
            print(f"❌ Erreur département {department}: {e}")
    
    print(f"\\n📊 RÉSULTATS DU SCRAPING")
    print("=" * 30)
    print(f"Total associations trouvées: {len(all_associations)}")
    
    if all_associations:
        # Sauvegarder les données
        data_manager.save_to_csv(all_associations, 'scraped_associations.csv')
        output_file = os.path.join(data_manager.data_dir, 'scraped_associations.csv')
        print(f"✅ Données sauvegardées: {output_file}")
        
        # Statistiques par secteur
        secteurs = {}
        for assoc in all_associations:
            secteur = assoc.get('secteur', 'autre')
            secteurs[secteur] = secteurs.get(secteur, 0) + 1
        
        print("\\nRépartition par secteur:")
        for secteur, count in secteurs.items():
            print(f"  - {secteur}: {count}")
        
        print(f"\\n🎯 Prochaine étape: Analyse des sites web")
        print("   Commande: python analyzers/website_analyzer.py")
    
    else:
        print("❌ Aucune association trouvée")
    
    return len(all_associations)

if __name__ == "__main__":
    main()
