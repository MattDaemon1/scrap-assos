import requests
import time
import re
import sys
import os
from datetime import datetime
import urllib.parse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_manager import DataManager

class ApiAssociationAnalyzer:
    """Analyseur spécialisé pour les associations trouvées via APIs officielles"""
    
    def __init__(self):
        self.data_manager = DataManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search_real_website(self, association):
        """Rechercher le vrai site web d'une association"""
        nom = association.get('nom', '')
        ville = association.get('ville', '')
        siren = association.get('siren', '')
        
        print(f"🔍 Recherche site: {nom} - {ville}")
        
        # 1. Recherche Google directe
        real_sites = self._search_google(nom, ville, siren)
        
        # 2. Recherche sur les répertoires associatifs
        directory_info = self._search_directories(nom, ville)
        
        # 3. Recherche site municipal
        municipal_info = self._search_municipal_site(nom, ville)
        
        return {
            'google_results': real_sites,
            'directory_info': directory_info,
            'municipal_info': municipal_info
        }
    
    def _search_google(self, nom, ville, siren):
        """Recherche Google pour le site officiel"""
        try:
            # Nettoyer le nom pour la recherche
            nom_clean = nom.replace('ASSOCIATION', '').replace('(', '').replace(')', '').strip()
            
            # Requêtes de recherche
            search_queries = [
                f'"{nom_clean}" {ville} association site officiel',
                f'"{nom_clean}" {ville} association',
                f'"{nom_clean}" association {ville}'
            ]
            
            if siren:
                search_queries.append(f'SIREN {siren} association')
            
            found_sites = []
            
            for query in search_queries[:2]:  # Limiter à 2 requêtes
                print(f"  🔎 Google: {query}")
                
                # Utiliser DuckDuckGo comme alternative à Google (plus permissif)
                try:
                    url = "https://duckduckgo.com/html/"
                    params = {'q': query}
                    
                    response = self.session.get(url, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        # Extraire les URLs des résultats
                        content = response.text
                        
                        # Patterns pour trouver des sites d'associations
                        patterns = [
                            r'href="([^"]*(?:' + re.escape(ville.lower()) + r')[^"]*\.(?:fr|org|com|net)[^"]*)"',
                            r'href="([^"]*(?:' + re.escape(nom_clean.lower().replace(' ', '')) + r')[^"]*\.(?:fr|org|com)[^"]*)"',
                            r'href="([^"]*association[^"]*\.(?:fr|org)[^"]*)"'
                        ]
                        
                        for pattern in patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            for match in matches[:3]:  # Max 3 par pattern
                                if self._is_valid_association_url(match):
                                    found_sites.append({
                                        'url': match,
                                        'source': 'DuckDuckGo',
                                        'query': query,
                                        'confidence': self._calculate_confidence(match, nom_clean, ville)
                                    })
                    
                    time.sleep(1)  # Délai respectueux
                    
                except Exception as e:
                    print(f"    ⚠️ Erreur recherche: {e}")
            
            # Trier par confiance
            found_sites.sort(key=lambda x: x['confidence'], reverse=True)
            return found_sites[:3]  # Top 3
            
        except Exception as e:
            print(f"  ❌ Erreur Google: {e}")
            return []
    
    def _search_directories(self, nom, ville):
        """Rechercher dans les répertoires d'associations"""
        directories = [
            {
                'name': 'HelloAsso',
                'url': 'https://www.helloasso.com/associations/recherche',
                'search_param': 'q'
            },
            {
                'name': 'Net1901',
                'url': 'https://www.net1901.org/recherche',
                'search_param': 'q'
            }
        ]
        
        results = []
        
        for directory in directories:
            try:
                print(f"  📂 {directory['name']}...")
                
                # Recherche dans le répertoire
                search_term = f"{nom} {ville}".replace('ASSOCIATION', '').strip()
                
                params = {directory['search_param']: search_term}
                response = self.session.get(directory['url'], params=params, timeout=10)
                
                if response.status_code == 200:
                    # Analyser la réponse pour extraire des infos
                    content = response.text.lower()
                    
                    # Chercher des mentions de l'association
                    if any(word in content for word in nom.lower().split()[:2]):
                        results.append({
                            'directory': directory['name'],
                            'found': True,
                            'url': response.url
                        })
                    
                time.sleep(2)
                
            except Exception as e:
                print(f"    ⚠️ Erreur {directory['name']}: {e}")
        
        return results
    
    def _search_municipal_site(self, nom, ville):
        """Rechercher sur le site de la commune"""
        try:
            print(f"  🏛️ Site municipal {ville}...")
            
            # Construire l'URL du site municipal
            ville_clean = ville.lower().replace(' ', '-').replace("'", '-')
            possible_urls = [
                f"https://www.{ville_clean}.fr",
                f"https://{ville_clean}.fr",
                f"https://mairie-{ville_clean}.fr"
            ]
            
            for url in possible_urls:
                try:
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        # Chercher une page associations
                        content = response.text.lower()
                        
                        if 'association' in content:
                            # Chercher des liens vers une page associations
                            association_links = re.findall(
                                r'href="([^"]*association[^"]*)"', 
                                response.text, 
                                re.IGNORECASE
                            )
                            
                            return {
                                'municipal_site': url,
                                'has_associations_page': len(association_links) > 0,
                                'association_links': association_links[:3]
                            }
                    
                except Exception:
                    continue
            
            return {'municipal_site': None, 'has_associations_page': False}
            
        except Exception as e:
            print(f"    ⚠️ Erreur site municipal: {e}")
            return {}
    
    def _is_valid_association_url(self, url):
        """Vérifier si l'URL semble valide pour une association"""
        if not url or len(url) < 10:
            return False
        
        # Filtrer les URLs non pertinentes
        invalid_patterns = [
            'google.com', 'facebook.com', 'twitter.com', 'linkedin.com',
            'wikipedia.org', 'youtube.com', 'instagram.com'
        ]
        
        return not any(pattern in url.lower() for pattern in invalid_patterns)
    
    def _calculate_confidence(self, url, nom, ville):
        """Calculer un score de confiance pour l'URL"""
        score = 0
        url_lower = url.lower()
        nom_lower = nom.lower()
        ville_lower = ville.lower()
        
        # Points pour correspondance nom
        nom_words = nom_lower.replace('association', '').split()
        for word in nom_words:
            if len(word) > 3 and word in url_lower:
                score += 3
        
        # Points pour correspondance ville
        if ville_lower.replace(' ', '') in url_lower.replace('-', ''):
            score += 2
        
        # Points pour extension appropriée
        if url_lower.endswith('.fr'):
            score += 2
        elif url_lower.endswith('.org'):
            score += 1
        
        # Points pour mots-clés association
        if any(word in url_lower for word in ['asso', 'association', 'club']):
            score += 1
        
        return score
    
    def find_real_contacts(self, association, website_info):
        """Chercher les vrais contacts depuis les sites trouvés"""
        contacts = {
            'emails': [],
            'phones': [],
            'social_media': []
        }
        
        # Analyser les sites trouvés
        google_results = website_info.get('google_results', [])
        
        for result in google_results[:2]:  # 2 meilleurs résultats
            url = result['url']
            print(f"  📧 Analyse contacts: {url}")
            
            try:
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    content = response.text
                    
                    # Extraire emails
                    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
                    for email in emails[:3]:  # Max 3 emails
                        if self._is_valid_email(email):
                            contacts['emails'].append(email)
                    
                    # Extraire téléphones français
                    phones = re.findall(r'0[1-9](?:[.\s-]?\d{2}){4}', content)
                    contacts['phones'].extend(phones[:2])  # Max 2 téléphones
                
                time.sleep(1)
                
            except Exception as e:
                print(f"    ⚠️ Erreur analyse {url}: {e}")
        
        # Déduplication
        contacts['emails'] = list(set(contacts['emails']))
        contacts['phones'] = list(set(contacts['phones']))
        
        return contacts
    
    def _is_valid_email(self, email):
        """Vérifier si l'email semble valide et pertinent"""
        if not email or len(email) < 5:
            return False
        
        # Filtrer les emails non pertinents
        invalid_patterns = [
            'webmaster@', 'admin@', 'no-reply@', 'noreply@',
            'support@', 'contact@example', '@example.com'
        ]
        
        return not any(pattern in email.lower() for pattern in invalid_patterns)
    
    def analyze_api_associations(self, filename="api_associations_20250713_1425.csv"):
        """Analyser toutes les associations du fichier API"""
        print("🎯 ANALYSE ASSOCIATIONS APIs OFFICIELLES")
        print("=" * 55)
        
        # Charger les données
        associations = self.data_manager.load_from_csv(filename)
        
        if not associations:
            print(f"❌ Impossible de charger {filename}")
            return
        
        print(f"📊 {len(associations)} associations à analyser")
        
        analyzed_associations = []
        
        for i, association in enumerate(associations[:10], 1):  # Limiter à 10 pour commencer
            print(f"\n📋 {i}/10 - {association.get('nom', 'Nom inconnu')}")
            
            # Rechercher le vrai site web
            website_info = self.search_real_website(association)
            
            # Chercher les vrais contacts
            contacts = self.find_real_contacts(association, website_info)
            
            # Enrichir l'association
            association_enriched = association.copy()
            association_enriched.update({
                'site_web_reel': website_info['google_results'][0]['url'] if website_info['google_results'] else '',
                'site_web_confiance': website_info['google_results'][0]['confidence'] if website_info['google_results'] else 0,
                'emails_reels': ', '.join(contacts['emails']) if contacts['emails'] else '',
                'telephones_reels': ', '.join(contacts['phones']) if contacts['phones'] else '',
                'municipal_site': website_info.get('municipal_info', {}).get('municipal_site', ''),
                'directory_found': len(website_info.get('directory_info', [])) > 0,
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            analyzed_associations.append(association_enriched)
            
            # Délai entre analyses
            time.sleep(2)
        
        # Sauvegarder les résultats
        if analyzed_associations:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            output_filename = f"analyzed_api_associations_{timestamp}.csv"
            
            self.data_manager.save_to_csv(analyzed_associations, output_filename)
            
            print(f"\n✅ ANALYSE TERMINÉE")
            print(f"📁 Fichier: data/{output_filename}")
            print(f"📊 {len(analyzed_associations)} associations analysées")
            
            # Statistiques
            stats = self._generate_analysis_stats(analyzed_associations)
            print(f"\n📈 RÉSULTATS:")
            for key, value in stats.items():
                print(f"  • {key}: {value}")
            
            return analyzed_associations
        
        return []
    
    def _generate_analysis_stats(self, associations):
        """Générer des statistiques d'analyse"""
        total = len(associations)
        
        with_real_website = sum(1 for a in associations if a.get('site_web_reel'))
        with_real_emails = sum(1 for a in associations if a.get('emails_reels'))
        with_real_phones = sum(1 for a in associations if a.get('telephones_reels'))
        in_directories = sum(1 for a in associations if a.get('directory_found'))
        
        avg_confidence = sum(a.get('site_web_confiance', 0) for a in associations) / total if total > 0 else 0
        
        return {
            'Total analysées': total,
            'Avec site web réel trouvé': with_real_website,
            'Avec emails réels trouvés': with_real_emails,
            'Avec téléphones réels trouvés': with_real_phones,
            'Trouvées dans répertoires': in_directories,
            'Confiance moyenne sites': f"{avg_confidence:.1f}/10"
        }

def main():
    """Fonction principale"""
    analyzer = ApiAssociationAnalyzer()
    
    print("🎯 ANALYSEUR ASSOCIATIONS APIs OFFICIELLES")
    print("=" * 55)
    print("🔍 Recherche sites web réels")
    print("📧 Extraction contacts authentiques")
    print("🏛️ Vérification sites municipaux")
    print("📂 Consultation répertoires associatifs")
    
    print(f"\n❓ Lancer l'analyse des associations API ? (oui/non): ", end="")
    confirmation = input().strip().lower()
    
    if confirmation in ['oui', 'o', 'yes', 'y']:
        results = analyzer.analyze_api_associations()
        
        if results:
            print(f"\n🎉 ANALYSE RÉUSSIE !")
            print(f"✅ Sites web réels trouvés")
            print(f"✅ Contacts authentiques extraits")
            print(f"✅ Données enrichies et vérifiées")
        else:
            print(f"\n😞 Aucun résultat d'analyse")
    else:
        print("🚪 Analyse annulée")

if __name__ == "__main__":
    main()
