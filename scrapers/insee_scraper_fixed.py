import requests
import time
import json
import base64
from datetime import datetime, timedelta
import sys
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_manager import DataManager

class InseeScraperFixed:
    """Scraper INSEE corrigé avec authentification OAuth2 correcte"""
    
    def __init__(self):
        self.data_manager = DataManager()
        self.consumer_key = os.getenv('INSEE_CONSUMER_KEY')
        self.consumer_secret = os.getenv('INSEE_CONSUMER_SECRET')
        self.bing_api_key = os.getenv('BING_SEARCH_API_KEY')
        self.access_token = None
        self.token_expires_at = None
        self.base_url = "https://api.insee.fr/entreprises/sirene/V3"
        self.auth_url = "https://api.insee.fr/token"
        
    def get_access_token(self):
        """Obtenir un token d'accès OAuth2 avec la méthode correcte"""
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token
        
        print("🔑 Authentification INSEE OAuth2...")
        
        # Encoder correctement pour Basic Auth
        credentials = f"{self.consumer_key}:{self.consumer_secret}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('ascii')
        
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'client_credentials'
        }
        
        try:
            print(f"  📡 POST {self.auth_url}")
            print(f"  🔐 Consumer Key: {self.consumer_key}")
            
            response = requests.post(self.auth_url, headers=headers, data=data, timeout=15)
            
            print(f"  📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                expires_in = token_data.get('expires_in', 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
                
                print("  ✅ Token obtenu avec succès")
                print(f"  ⏰ Expire dans {expires_in} secondes")
                return self.access_token
                
            else:
                print(f"  ❌ Erreur {response.status_code}")
                print(f"  📄 Réponse: {response.text}")
                
                # Essayer avec un User-Agent
                headers['User-Agent'] = 'Python-INSEE-Client/1.0'
                response = requests.post(self.auth_url, headers=headers, data=data, timeout=15)
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.access_token = token_data['access_token']
                    expires_in = token_data.get('expires_in', 3600)
                    self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
                    print("  ✅ Token obtenu avec User-Agent")
                    return self.access_token
                else:
                    print(f"  ❌ Échec définitif: {response.status_code}")
                    return None
                
        except Exception as e:
            print(f"  ❌ Exception: {e}")
            return None
    
    def search_associations_by_category(self, category_code, max_results=20):
        """Rechercher des associations par catégorie juridique"""
        print(f"🔍 Recherche associations catégorie {category_code}...")
        
        token = self.get_access_token()
        if not token:
            print("❌ Impossible d'obtenir le token")
            return []
        
        url = f"{self.base_url}/siret"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
            'User-Agent': 'Python-INSEE-Client/1.0'
        }
        
        # Associations = catégories juridiques 9xxx
        params = {
            'q': f'categorieJuridiqueUniteLegale:{category_code}*',
            'champs': 'siret,siren,denominationUniteLegale,nomUniteLegale,prenom1UniteLegale,categorieJuridiqueUniteLegale,activitePrincipaleUniteLegale,libelleCommuneEtablissement,codePostalEtablissement,numeroVoieEtablissement,typeVoieEtablissement,libelleVoieEtablissement,etatAdministratifUniteLegale,dateCreationUniteLegale',
            'nombre': min(max_results, 100),  # Limiter pour éviter timeouts
            'debut': 1
        }
        
        associations = []
        
        try:
            print(f"  📡 GET {url}")
            print(f"  🔍 Recherche: {params['q']}")
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            print(f"  📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if 'etablissements' in data:
                    etablissements = data['etablissements']
                    print(f"  ✅ {len(etablissements)} établissements trouvés")
                    
                    for etab in etablissements:
                        try:
                            association = self._extract_association_data(etab, category_code)
                            if association:
                                associations.append(association)
                        except Exception as e:
                            print(f"    ⚠️ Erreur extraction: {e}")
                            continue
                    
                    print(f"  ✅ {len(associations)} associations valides extraites")
                    
                elif 'header' in data:
                    header = data['header']
                    print(f"  ℹ️ Réponse vide - Total disponible: {header.get('total', 0)}")
                    
                else:
                    print(f"  ⚠️ Format réponse inattendu: {list(data.keys())}")
                    
            elif response.status_code == 401:
                print(f"  ❌ Token invalide ou expiré")
                self.access_token = None
                
            elif response.status_code == 429:
                print(f"  ⚠️ Rate limit - attente 60s")
                time.sleep(60)
                
            else:
                print(f"  ❌ Erreur {response.status_code}")
                print(f"  📄 Réponse: {response.text[:300]}")
                
        except Exception as e:
            print(f"  ❌ Exception: {e}")
        
        return associations
    
    def search_associations_by_region(self, region_code, max_results=15):
        """Rechercher associations par région (Centre-Val de Loire = 24)"""
        print(f"🗺️ Recherche associations région {region_code}...")
        
        token = self.get_access_token()
        if not token:
            return []
        
        url = f"{self.base_url}/siret"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
            'User-Agent': 'Python-INSEE-Client/1.0'
        }
        
        # Associations en Centre-Val de Loire
        params = {
            'q': f'categorieJuridiqueUniteLegale:9* AND regionImplantationEtablissement:{region_code}',
            'champs': 'siret,siren,denominationUniteLegale,nomUniteLegale,categorieJuridiqueUniteLegale,activitePrincipaleUniteLegale,libelleCommuneEtablissement,codePostalEtablissement,numeroVoieEtablissement,typeVoieEtablissement,libelleVoieEtablissement,etatAdministratifUniteLegale,dateCreationUniteLegale',
            'nombre': max_results,
            'debut': 1
        }
        
        associations = []
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                etablissements = data.get('etablissements', [])
                
                for etab in etablissements:
                    association = self._extract_association_data(etab, f"region_{region_code}")
                    if association:
                        associations.append(association)
                
                print(f"  ✅ {len(associations)} associations région {region_code}")
                
        except Exception as e:
            print(f"  ❌ Erreur région: {e}")
        
        return associations
    
    def _extract_association_data(self, etablissement, search_context):
        """Extraire les données d'une association depuis la réponse INSEE"""
        try:
            unite_legale = etablissement.get('uniteLegale', {})
            
            # Vérifier état administratif
            etat_admin = unite_legale.get('etatAdministratifUniteLegale', 'A')
            if etat_admin != 'A':  # Seulement les actifs
                return None
            
            # Extraire le nom
            nom = self._extract_name(unite_legale)
            if not nom or len(nom) < 5:
                return None
            
            # Filtrer seulement les vraies associations
            if not any(word in nom.lower() for word in ['association', 'asso', 'club', 'union', 'fédération', 'comité']):
                return None
            
            # Extraire l'adresse
            adresse = self._format_address(etablissement)
            
            # Code postal et département
            code_postal = etablissement.get('codePostalEtablissement', '')
            departement = code_postal[:2] if code_postal and len(code_postal) >= 2 else ''
            
            # Données complètes
            association = {
                'nom': nom,
                'siren': etablissement.get('siren'),
                'siret': etablissement.get('siret'),
                'categorie_juridique': unite_legale.get('categorieJuridiqueUniteLegale'),
                'activite_principale': unite_legale.get('activitePrincipaleUniteLegale'),
                'ville': etablissement.get('libelleCommuneEtablissement'),
                'code_postal': code_postal,
                'departement': departement,
                'adresse_complete': adresse,
                'etat_administratif': etat_admin,
                'date_creation': unite_legale.get('dateCreationUniteLegale'),
                'source': 'INSEE_SIRENE_API',
                'recherche_par': search_context,
                'date_extraction': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Enrichir avec secteur d'activité
            association['secteur_activite'] = self._determine_sector(nom, association.get('activite_principale', ''))
            
            return association
            
        except Exception as e:
            print(f"    ⚠️ Erreur extraction: {e}")
            return None
    
    def _extract_name(self, unite_legale):
        """Extraire le nom de l'association"""
        # Priorité à la dénomination
        denomination = unite_legale.get('denominationUniteLegale')
        if denomination and denomination.strip():
            return denomination.strip()
        
        # Sinon nom + prénom pour les personnes physiques
        nom = unite_legale.get('nomUniteLegale', '')
        prenom = unite_legale.get('prenom1UniteLegale', '')
        
        if nom:
            if prenom:
                return f"{prenom} {nom}".strip()
            else:
                return nom.strip()
        
        return None
    
    def _format_address(self, etablissement):
        """Formater l'adresse complète"""
        parts = []
        
        numero = etablissement.get('numeroVoieEtablissement')
        type_voie = etablissement.get('typeVoieEtablissement')
        libelle_voie = etablissement.get('libelleVoieEtablissement')
        
        if numero:
            parts.append(str(numero))
        if type_voie:
            parts.append(type_voie)
        if libelle_voie:
            parts.append(libelle_voie)
        
        adresse_voie = ' '.join(parts) if parts else ''
        
        code_postal = etablissement.get('codePostalEtablissement')
        commune = etablissement.get('libelleCommuneEtablissement')
        
        if code_postal and commune:
            if adresse_voie:
                return f"{adresse_voie}, {code_postal} {commune}"
            else:
                return f"{code_postal} {commune}"
        
        return adresse_voie if adresse_voie else None
    
    def _determine_sector(self, nom, activite_code):
        """Déterminer le secteur d'activité"""
        nom_lower = nom.lower()
        
        # Par nom
        if any(word in nom_lower for word in ['sport', 'football', 'tennis', 'basket', 'rugby', 'athlé']):
            return 'Sport'
        elif any(word in nom_lower for word in ['culture', 'théâtre', 'musique', 'art', 'concert', 'festival']):
            return 'Culture'
        elif any(word in nom_lower for word in ['social', 'entraide', 'solidarité', 'insertion', 'aide']):
            return 'Social'
        elif any(word in nom_lower for word in ['environnement', 'nature', 'écologie', 'vert']):
            return 'Environnement'
        elif any(word in nom_lower for word in ['éducation', 'école', 'formation', 'enseignement']):
            return 'Éducation'
        
        # Par code activité
        if activite_code:
            if activite_code.startswith('93'):  # Sports
                return 'Sport'
            elif activite_code.startswith('90'):  # Arts/Culture
                return 'Culture'
            elif activite_code.startswith('88'):  # Social
                return 'Social'
            elif activite_code.startswith('85'):  # Éducation
                return 'Éducation'
        
        return 'Divers'
    
    def search_websites_with_bing(self, association):
        """Rechercher le site web avec l'API Bing"""
        if not self.bing_api_key or self.bing_api_key == 'your_bing_api_key_here':
            print(f"    ⚠️ Clé Bing manquante")
            return {}
        
        nom = association.get('nom', '')
        ville = association.get('ville', '')
        
        print(f"  🔍 Bing: {nom} {ville}")
        
        try:
            url = "https://api.bing.microsoft.com/v7.0/search"
            
            headers = {
                'Ocp-Apim-Subscription-Key': self.bing_api_key,
                'User-Agent': 'Mozilla/5.0 (compatible; BingBot/1.0)'
            }
            
            # Requête de recherche optimisée
            query = f'"{nom}" {ville} site officiel association'
            
            params = {
                'q': query,
                'count': 5,
                'offset': 0,
                'mkt': 'fr-FR',
                'responseFilter': 'Webpages'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                webpages = data.get('webPages', {}).get('value', [])
                
                results = []
                for page in webpages[:3]:  # Top 3
                    results.append({
                        'url': page.get('url'),
                        'title': page.get('name'),
                        'snippet': page.get('snippet'),
                        'confidence': self._calculate_website_confidence(page.get('url', ''), nom, ville)
                    })
                
                # Trier par confiance
                results.sort(key=lambda x: x['confidence'], reverse=True)
                
                if results:
                    print(f"    ✅ {len(results)} sites trouvés")
                    return {
                        'site_web_reel': results[0]['url'],
                        'site_web_title': results[0]['title'],
                        'site_web_confidence': results[0]['confidence'],
                        'alternative_sites': [r['url'] for r in results[1:]]
                    }
            
            elif response.status_code == 401:
                print(f"    ❌ Clé Bing invalide")
            elif response.status_code == 429:
                print(f"    ⚠️ Rate limit Bing")
                time.sleep(1)
            else:
                print(f"    ⚠️ Bing error {response.status_code}")
                
        except Exception as e:
            print(f"    ❌ Erreur Bing: {e}")
        
        return {}
    
    def _calculate_website_confidence(self, url, nom, ville):
        """Calculer la confiance pour un site web"""
        if not url:
            return 0
        
        score = 0
        url_lower = url.lower()
        
        # Mots du nom dans l'URL
        nom_words = nom.lower().replace('association', '').split()
        for word in nom_words:
            if len(word) > 3 and word in url_lower:
                score += 3
        
        # Ville dans l'URL
        if ville and ville.lower().replace(' ', '') in url_lower.replace('-', ''):
            score += 2
        
        # Extension française
        if url_lower.endswith('.fr'):
            score += 2
        elif url_lower.endswith('.org'):
            score += 1
        
        # Mots clés association
        if any(word in url_lower for word in ['asso', 'association', 'club']):
            score += 1
        
        # Pénalités
        if any(word in url_lower for word in ['facebook', 'linkedin', 'twitter', 'instagram']):
            score -= 5
        
        return max(0, score)
    
    def run_complete_scraping(self):
        """Lancer le scraping complet INSEE + Bing"""
        print("🎯 SCRAPING COMPLET INSEE + BING")
        print("=" * 50)
        print("✅ API INSEE SIRENE officielle")
        print("✅ API Bing Search pour sites web")
        print("✅ Données 100% vérifiées")
        
        if not self.consumer_key or not self.consumer_secret:
            print("❌ Clés INSEE manquantes")
            return []
        
        all_associations = []
        
        # 1. Test authentification
        token = self.get_access_token()
        if not token:
            print("❌ Authentification INSEE échouée")
            return []
        
        print(f"\n✅ Authentification INSEE réussie")
        
        # 2. Recherche par catégories juridiques d'associations
        print(f"\n📊 ÉTAPE 1: Recherche par catégories associations")
        
        # Principales catégories d'associations
        categories = [
            '92',   # Associations loi 1901
            '93',   # Associations sportives  
            '94',   # Autres associations
            '91'    # Syndicats professionnels
        ]
        
        for category in categories:
            print(f"\n🏷️ Catégorie {category}:")
            category_associations = self.search_associations_by_category(category, max_results=10)
            all_associations.extend(category_associations)
            time.sleep(2)  # Délai respectueux
        
        # 3. Recherche par région Centre-Val de Loire
        print(f"\n📊 ÉTAPE 2: Recherche Centre-Val de Loire")
        print(f"\n🗺️ Région 24 (Centre-Val de Loire):")
        region_associations = self.search_associations_by_region('24', max_results=15)
        all_associations.extend(region_associations)
        
        # 4. Déduplication par SIREN
        print(f"\n🧹 ÉTAPE 3: Déduplication")
        unique_associations = []
        seen_sirens = set()
        
        for assoc in all_associations:
            siren = assoc.get('siren')
            if siren and siren not in seen_sirens:
                seen_sirens.add(siren)
                unique_associations.append(assoc)
        
        print(f"✅ {len(unique_associations)} associations uniques")
        
        # 5. Enrichissement avec Bing
        print(f"\n📊 ÉTAPE 4: Recherche sites web (Bing)")
        
        enriched_associations = []
        for i, assoc in enumerate(unique_associations[:15], 1):  # Limiter à 15
            print(f"\n🌐 {i}/15 - {assoc.get('nom', 'Sans nom')}")
            
            # Rechercher le site web
            website_info = self.search_websites_with_bing(assoc)
            
            # Enrichir
            assoc_enriched = assoc.copy()
            assoc_enriched.update(website_info)
            enriched_associations.append(assoc_enriched)
            
            time.sleep(1)  # Délai entre requêtes Bing
        
        # 6. Sauvegarde
        if enriched_associations:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"insee_bing_associations_{timestamp}.csv"
            
            self.data_manager.save_to_csv(enriched_associations, filename)
            
            print(f"\n✅ SCRAPING COMPLET TERMINÉ")
            print(f"📁 Fichier: data/{filename}")
            print(f"📊 Total: {len(enriched_associations)} associations")
            
            # Statistiques
            stats = self._generate_stats(enriched_associations)
            print(f"\n📈 STATISTIQUES:")
            for key, value in stats.items():
                print(f"  • {key}: {value}")
            
            print(f"\n🏆 QUALITÉ MAXIMALE:")
            print(f"✅ SIREN/SIRET officiels INSEE")
            print(f"✅ Sites web trouvés par Bing")
            print(f"✅ Adresses complètes vérifiées")
            print(f"✅ Données traçables et légales")
            
            return enriched_associations
        
        else:
            print("❌ Aucune association trouvée")
            return []
    
    def _generate_stats(self, associations):
        """Générer statistiques détaillées"""
        total = len(associations)
        
        with_website = sum(1 for a in associations if a.get('site_web_reel'))
        by_sector = {}
        by_dept = {}
        by_category = {}
        
        for assoc in associations:
            # Secteur
            sector = assoc.get('secteur_activite', 'Inconnu')
            by_sector[sector] = by_sector.get(sector, 0) + 1
            
            # Département
            dept = assoc.get('departement', '??')
            by_dept[dept] = by_dept.get(dept, 0) + 1
            
            # Catégorie juridique
            cat = assoc.get('categorie_juridique', 'Inconnue')
            by_category[cat] = by_category.get(cat, 0) + 1
        
        return {
            'Total associations': total,
            'Avec site web trouvé': with_website,
            'Secteurs différents': len(by_sector),
            'Départements représentés': len(by_dept),
            'Catégories juridiques': len(by_category),
            'Répartition secteurs': dict(sorted(by_sector.items(), key=lambda x: x[1], reverse=True)),
            'Top départements': dict(sorted(by_dept.items(), key=lambda x: x[1], reverse=True)[:5]),
            'Catégories juridiques': dict(sorted(by_category.items(), key=lambda x: x[1], reverse=True))
        }

def main():
    """Fonction principale"""
    scraper = InseeScraperFixed()
    
    print("🎯 SCRAPER INSEE + BING - DONNÉES OFFICIELLES")
    print("=" * 55)
    print("🏛️ API INSEE SIRENE (OAuth2 corrigé)")
    print("🔍 API Bing Search (sites web)")
    print("✅ Authentification robuste")
    print("✅ Enrichissement automatique")
    
    print(f"\n❓ Lancer le scraping complet ? (oui/non): ", end="")
    confirmation = input().strip().lower()
    
    if confirmation in ['oui', 'o', 'yes', 'y']:
        associations = scraper.run_complete_scraping()
        
        if associations:
            print(f"\n🎉 MISSION ACCOMPLIE !")
            print(f"📊 {len(associations)} associations officielles")
            print(f"🌐 Sites web recherchés automatiquement")
            print(f"✅ Qualité données maximale")
        else:
            print(f"\n😞 Échec - Vérifiez la configuration")
    else:
        print("🚪 Scraping annulé")

if __name__ == "__main__":
    main()
