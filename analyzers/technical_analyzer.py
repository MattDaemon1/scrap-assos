import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from urllib.parse import urlparse, urljoin
import sys
import os
import csv
from datetime import datetime
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_manager import DataManager

class WebsiteTechnicalAnalyzer:
    def __init__(self):
        self.data_manager = DataManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.driver = None
    
    def init_selenium_driver(self):
        """Initialiser le driver Selenium pour les tests avancés"""
        if self.driver:
            return
        
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Mode sans interface
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            self.driver = webdriver.Chrome(
                service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            self.driver.set_page_load_timeout(15)
            print("✅ Driver Selenium initialisé")
            
        except Exception as e:
            print(f"⚠️ Selenium non disponible: {e}")
            self.driver = None
    
    def find_association_website(self, association):
        """Trouver le site web d'une association via différentes méthodes"""
        nom = association.get('nom', '').strip()
        email = association.get('email', '').strip()
        site_declare = association.get('site_web', '').strip()
        
        websites_found = []
        
        # 1. Site web déclaré
        if site_declare and site_declare not in ['', 'N/A', 'nan']:
            result = self.test_website_accessibility(site_declare)
            websites_found.append({
                'url': site_declare,
                'source': 'declared',
                'accessible': result['accessible'],
                'status_code': result.get('status_code'),
                'response_time': result.get('response_time')
            })
        
        # 2. Chercher via le nom de l'association
        if nom:
            potential_urls = self.generate_potential_websites(nom, email)
            for url in potential_urls[:5]:  # Tester max 5 URLs
                result = self.test_website_accessibility(url)
                if result['accessible']:
                    websites_found.append({
                        'url': url,
                        'source': 'generated',
                        'accessible': True,
                        'status_code': result.get('status_code'),
                        'response_time': result.get('response_time')
                    })
                    break  # Arrêter dès qu'on trouve un site
                time.sleep(0.5)
        
        # 3. Chercher via Google (simulation)
        if not websites_found and nom:
            google_url = self.search_google_for_website(nom)
            if google_url:
                result = self.test_website_accessibility(google_url)
                if result['accessible']:
                    websites_found.append({
                        'url': google_url,
                        'source': 'google_search',
                        'accessible': True,
                        'status_code': result.get('status_code'),
                        'response_time': result.get('response_time')
                    })
        
        return websites_found
    
    def test_website_accessibility(self, url, timeout=8):
        """Tester l'accessibilité d'un site web"""
        if not url or url.strip() == '':
            return {'accessible': False, 'error': 'URL vide'}
        
        # Normaliser l'URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            start_time = time.time()
            response = self.session.get(url, timeout=timeout, allow_redirects=True)
            response_time = time.time() - start_time
            
            return {
                'accessible': response.status_code < 400,
                'status_code': response.status_code,
                'final_url': response.url,
                'response_time': response_time,
                'content_length': len(response.content),
                'headers': dict(response.headers)
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'accessible': False,
                'error': str(e),
                'status_code': None,
                'response_time': None
            }
    
    def analyze_website_technical_issues(self, url):
        """Analyser les problèmes techniques d'un site web"""
        print(f"    🔍 Analyse technique de: {url}")
        
        analysis = {
            'url': url,
            'has_ssl': False,
            'is_responsive': False,
            'load_time': 0,
            'has_mobile_viewport': False,
            'uses_modern_framework': False,
            'has_outdated_design': False,
            'accessibility_score': 0,
            'performance_issues': [],
            'technical_problems': [],
            'recommendations': []
        }
        
        try:
            # Test basique avec requests
            start_time = time.time()
            response = self.session.get(url, timeout=10)
            load_time = time.time() - start_time
            
            analysis['load_time'] = round(load_time, 2)
            analysis['has_ssl'] = url.startswith('https://')
            
            if response.status_code == 200:
                content = response.text.lower()
                
                # Analyser le contenu HTML
                analysis.update(self.analyze_html_content(content))
                
                # Tests de performance
                if load_time > 3:
                    analysis['performance_issues'].append('Temps de chargement lent (>3s)')
                
                if not analysis['has_ssl']:
                    analysis['technical_problems'].append('Pas de certificat SSL/HTTPS')
                
                # Tests avancés avec Selenium si disponible
                if self.driver:
                    selenium_analysis = self.analyze_with_selenium(url)
                    analysis.update(selenium_analysis)
            
            # Génerer les recommandations
            analysis['recommendations'] = self.generate_recommendations(analysis)
            
        except Exception as e:
            analysis['technical_problems'].append(f'Erreur d analyse: {str(e)}')
        
        return analysis
    
    def analyze_html_content(self, html_content):
        """Analyser le contenu HTML pour détecter les problèmes"""
        analysis = {
            'has_mobile_viewport': False,
            'uses_modern_framework': False,
            'has_outdated_design': False,
            'accessibility_score': 0
        }
        
        # Viewport mobile
        if 'viewport' in html_content and 'width=device-width' in html_content:
            analysis['has_mobile_viewport'] = True
        
        # Framework moderne
        modern_indicators = ['bootstrap', 'react', 'vue', 'angular', 'flexbox', 'grid']
        if any(indicator in html_content for indicator in modern_indicators):
            analysis['uses_modern_framework'] = True
        
        # Design obsolète
        outdated_indicators = ['table border=', 'font face=', 'bgcolor=', 'align=center', '<marquee']
        if any(indicator in html_content for indicator in outdated_indicators):
            analysis['has_outdated_design'] = True
        
        # Score d'accessibilité basique
        accessibility_score = 0
        if '<title>' in html_content:
            accessibility_score += 2
        if 'alt=' in html_content:
            accessibility_score += 2
        if 'aria-' in html_content:
            accessibility_score += 2
        if '<h1>' in html_content:
            accessibility_score += 2
        if 'role=' in html_content:
            accessibility_score += 2
        
        analysis['accessibility_score'] = accessibility_score
        
        return analysis
    
    def analyze_with_selenium(self, url):
        """Analyse avancée avec Selenium"""
        selenium_analysis = {
            'is_responsive': False,
            'javascript_errors': [],
            'broken_links_count': 0
        }
        
        try:
            self.driver.get(url)
            time.sleep(2)
            
            # Test responsive en changeant la taille de fenêtre
            original_size = self.driver.get_window_size()
            
            # Test mobile
            self.driver.set_window_size(375, 667)  # iPhone size
            time.sleep(1)
            
            # Vérifier si le contenu s'adapte
            body_width = self.driver.execute_script("return document.body.scrollWidth;")
            if body_width <= 400:  # Le contenu s'adapte
                selenium_analysis['is_responsive'] = True
            
            # Restaurer la taille originale
            self.driver.set_window_size(original_size['width'], original_size['height'])
            
            # Chercher les erreurs JavaScript
            logs = self.driver.get_log('browser')
            js_errors = [log for log in logs if log['level'] == 'SEVERE']
            selenium_analysis['javascript_errors'] = [error['message'] for error in js_errors]
            
        except Exception as e:
            print(f"    ⚠️ Erreur Selenium: {e}")
        
        return selenium_analysis
    
    def generate_potential_websites(self, nom, email):
        """Générer des URLs potentielles"""
        urls = []
        
        if not nom:
            return urls
        
        # Nettoyer le nom
        clean_name = re.sub(r'association |centre |club |société ', '', nom.lower())
        clean_name = re.sub(r'[^a-z0-9]', '', clean_name)[:20]
        
        if clean_name:
            # Variations d'URL
            urls.extend([
                f"https://www.{clean_name}.fr",
                f"https://{clean_name}.fr",
                f"https://www.{clean_name}.org",
                f"https://{clean_name}.org",
                f"https://www.{clean_name}.com"
            ])
        
        # Basé sur l'email si disponible
        if email and '@' in email:
            domain = email.split('@')[1]
            if not domain.endswith(('.com', '.fr', '.org')):
                urls.extend([
                    f"https://www.{domain}",
                    f"https://{domain}"
                ])
        
        return urls
    
    def search_google_for_website(self, nom):
        """Simuler une recherche Google (version simplifiée)"""
        # Dans un cas réel, on utiliserait l'API Google Search
        # Ici, on simule en testant des patterns communs
        
        clean_name = re.sub(r'[^a-z0-9]', '', nom.lower())[:15]
        
        # Patterns courants pour les associations françaises
        common_patterns = [
            f"https://www.{clean_name}-asso.fr",
            f"https://{clean_name}.asso.fr",
            f"https://www.asso-{clean_name}.fr"
        ]
        
        for pattern in common_patterns:
            result = self.test_website_accessibility(pattern)
            if result['accessible']:
                return pattern
        
        return None
    
    def generate_recommendations(self, analysis):
        """Générer des recommandations basées sur l'analyse"""
        recommendations = []
        
        # SSL/HTTPS
        if not analysis['has_ssl']:
            recommendations.append("🔒 Implémenter un certificat SSL/HTTPS pour la sécurité")
        
        # Performance
        if analysis['load_time'] > 3:
            recommendations.append("⚡ Optimiser la vitesse de chargement (compression, cache)")
        
        # Mobile/Responsive
        if not analysis['has_mobile_viewport']:
            recommendations.append("📱 Ajouter le viewport mobile pour la responsivité")
        
        if not analysis['is_responsive']:
            recommendations.append("📱 Rendre le site responsive pour tous les appareils")
        
        # Design
        if analysis['has_outdated_design']:
            recommendations.append("🎨 Moderniser le design (éliminer les éléments obsolètes)")
        
        if not analysis['uses_modern_framework']:
            recommendations.append("🔧 Utiliser un framework moderne (Bootstrap, CSS Grid)")
        
        # Accessibilité
        if analysis['accessibility_score'] < 6:
            recommendations.append("♿ Améliorer l'accessibilité (alt text, ARIA, structure)")
        
        # Recommandations globales
        if len(analysis['technical_problems']) > 2:
            recommendations.append("🚀 Refonte complète du site recommandée")
        elif len(recommendations) > 0:
            recommendations.append("✨ Mise à jour technique recommandée")
        
        return recommendations

def main():
    """Analyser les sites web d'associations réelles"""
    analyzer = WebsiteTechnicalAnalyzer()
    data_manager = DataManager()
    
    print("🔍 ANALYSE TECHNIQUE DES SITES WEB")
    print("=" * 50)
    
    # Charger les associations
    associations_file = 'realistic_associations.csv'
    associations = data_manager.load_from_csv(associations_file)
    
    if not associations:
        print(f"❌ Fichier {associations_file} non trouvé")
        print("   Lancez d'abord: python create_demo_dataset_v2.py")
        return
    
    print(f"📊 {len(associations)} associations à analyser")
    
    # Initialiser Selenium si possible
    analyzer.init_selenium_driver()
    
    analyzed_associations = []
    
    for i, association in enumerate(associations, 1):
        nom = association.get('nom', f'Association {i}')
        print(f"\\n[{i}/{len(associations)}] {nom}")
        
        try:
            # 1. Trouver les sites web
            websites = analyzer.find_association_website(association)
            
            website_analysis = {
                'websites_found': len(websites),
                'working_websites': [],
                'broken_websites': [],
                'needs_website': True,
                'technical_issues': [],
                'recommendations': [],
                'priority_score': 5
            }
            
            if websites:
                for site in websites:
                    if site['accessible']:
                        print(f"  ✅ Site trouvé: {site['url']}")
                        
                        # 2. Analyser les problèmes techniques
                        tech_analysis = analyzer.analyze_website_technical_issues(site['url'])
                        
                        site_info = {
                            'url': site['url'],
                            'source': site['source'],
                            'technical_analysis': tech_analysis
                        }
                        
                        website_analysis['working_websites'].append(site_info)
                        website_analysis['needs_website'] = False
                        
                        # Calcul du score de priorité
                        priority = 3  # Base: site existant
                        if len(tech_analysis['technical_problems']) > 2:
                            priority += 3  # Problèmes techniques
                        if tech_analysis['has_outdated_design']:
                            priority += 2  # Design obsolète
                        if not tech_analysis['is_responsive']:
                            priority += 2  # Pas responsive
                        if tech_analysis['load_time'] > 3:
                            priority += 1  # Lent
                        
                        website_analysis['priority_score'] = min(priority, 10)
                        website_analysis['technical_issues'] = tech_analysis['technical_problems']
                        website_analysis['recommendations'] = tech_analysis['recommendations']
                        
                        if len(tech_analysis['recommendations']) > 3:
                            print(f"    🎯 PROSPECT: Nombreux problèmes techniques détectés")
                        else:
                            print(f"    ✅ Site correct avec {len(tech_analysis['recommendations'])} améliorations possibles")
                    else:
                        website_analysis['broken_websites'].append(site['url'])
                        print(f"  ❌ Site cassé: {site['url']}")
            
            if website_analysis['needs_website']:
                print(f"  🎯 PROSPECT: Aucun site web trouvé")
                website_analysis['priority_score'] = 9 if association.get('email') else 7
                website_analysis['recommendations'] = ["Création d'un site web professionnel nécessaire"]
            
            # Combiner toutes les données
            complete_analysis = {
                **association,
                **website_analysis,
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            analyzed_associations.append(complete_analysis)
            
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
            error_analysis = {
                **association,
                'websites_found': 0,
                'needs_website': True,
                'priority_score': 5,
                'recommendations': [f'Erreur d analyse: {str(e)}'],
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            analyzed_associations.append(error_analysis)
        
        time.sleep(1)  # Pause entre analyses
    
    # Fermer le driver Selenium
    if analyzer.driver:
        analyzer.driver.quit()
    
    # Sauvegarder les résultats
    output_file = 'technical_analysis.csv'
    data_manager.save_to_csv(analyzed_associations, output_file)
    
    print(f"\\n📊 RÉSULTATS DE L'ANALYSE TECHNIQUE")
    print("=" * 40)
    
    # Statistiques
    total = len(analyzed_associations)
    need_website = sum(1 for a in analyzed_associations if a.get('needs_website', True))
    have_website = total - need_website
    high_priority = sum(1 for a in analyzed_associations if a.get('priority_score', 0) >= 7)
    
    print(f"Total analysé: {total}")
    print(f"Sans site web: {need_website}")
    print(f"Avec site web: {have_website}")
    print(f"Haute priorité: {high_priority}")
    
    # Top prospects
    prospects = sorted(analyzed_associations, key=lambda x: x.get('priority_score', 0), reverse=True)
    top_prospects = prospects[:10]
    
    print(f"\\n🎯 TOP 10 PROSPECTS:")
    for i, prospect in enumerate(top_prospects, 1):
        nom = prospect.get('nom', 'N/A')[:35]
        score = prospect.get('priority_score', 0)
        email = prospect.get('email', 'Pas d email')[:25]
        status = "Pas de site" if prospect.get('needs_website') else "Site à améliorer"
        print(f"  {i:2d}. {nom:<35} | Score: {score} | {status} | {email}")
    
    print(f"\\n✅ Analyse sauvegardée: data/{output_file}")
    print(f"\\n🚀 Prochaine étape: Synchronisation Google Sheets et campagne email")
    
    return len(top_prospects)

if __name__ == "__main__":
    main()
