import pandas as pd
import requests
import time
import re
import sys
import os
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_manager import DataManager

class RnaContactScraper:
    """Scraper pour trouver les contacts des associations RNA par nom et ville"""
    
    def __init__(self):
        self.data_manager = DataManager()
        self.session = requests.Session()
        
        # Rotation User-Agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'
        ]
        
        self.search_engines = [
            self._search_google,
            self._search_qwant, 
            self._search_bing
        ]
        
        self.association_sites = [
            "helloasso.com",
            "loisirs.fr", 
            "net1901.org",
            "journal-officiel.gouv.fr",
            "associations.gouv.fr"
        ]
        
    def load_rna_associations(self, filepath):
        """Charger les associations RNA traitées"""
        try:
            df = pd.read_csv(filepath)
            print(f"📄 {len(df)} associations RNA chargées")
            return df.to_dict('records')
        except Exception as e:
            print(f"❌ Erreur chargement: {e}")
            return []
    
    def search_association_contacts(self, association):
        """Rechercher contacts d'une association spécifique"""
        nom = association['nom']
        ville = association['ville']
        secteur = association.get('secteur_nom', '')
        
        print(f"🔍 {nom[:40]}... ({ville})")
        
        # Préparer requêtes de recherche
        search_queries = self._build_search_queries(nom, ville, secteur)
        
        contacts = {
            'email_principal': '',
            'telephone': '',
            'site_web': '',
            'facebook': '',
            'contacts_sources': [],
            'search_success': False
        }
        
        # Essayer chaque moteur de recherche
        for search_engine in self.search_engines:
            if contacts['search_success']:
                break
                
            try:
                engine_contacts = search_engine(search_queries, association)
                if engine_contacts and (engine_contacts.get('email') or engine_contacts.get('website')):
                    contacts.update({
                        'email_principal': engine_contacts.get('email', ''),
                        'telephone': engine_contacts.get('phone', ''),
                        'site_web': engine_contacts.get('website', ''),
                        'facebook': engine_contacts.get('facebook', ''),
                        'search_success': True
                    })
                    contacts['contacts_sources'].append(engine_contacts.get('source', 'unknown'))
                    break
                    
            except Exception as e:
                continue
        
        # Si pas de résultat, essayer recherche directe sur sites spécialisés
        if not contacts['search_success']:
            contacts.update(self._search_specialized_sites(nom, ville))
        
        return contacts
    
    def _build_search_queries(self, nom, ville, secteur):
        """Construire les requêtes de recherche optimisées"""
        # Nettoyer le nom d'association
        nom_clean = self._clean_association_name(nom)
        ville_clean = ville.replace('-', ' ')
        
        queries = [
            f'"{nom_clean}" {ville_clean} contact email',
            f'"{nom_clean}" {ville_clean} site internet',
            f'"{nom_clean}" {ville_clean} association contact',
            f'{nom_clean} {ville_clean} helloasso',
            f'{nom_clean} {ville_clean} facebook',
            f'association "{nom_clean}" {ville_clean}',
        ]
        
        # Ajouter requête secteur si pertinent
        if secteur and secteur != 'Autre':
            queries.append(f'{nom_clean} {ville_clean} {secteur.lower()}')
        
        return queries
    
    def _clean_association_name(self, nom):
        """Nettoyer nom association pour recherche"""
        # Supprimer caractères spéciaux et accents problématiques
        nom = nom.replace('é', 'e').replace('è', 'e').replace('ê', 'e')
        nom = nom.replace('à', 'a').replace('ù', 'u').replace('ç', 'c')
        nom = nom.replace('É', 'E').replace('È', 'E').replace('À', 'A')
        
        # Supprimer mots inutiles
        stop_words = ['de', 'du', 'des', 'le', 'la', 'les', 'et', 'ou', 'avec']
        words = [w for w in nom.split() if w.lower() not in stop_words and len(w) > 2]
        
        return ' '.join(words[:4])  # Max 4 mots
    
    def _search_google(self, queries, association):
        """Recherche via Google"""
        try:
            # Prendre la meilleure requête
            query = queries[0]
            
            # Headers anti-détection
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # URL Google
            google_url = f"https://www.google.com/search?q={quote_plus(query)}&num=20"
            
            response = self.session.get(google_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                return self._extract_contacts_from_html(response.text, association, 'Google')
            
        except Exception as e:
            pass
        
        return None
    
    def _search_qwant(self, queries, association):
        """Recherche via Qwant (plus respectueux)"""
        try:
            query = queries[0]
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml',
                'Accept-Language': 'fr-FR,fr;q=0.9'
            }
            
            qwant_url = f"https://www.qwant.com/?q={quote_plus(query)}&t=web"
            
            response = self.session.get(qwant_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                return self._extract_contacts_from_html(response.text, association, 'Qwant')
                
        except Exception as e:
            pass
        
        return None
    
    def _search_bing(self, queries, association):
        """Recherche via Bing"""
        try:
            query = queries[0]
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml'
            }
            
            bing_url = f"https://www.bing.com/search?q={quote_plus(query)}"
            
            response = self.session.get(bing_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                return self._extract_contacts_from_html(response.text, association, 'Bing')
                
        except Exception as e:
            pass
        
        return None
    
    def _extract_contacts_from_html(self, html, association, source):
        """Extraire contacts depuis HTML de résultats"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text()
            
            # Extraire email
            email = self._extract_best_email(text, association)
            
            # Extraire téléphone
            phone = self._extract_phone(text)
            
            # Extraire site web
            website = self._extract_best_website(html, association)
            
            # Extraire Facebook
            facebook = self._extract_facebook(html, association)
            
            if email or website:
                return {
                    'email': email,
                    'phone': phone,
                    'website': website,
                    'facebook': facebook,
                    'source': source
                }
                
        except Exception as e:
            pass
        
        return None
    
    def _extract_best_email(self, text, association):
        """Extraire le meilleur email pour l'association"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        if not emails:
            return ""
        
        nom_words = association['nom'].lower().split()[:3]
        ville_clean = association['ville'].lower().replace('-', '')
        
        # Scorer les emails
        scored_emails = []
        
        for email in emails:
            if not self._is_valid_email_format(email):
                continue
                
            email_lower = email.lower()
            score = 0
            
            # Points pour mots du nom d'association
            for word in nom_words:
                if len(word) > 3 and word in email_lower:
                    score += 10
            
            # Points pour ville
            if len(ville_clean) > 4 and ville_clean in email_lower:
                score += 8
            
            # Points pour domaines associations
            if '.asso.fr' in email_lower:
                score += 15
            elif '.org' in email_lower:
                score += 10
            elif '.fr' in email_lower:
                score += 5
            
            # Points pour patterns association
            if any(pattern in email_lower for pattern in ['association', 'asso', 'club', 'amicale']):
                score += 5
            
            # Pénalités pour emails génériques
            if any(generic in email_lower for generic in ['contact@gmail', 'info@gmail', 'webmaster', 'noreply']):
                score -= 20
            
            if score > 0:
                scored_emails.append((email, score))
        
        if scored_emails:
            # Retourner email avec meilleur score
            best_email = sorted(scored_emails, key=lambda x: x[1], reverse=True)[0][0]
            return best_email.lower()
        
        return ""
    
    def _extract_phone(self, text):
        """Extraire numéro de téléphone français"""
        # Patterns téléphone français
        phone_patterns = [
            r'0[1-9](?:[.\s-]?\d{2}){4}',
            r'\+33[.\s-]?[1-9](?:[.\s-]?\d{2}){4}',
            r'(?:Tel|Tél|Téléphone|Phone)[\s:]*0[1-9](?:[.\s-]?\d{2}){4}'
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                phone = match.group()
                # Nettoyer le numéro
                phone = re.sub(r'[^\d+]', '', phone)
                if len(phone) >= 10:
                    return phone
        
        return ""
    
    def _extract_best_website(self, html, association):
        """Extraire le meilleur site web"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Chercher liens dans les résultats
            links = soup.find_all('a', href=True)
            
            nom_words = association['nom'].lower().split()[:2]
            scored_websites = []
            
            for link in links:
                url = link.get('href', '')
                if not url.startswith('http'):
                    continue
                
                # Filtrer URLs non pertinentes
                if any(exclude in url.lower() for exclude in ['google.', 'bing.', 'qwant.', 'wikipedia.', 'facebook.com/tr']):
                    continue
                
                url_lower = url.lower()
                score = 0
                
                # Points pour nom association dans URL
                for word in nom_words:
                    if len(word) > 3 and word in url_lower:
                        score += 10
                
                # Points pour sites spécialisés associations
                if any(site in url_lower for site in self.association_sites):
                    score += 15
                
                # Points pour domaines français
                if '.fr' in url_lower:
                    score += 5
                
                if '.org' in url_lower:
                    score += 3
                
                if score > 5:
                    scored_websites.append((url, score))
            
            if scored_websites:
                best_website = sorted(scored_websites, key=lambda x: x[1], reverse=True)[0][0]
                return best_website
                
        except Exception as e:
            pass
        
        return ""
    
    def _extract_facebook(self, html, association):
        """Extraire page Facebook"""
        try:
            # Pattern Facebook
            fb_pattern = r'https://(?:www\.)?facebook\.com/[^/\s"<>]+'
            matches = re.findall(fb_pattern, html)
            
            if matches:
                # Prendre la première page Facebook trouvée
                return matches[0]
                
        except Exception as e:
            pass
        
        return ""
    
    def _search_specialized_sites(self, nom, ville):
        """Recherche directe sur sites spécialisés"""
        contacts = {
            'email_principal': '',
            'telephone': '',
            'site_web': '',
            'search_success': False
        }
        
        try:
            # Recherche HelloAsso
            helloasso_result = self._search_helloasso_direct(nom, ville)
            if helloasso_result:
                contacts.update(helloasso_result)
                contacts['search_success'] = True
                return contacts
            
            # Recherche Net1901
            net1901_result = self._search_net1901_direct(nom, ville)
            if net1901_result:
                contacts.update(net1901_result)
                contacts['search_success'] = True
                return contacts
                
        except Exception as e:
            pass
        
        return contacts
    
    def _search_helloasso_direct(self, nom, ville):
        """Recherche directe HelloAsso"""
        try:
            # Construire URL recherche HelloAsso
            query = f"{nom} {ville}"
            url = f"https://www.helloasso.com/associations/recherche?q={quote_plus(query)}"
            
            headers = {'User-Agent': random.choice(self.user_agents)}
            response = self.session.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Chercher première association correspondante
                asso_links = soup.find_all('a', href=re.compile(r'/associations/[^/]+$'))
                
                if asso_links:
                    # Suivre le premier lien
                    detail_url = urljoin("https://www.helloasso.com", asso_links[0].get('href'))
                    detail_response = self.session.get(detail_url, headers=headers, timeout=10)
                    
                    if detail_response.status_code == 200:
                        detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                        detail_text = detail_soup.get_text()
                        
                        # Extraire contacts de la page de détail
                        email = self._extract_email_from_text(detail_text)
                        phone = self._extract_phone(detail_text)
                        
                        if email or phone:
                            return {
                                'email_principal': email,
                                'telephone': phone,
                                'site_web': detail_url
                            }
            
        except Exception as e:
            pass
        
        return None
    
    def _search_net1901_direct(self, nom, ville):
        """Recherche directe Net1901"""
        try:
            # Net1901 a une structure différente, recherche simplifiée
            query = f"{nom} {ville}"
            url = f"https://www.net1901.org/recherche?q={quote_plus(query)}"
            
            headers = {'User-Agent': random.choice(self.user_agents)}
            response = self.session.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text()
                
                # Extraire contacts
                email = self._extract_email_from_text(text)
                phone = self._extract_phone(text)
                
                if email or phone:
                    return {
                        'email_principal': email,
                        'telephone': phone,
                        'site_web': url
                    }
            
        except Exception as e:
            pass
        
        return None
    
    def _extract_email_from_text(self, text):
        """Extraire email depuis texte simple"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        for email in emails:
            if self._is_valid_email_format(email):
                return email.lower()
        
        return ""
    
    def _is_valid_email_format(self, email):
        """Vérifier format email valide"""
        if not email or len(email) < 5 or '@' not in email:
            return False
        
        # Filtrer emails invalides
        invalid_patterns = [
            'noreply', 'no-reply', 'donotreply', 'webmaster@example',
            'test@', '@test.', 'admin@localhost', 'contact@google',
            'info@facebook', '@...', '...@'
        ]
        
        email_lower = email.lower()
        return not any(pattern in email_lower for pattern in invalid_patterns)
    
    def process_rna_contacts(self, filepath, max_associations=100, start_index=0):
        """Traitement complet recherche contacts RNA"""
        print("🎯 RECHERCHE CONTACTS ASSOCIATIONS RNA")
        print("=" * 60)
        print("📋 Source: Associations RNA officielles")
        print("🔍 Méthodes: Google + Qwant + Bing + Sites spécialisés")
        print("📧 Objectif: Emails et contacts réels")
        
        # Charger associations
        associations = self.load_rna_associations(filepath)
        if not associations:
            return []
        
        # Sélectionner plage à traiter
        total_associations = len(associations)
        end_index = min(start_index + max_associations, total_associations)
        
        associations_to_process = associations[start_index:end_index]
        
        print(f"\n📊 TRAITEMENT:")
        print(f"  • Total RNA: {total_associations}")
        print(f"  • Index de départ: {start_index}")
        print(f"  • À traiter: {len(associations_to_process)}")
        print(f"  • Index fin: {end_index}")
        
        # Traitement avec recherche
        updated_associations = []
        found_contacts = 0
        
        for i, association in enumerate(associations_to_process):
            try:
                print(f"\n{start_index + i + 1}/{total_associations} - ", end="")
                
                # Rechercher contacts
                contacts = self.search_association_contacts(association)
                
                # Mettre à jour association
                association.update(contacts)
                
                if contacts.get('email_principal') or contacts.get('site_web'):
                    found_contacts += 1
                    print(f"  ✅ Contacts trouvés!")
                else:
                    print(f"  ⚠️ Aucun contact")
                
                updated_associations.append(association)
                
                # Délais pour éviter blocage
                if i % 5 == 0 and i > 0:
                    print(f"  ⏳ Pause courte...")
                    time.sleep(3)
                else:
                    time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                print(f"  ❌ Erreur: {e}")
                updated_associations.append(association)
        
        # Sauvegarder résultats
        if updated_associations:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"rna_with_contacts_{start_index}_{end_index}_{timestamp}.csv"
            
            self.data_manager.save_to_csv(updated_associations, filename)
            
            # Statistiques
            success_rate = (found_contacts / len(updated_associations) * 100) if updated_associations else 0
            
            print(f"\n🎉 RECHERCHE TERMINÉE")
            print(f"📁 Fichier: data/{filename}")
            print(f"📊 Traités: {len(updated_associations)}")
            print(f"📧 Contacts trouvés: {found_contacts}")
            print(f"📈 Taux de succès: {success_rate:.1f}%")
            
            # Exemples de contacts trouvés
            examples = [a for a in updated_associations if a.get('email_principal')][:3]
            if examples:
                print(f"\n💼 EXEMPLES TROUVÉS:")
                for ex in examples:
                    print(f"  • {ex['nom'][:30]}... → {ex['email_principal']}")
            
            return updated_associations
        
        return []

def main():
    """Fonction principale"""
    scraper = RnaContactScraper()
    
    print("🎯 RECHERCHE CONTACTS RNA")
    print("=" * 60)
    print("📋 654 associations RNA du département 01")
    print("🔍 Recherche intelligente par nom + ville")
    print("📧 Extraction emails réels")
    
    # Paramètres
    filepath = "data/rna_associations_processed_20250713_1548.csv"
    
    print(f"\n❓ Paramètres de recherche:")
    print(f"Nombre d'associations à traiter (max 100): ", end="")
    max_assocs = int(input().strip() or "50")
    
    print(f"Index de départ (0 pour début): ", end="")
    start_idx = int(input().strip() or "0")
    
    print(f"\n🚀 Lancement recherche...")
    associations = scraper.process_rna_contacts(filepath, max_assocs, start_idx)
    
    if associations:
        contacts_found = sum(1 for a in associations if a.get('email_principal'))
        print(f"\n🎉 SUCCÈS ! {contacts_found} contacts trouvés sur {len(associations)} associations")
    else:
        print(f"\n😞 Aucun résultat")

if __name__ == "__main__":
    main()
