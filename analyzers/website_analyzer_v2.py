import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from urllib.parse import urlparse
import sys
import os
import csv
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_manager import DataManager

class WebsiteAnalyzer:
    def __init__(self):
        self.data_manager = DataManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def check_website_exists(self, url, timeout=5):
        """Vérifier si un site web existe et est accessible"""
        if not url or url.strip() == '':
            return {
                'exists': False,
                'status_code': None,
                'error': 'URL vide',
                'response_time': None
            }
        
        try:
            # Normaliser l'URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            response = self.session.head(url, timeout=timeout, allow_redirects=True)
            return {
                'exists': response.status_code < 400,
                'status_code': response.status_code,
                'final_url': response.url,
                'response_time': response.elapsed.total_seconds()
            }
        except requests.exceptions.RequestException as e:
            return {
                'exists': False,
                'error': str(e),
                'status_code': None,
                'response_time': None
            }
    
    def generate_potential_urls(self, association_name, email):
        """Générer des URLs potentielles pour une association"""
        urls = []
        
        if not association_name:
            return urls
        
        # Nettoyer le nom de l'association
        clean_name = association_name.lower()
        clean_name = clean_name.replace('association ', '').replace('centre ', '').replace('club ', '')
        clean_name = clean_name.replace(' de ', '').replace(' du ', '').replace(' des ', '')
        clean_name = clean_name.replace(' ', '').replace('-', '').replace('é', 'e').replace('è', 'e')
        clean_name = ''.join(c for c in clean_name if c.isalnum())[:20]
        
        # URL basée sur le nom
        if clean_name:
            urls.extend([
                f"https://www.{clean_name}.fr",
                f"https://{clean_name}.fr",
                f"https://www.{clean_name}.org",
                f"https://{clean_name}.org"
            ])
        
        # URL basée sur l'email si disponible
        if email and '@' in email:
            domain = email.split('@')[1]
            if domain != 'gmail.com' and domain != 'outlook.com':
                urls.extend([
                    f"https://www.{domain}",
                    f"https://{domain}"
                ])
        
        return urls[:6]  # Limiter à 6 tentatives
    
    def analyze_association_website_status(self, association):
        """Analyser le statut web d'une association"""
        nom = association.get('nom', '')
        email = association.get('email', '')
        site_existant = association.get('site_web', '')
        
        analysis = {
            'nom': nom,
            'email': email,
            'site_existant': site_existant,
            'site_fonctionne': False,
            'urls_testees': [],
            'besoin_site': True,
            'priorite_web': 5,
            'recommandation': '',
            'date_analyse': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Test du site existant s'il y en a un
        if site_existant:
            print(f"  Test site existant: {site_existant}")
            result = self.check_website_exists(site_existant)
            analysis['urls_testees'].append({
                'url': site_existant,
                'type': 'existant',
                'fonctionne': result['exists'],
                'status_code': result.get('status_code')
            })
            
            if result['exists']:
                analysis['site_fonctionne'] = True
                analysis['besoin_site'] = False
                analysis['priorite_web'] = 2
                analysis['recommandation'] = 'Site existant fonctionnel - Peut-être proposer une refonte'
            else:
                analysis['recommandation'] = 'Site déclaré mais non fonctionnel - Besoin urgent d\'un nouveau site'
                analysis['priorite_web'] = 9
        
        # Si pas de site ou site non fonctionnel, tester des URLs potentielles
        if not analysis['site_fonctionne']:
            print(f"  Recherche URLs potentielles...")
            potential_urls = self.generate_potential_urls(nom, email)
            
            for url in potential_urls:
                print(f"    Test: {url}")
                result = self.check_website_exists(url)
                analysis['urls_testees'].append({
                    'url': url,
                    'type': 'potentielle',
                    'fonctionne': result['exists'],
                    'status_code': result.get('status_code')
                })
                
                if result['exists']:
                    analysis['site_fonctionne'] = True
                    analysis['besoin_site'] = False
                    analysis['priorite_web'] = 3
                    analysis['recommandation'] = f'Site trouvé non déclaré: {url} - Proposer référencement/optimisation'
                    break
                
                time.sleep(0.5)  # Pause entre les tests
        
        # Si aucun site trouvé
        if not analysis['site_fonctionne']:
            if email:
                analysis['priorite_web'] = 8
                analysis['recommandation'] = 'Aucun site web - Contact email disponible - Excellent prospect'
            else:
                analysis['priorite_web'] = 6
                analysis['recommandation'] = 'Aucun site web - Pas d email - Prospect moyen'
        
        return analysis

def main():
    """Fonction principale pour analyser les sites web"""
    analyzer = WebsiteAnalyzer()
    data_manager = DataManager()
    
    print("🔍 ANALYSE DES SITES WEB DES ASSOCIATIONS")
    print("=" * 50)
    
    # Charger les associations scrapées
    associations_file = 'scraped_associations.csv'
    associations = data_manager.load_from_csv(associations_file)
    
    if not associations:
        print(f"❌ Aucune association trouvée dans {associations_file}")
        return
    
    print(f"📊 {len(associations)} associations à analyser")
    
    analyses = []
    
    for i, association in enumerate(associations, 1):
        nom = association.get('nom', f'Association {i}')
        print(f"\\n[{i}/{len(associations)}] Analyse: {nom}")
        
        try:
            analysis = analyzer.analyze_association_website_status(association)
            
            # Combiner avec les données originales
            combined_data = {**association, **analysis}
            analyses.append(combined_data)
            
            # Afficher le résultat
            if analysis['site_fonctionne']:
                print(f"  ✅ Site trouvé: {analysis['recommandation']}")
            else:
                print(f"  🎯 Prospect: {analysis['recommandation']}")
                
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
            # Ajouter l'association même en cas d'erreur
            error_analysis = {
                **association,
                'site_fonctionne': False,
                'besoin_site': True,
                'priorite_web': 5,
                'recommandation': f'Erreur d analyse: {str(e)}',
                'date_analyse': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            analyses.append(error_analysis)
    
    # Sauvegarder les résultats
    output_file = 'analyzed_associations.csv'
    data_manager.save_to_csv(analyses, output_file)
    
    print(f"\\n📊 RÉSULTATS DE L'ANALYSE")
    print("=" * 30)
    print(f"Total analysé: {len(analyses)}")
    
    # Statistiques
    sites_fonctionnels = sum(1 for a in analyses if a.get('site_fonctionne', False))
    besoin_site = sum(1 for a in analyses if a.get('besoin_site', True))
    avec_email = sum(1 for a in analyses if a.get('email', '').strip())
    
    print(f"Sites fonctionnels: {sites_fonctionnels}")
    print(f"Besoin d'un site: {besoin_site}")
    print(f"Avec email: {avec_email}")
    
    # Top prospects (besoin site + email)
    top_prospects = [a for a in analyses if a.get('besoin_site', True) and a.get('email', '').strip()]
    print(f"\\n🎯 TOP PROSPECTS: {len(top_prospects)} associations")
    
    if top_prospects:
        # Trier par priorité
        top_prospects.sort(key=lambda x: x.get('priorite_web', 5), reverse=True)
        
        print("\\nTop 5 prospects:")
        for i, prospect in enumerate(top_prospects[:5], 1):
            nom = prospect.get('nom', 'N/A')[:40]
            email = prospect.get('email', 'N/A')
            priorite = prospect.get('priorite_web', 0)
            print(f"  {i}. {nom} - {email} (Priorité: {priorite})")
    
    print(f"\\n✅ Données sauvegardées: data/{output_file}")
    print(f"\\n🚀 Prochaine étape: Synchronisation Google Sheets")
    print("   Commande: python email_manager/campaign_manager.py")
    
    return len(top_prospects)

if __name__ == "__main__":
    main()
