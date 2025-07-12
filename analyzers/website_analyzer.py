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
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_manager import DataManager

class WebsiteAnalyzer:
    def __init__(self):
        self.data_manager = DataManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def check_website_exists(self, url, timeout=10):
        """Vérifier si un site web existe et est accessible"""
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
    
    def analyze_website_quality(self, url):
        """Analyser la qualité d'un site web"""
        analysis = {
            'url': url,
            'is_responsive': False,
            'has_ssl': False,
            'is_modern': False,
            'accessibility_issues': [],
            'technology_stack': [],
            'last_updated': None,
            'performance_score': 0
        }
        
        try:
            # Vérifier l'existence
            exists_check = self.check_website_exists(url)
            if not exists_check['exists']:
                analysis['error'] = 'Site inaccessible'
                return analysis
            
            # Analyser avec requests pour les bases
            response = self.session.get(url, timeout=15)
            html_content = response.text.lower()
            
            # Vérifier SSL
            analysis['has_ssl'] = url.startswith('https://')
            
            # Détecter les technologies obsolètes
            obsolete_tech = ['flash', 'silverlight', 'java applet', 'activex']
            for tech in obsolete_tech:
                if tech in html_content:
                    analysis['technology_stack'].append(f'obsolete_{tech.replace(" ", "_")}')
            
            # Vérifier la responsivité (basique)
            responsive_indicators = ['viewport', 'media query', 'bootstrap', 'responsive']
            analysis['is_responsive'] = any(indicator in html_content for indicator in responsive_indicators)
            
            # Détecter CMS moderne
            modern_cms = ['wordpress', 'drupal', 'joomla', 'react', 'vue', 'angular']
            for cms in modern_cms:
                if cms in html_content:
                    analysis['technology_stack'].append(cms)
            
            # Score de modernité basique
            score = 0
            if analysis['has_ssl']:
                score += 30
            if analysis['is_responsive']:
                score += 40
            if any('modern' in tech for tech in analysis['technology_stack']):
                score += 30
            
            analysis['performance_score'] = min(score, 100)
            analysis['is_modern'] = score >= 70
            
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis
    
    def check_association_websites(self, associations):
        """Vérifier les sites web d'une liste d'associations"""
        results = []
        
        for i, association in enumerate(associations):
            print(f"Analyse {i+1}/{len(associations)}: {association.get('name', 'Sans nom')}")
            
            # Générer les URLs possibles
            possible_urls = self.generate_possible_urls(association)
            
            website_found = False
            best_analysis = None
            
            for url in possible_urls:
                print(f"  Test URL: {url}")
                analysis = self.analyze_website_quality(url)
                
                if analysis.get('exists', False) or not analysis.get('error'):
                    website_found = True
                    best_analysis = analysis
                    break
                
                time.sleep(1)  # Pause entre les requêtes
            
            # Mise à jour de l'association
            association['website_analysis'] = best_analysis
            association['has_website'] = website_found
            association['website_quality'] = 'good' if (best_analysis and best_analysis.get('is_modern')) else 'poor'
            association['needs_website'] = not website_found or (best_analysis and not best_analysis.get('is_modern'))
            
            results.append(association)
            
            # Pause entre les associations
            time.sleep(2)
        
        return results
    
    def generate_possible_urls(self, association):
        """Générer les URLs possibles pour une association"""
        name = association.get('name', '').lower()
        urls = []
        
        # Nettoyer le nom
        import re
        clean_name = re.sub(r'[^a-z0-9\s]', '', name)
        clean_name = re.sub(r'\s+', '-', clean_name.strip())
        
        # Patterns d'URL courantes
        patterns = [
            f"{clean_name}.fr",
            f"{clean_name}.org",
            f"{clean_name}.asso.fr",
            f"www.{clean_name}.fr",
            f"asso-{clean_name}.fr",
            f"{clean_name.replace('-', '')}.fr"
        ]
        
        # Limiter à 5 tentatives max
        return patterns[:5]
    
    def batch_analyze(self, csv_filename):
        """Analyser en lot depuis un fichier CSV"""
        print(f"Chargement des associations depuis {csv_filename}")
        associations = self.data_manager.load_from_csv(csv_filename)
        
        if not associations:
            print("Aucune association trouvée")
            return
        
        print(f"Analyse de {len(associations)} associations...")
        analyzed = self.check_association_websites(associations)
        
        # Sauvegarder les résultats
        output_filename = f"analyzed_{csv_filename}"
        self.data_manager.save_to_csv(analyzed, output_filename)
        
        # Statistiques
        stats = {
            'total': len(analyzed),
            'with_website': len([a for a in analyzed if a.get('has_website')]),
            'needs_website': len([a for a in analyzed if a.get('needs_website')]),
            'good_quality': len([a for a in analyzed if a.get('website_quality') == 'good'])
        }
        
        print("\n=== STATISTIQUES ===")
        print(f"Total analysé: {stats['total']}")
        print(f"Avec site web: {stats['with_website']}")
        print(f"Besoin nouveau site: {stats['needs_website']}")
        print(f"Site de bonne qualité: {stats['good_quality']}")
        
        # Exporter les prospects qualifiés
        prospects = [a for a in analyzed if a.get('needs_website') and a.get('email')]
        if prospects:
            self.data_manager.export_for_outreach(prospects, "prospects_qualifies.csv")
            print(f"\nExporté {len(prospects)} prospects qualifiés")
        
        return analyzed

def main():
    analyzer = WebsiteAnalyzer()
    
    # Test avec un fichier CSV existant
    import os
    data_dir = "data"
    
    if os.path.exists(data_dir):
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        if csv_files:
            print("Fichiers CSV disponibles:")
            for i, filename in enumerate(csv_files):
                print(f"{i+1}. {filename}")
            
            choice = input("Entrez le numéro du fichier à analyser (ou 'q' pour quitter): ")
            if choice.isdigit() and 1 <= int(choice) <= len(csv_files):
                selected_file = csv_files[int(choice)-1]
                analyzer.batch_analyze(selected_file)
            else:
                print("Aucune analyse effectuée")
        else:
            print("Aucun fichier CSV trouvé dans le dossier data/")
    else:
        print("Dossier data/ non trouvé")

if __name__ == "__main__":
    main()
