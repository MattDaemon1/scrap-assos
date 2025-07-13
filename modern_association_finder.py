#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMART CONTACT FINDER - ASSOCIATIONS MODERNES (2000+)
Version qui se concentre sur les associations créées après 2000

Stratégie:
- Associations créées après 2000 = plus de présence en ligne
- Meilleur taux de succès attendu
- Contacts plus fiables et actifs
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
import random
from datetime import datetime
import os
from urllib.parse import quote
import unicodedata

class ModernAssociationFinder:
    def __init__(self):
        self.session = requests.Session()
        self.setup_session()
        self.base_delay = 1.0
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
        
    def setup_session(self):
        """Configuration sécurisée de la session"""
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def parse_date(self, date_str):
        """Parse les différents formats de date"""
        if not date_str or date_str == "0001-01-01":
            return None
            
        try:
            # Format MM/DD/YYYY
            if '/' in date_str:
                return datetime.strptime(date_str, '%m/%d/%Y')
            # Format YYYY-MM-DD
            elif '-' in date_str:
                return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            pass
            
        return None
        
    def is_modern_association(self, row):
        """Filtre pour les associations modernes (2000+)"""
        date_publi = row.get('date_publi', '')
        titre = row.get('titre', '')
        
        # Ignorer les associations avec des titres problématiques
        titre_upper = titre.upper()
        problematic_keywords = [
            'ERREUR', 'VOIR NUMERO', 'VOIR -', 'VOIR N°', 'DISSOLUTION',
            'DISSOUTE', 'FUSION', 'TRANSFERT', 'ASSOCIATION DISSOUTE'
        ]
        
        for keyword in problematic_keywords:
            if keyword in titre_upper:
                return False
                
        # Vérifier la date
        parsed_date = self.parse_date(date_publi)
        if parsed_date and parsed_date.year >= 1990:
            return True
            
        return False
        
    def clean_association_name(self, nom):
        """Nettoie le nom de l'association pour la recherche"""
        if not nom:
            return ""
            
        # Supprimer les accents
        nom = unicodedata.normalize('NFD', nom).encode('ascii', 'ignore').decode('utf-8')
        
        # Nettoyer les caractères spéciaux
        nom = re.sub(r'[^\w\s-]', ' ', nom)
        
        # Supprimer les mots génériques inutiles pour la recherche
        mots_a_supprimer = [
            'association', 'societe', 'amicale', 'comite', 'club', 'syndicat',
            'groupement', 'federation', 'union', 'cercle'
        ]
        
        mots = nom.split()
        mots_filtres = []
        for mot in mots:
            if mot.lower() not in mots_a_supprimer and len(mot) > 2:
                mots_filtres.append(mot)
                
        return ' '.join(mots_filtres).strip()
        
    def generate_modern_queries(self, nom, ville):
        """Génère des requêtes adaptées aux associations modernes"""
        nom_clean = self.clean_association_name(nom)
        queries = []
        
        if not nom_clean or not ville:
            return queries
            
        ville_clean = ville.replace('-', ' ')
        
        # Requêtes modernes (plus de chances d'avoir sites web/réseaux sociaux)
        queries.extend([
            f'"{nom_clean}" {ville_clean} email contact',
            f'"{nom_clean}" {ville_clean} site web',
            f'"{nom_clean}" {ville_clean} facebook',
            f'"{nom_clean}" {ville_clean} association contact',
            f'{nom_clean} {ville_clean} "@" email',
            f'association "{nom_clean}" {ville_clean} contact',
            f'{nom_clean} {ville_clean} president secretaire',
            f'"{nom_clean}" {ville_clean} site:facebook.com',
        ])
        
        # Recherches sur sites officiels locaux
        ville_slug = ville_clean.lower().replace(' ', '-')
        queries.extend([
            f'site:mairie-{ville_slug}.fr "{nom_clean}"',
            f'site:{ville_slug}.fr "{nom_clean}"',
            f'site:cc-{ville_slug}.fr "{nom_clean}"'
        ])
        
        return queries[:10]  # Limiter à 10 requêtes max
        
    def search_engine_request(self, query, engine="google"):
        """Effectue une recherche sur un moteur donné"""
        try:
            # Rotation des user agents
            self.session.headers['User-Agent'] = random.choice(self.user_agents)
            
            if engine == "google":
                url = f"https://www.google.com/search?q={quote(query)}&num=15"
            elif engine == "bing":
                url = f"https://www.bing.com/search?q={quote(query)}&count=15"
            else:
                return None
                
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return response.text
                
        except Exception as e:
            print(f"        ❌ Erreur {engine}: {str(e)[:50]}...")
            
        return None
        
    def extract_emails(self, html_content):
        """Extrait les emails du contenu HTML"""
        if not html_content:
            return []
            
        # Pattern email amélioré
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, html_content)
        
        # Filtrer les emails valides
        valid_emails = []
        for email in emails:
            email = email.lower().strip()
            
            # Ignorer les emails génériques/spam
            spam_keywords = [
                'noreply', 'no-reply', 'donotreply', 'exemple', 'example', 
                'test', 'googleads', 'doubleclick', 'facebook', 'google-analytics',
                'google.com', 'youtube.com', 'twitter.com'
            ]
            
            if any(spam in email for spam in spam_keywords):
                continue
                
            if email not in valid_emails:
                valid_emails.append(email)
                
        return valid_emails
        
    def score_email(self, email, nom_association, ville):
        """Score un email selon sa pertinence"""
        score = 0
        email_lower = email.lower()
        nom_lower = nom_association.lower()
        ville_lower = ville.lower()
        
        # Score basé sur le domaine
        domain = email.split('@')[1]
        
        # Domaines officiels/municipaux (score élevé)
        if any(x in domain for x in ['mairie', 'ville', 'commune', 'cc-', ville_lower.replace(' ', '-')]):
            score += 40
            
        # Domaines associatifs
        if any(x in domain for x in ['asso', 'association', 'club', 'org']):
            score += 35
            
        # Domaines professionnels
        if domain.endswith(('.fr', '.org', '.net')):
            score += 20
        elif domain.endswith('.com'):
            score += 15
            
        # Correspondance avec le nom de l'association
        nom_mots = [mot for mot in nom_lower.split() if len(mot) > 3]
        for mot in nom_mots:
            if mot in email_lower:
                score += 25
                
        # Correspondance avec la ville
        ville_clean = ville_lower.replace('-', '').replace(' ', '')
        if ville_clean in domain:
            score += 20
            
        # Types d'emails prioritaires
        priority_keywords = ['contact', 'info', 'secretaire', 'president', 'bureau']
        for keyword in priority_keywords:
            if keyword in email_lower:
                score += 15
                
        return score
        
    def search_mairie_email(self, ville):
        """Recherche l'email de la mairie comme fallback"""
        print(f"        🏛️ Recherche email mairie de {ville}...")
        
        ville_clean = ville.replace('-', ' ').lower()
        
        # Requêtes pour trouver l'email de la mairie
        mairie_queries = [
            f'mairie {ville} email contact',
            f'mairie {ville_clean} "@"',
            f'site:mairie-{ville_clean.replace(" ", "-")}.fr contact',
            f'"{ville}" mairie email',
            f'mairie {ville} contact "@"'
        ]
        
        all_emails = []
        
        for query in mairie_queries[:3]:  # Limiter à 3 requêtes pour la mairie
            for engine in ['google', 'bing']:
                print(f"          📧 {engine.title()}: {query[:50]}...")
                
                html = self.search_engine_request(query, engine)
                if html:
                    emails = self.extract_emails(html)
                    all_emails.extend(emails)
                    
                time.sleep(self.base_delay + random.uniform(0.2, 0.8))
                
        # Filtrer et scorer les emails de mairie
        mairie_emails = []
        for email in set(all_emails):
            email_lower = email.lower()
            domain = email.split('@')[1].lower()
            
            # Prioriser les emails officiels de mairie
            if any(keyword in domain for keyword in ['mairie', 'ville', 'commune']) or \
               any(keyword in domain for keyword in [ville_clean.replace(' ', ''), ville_clean.replace(' ', '-')]):
                mairie_emails.append((email, 100))  # Score max pour emails officiels
            elif any(keyword in email_lower for keyword in ['mairie', 'secretariat', 'accueil']):
                mairie_emails.append((email, 80))
            elif domain.endswith('.fr'):
                mairie_emails.append((email, 60))
                
        if mairie_emails:
            # Trier par score et prendre le meilleur
            mairie_emails.sort(key=lambda x: x[1], reverse=True)
            best_mairie_email = mairie_emails[0][0]
            print(f"        🏛️ Email mairie trouvé: {best_mairie_email}")
            return best_mairie_email
            
        return None

    def smart_search_contact(self, nom, ville, date_creation):
        """Recherche intelligente d'un contact pour association moderne"""
        print(f"    🔍 {nom[:40]}... ({date_creation}) à {ville}")
        
        all_emails = []
        queries = self.generate_modern_queries(nom, ville)
        
        for i, query in enumerate(queries):
            # Alterner entre moteurs
            engine = 'google' if i % 2 == 0 else 'bing'
            print(f"        📡 {engine.title()}: {query[:55]}...")
            
            html = self.search_engine_request(query, engine)
            if html:
                emails = self.extract_emails(html)
                all_emails.extend(emails)
                
                # Si on trouve des emails rapidement, on peut réduire les recherches
                if len(set(all_emails)) >= 3:
                    break
                    
            # Délai anti-détection adaptatif
            delay = self.base_delay + random.uniform(0.3, 1.0)
            time.sleep(delay)
            
        # Déduplication et scoring
        unique_emails = list(set(all_emails))
        if unique_emails:
            # Scorer et trier
            scored_emails = [(email, self.score_email(email, nom, ville)) for email in unique_emails]
            scored_emails.sort(key=lambda x: x[1], reverse=True)
            
            # Prendre le meilleur email
            best_email, best_score = scored_emails[0]
            print(f"        ✅ Email association trouvé: {best_email} (score: {best_score})")
            return best_email, "Association"
        else:
            print(f"        ❌ Aucun email association trouvé")
            
            # Fallback: rechercher l'email de la mairie
            mairie_email = self.search_mairie_email(ville)
            if mairie_email:
                return mairie_email, "Mairie"
            else:
                print(f"        ❌ Aucun email mairie trouvé")
                return None, None
            
    def load_modern_associations(self, file_path):
        """Charge et filtre les associations modernes (2000+)"""
        print("📂 Chargement des données RNA...")
        df = pd.read_csv(file_path)
        
        initial_count = len(df)
        print(f"📊 {initial_count} associations dans le fichier")
        
        # Filtrer les associations modernes
        modern_associations = []
        for _, row in df.iterrows():
            if self.is_modern_association(row):
                modern_associations.append(row)
                
        df_modern = pd.DataFrame(modern_associations)
        
        modern_count = len(df_modern)
        print(f"✅ {modern_count} associations modernes (1990+)")
        print(f"🗑️ {initial_count - modern_count} associations anciennes filtrées")
        
        # Trier par date (plus récentes en premier)
        df_modern['date_parsed'] = df_modern['date_publi'].apply(self.parse_date)
        df_modern = df_modern.sort_values('date_parsed', ascending=False)
        
        return df_modern
        
    def run_modern_search(self, target_results=10, start_index=0, max_attempts=100):
        """Lance la recherche jusqu'à obtenir le nombre de résultats souhaité"""
        print("🎯 SMART CONTACT FINDER - ASSOCIATIONS MODERNES")
        print("=" * 65)
        print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print("📍 CIBLE: Associations créées après 1990")
        print(f"🎯 OBJECTIF: {target_results} contacts trouvés")
        print("💡 STRATÉGIE:")
        print("  ✅ Recherche continue jusqu'à atteindre l'objectif")
        print("  ✅ Associations récentes = meilleure présence en ligne")
        print("  ✅ Recherches adaptées aux pratiques modernes")
        print("  ✅ Fallback automatique sur email de la mairie")
        print("  ✅ Arrêt automatique une fois l'objectif atteint")
        
        # Charger et filtrer les données
        rna_file = "data/rna_import_20250701_dpt_01.csv"
        df = self.load_modern_associations(rna_file)
        
        if len(df) == 0:
            print("❌ Aucune association moderne trouvée")
            return []
            
        if start_index >= len(df):
            print(f"❌ Index {start_index} trop élevé (max: {len(df)-1})")
            return []
        
        print(f"📍 Index de départ: {start_index}")
        print(f"🎯 Objectif: {target_results} contacts")
        print(f"🔢 Maximum d'essais: {max_attempts}")
        print("🚀 Lancement recherche ciblée...")
        print("-" * 65)
        
        results = []
        found_count = 0
        attempts = 0
        current_index = start_index
        
        while found_count < target_results and attempts < max_attempts and current_index < len(df):
            attempts += 1
            row = df.iloc[current_index]
            
            nom = row['titre']
            ville = row['libcom']
            adresse = row.get('adr1', '')
            objet = row.get('objet', '')
            date_creation = row.get('date_publi', '')
            
            print(f"{attempts:4d}. Recherche: {found_count}/{target_results} trouvés - ", end="")
            
            email_result = self.smart_search_contact(nom, ville, date_creation)
            
            if email_result[0]:  # Si un email a été trouvé
                email, contact_type = email_result
                found_count += 1
                contact_data = {
                    'nom_association': nom,
                    'ville': ville,
                    'adresse': adresse,
                    'objet': objet,
                    'email': email,
                    'contact_type': contact_type,  # "Association" ou "Mairie"
                    'date_creation': date_creation,
                    'source': 'RNA_Modern',
                    'search_method': 'Modern_Smart_Search_With_Fallback',
                    'date_extraction': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'secteur': 'À analyser'
                }
                results.append(contact_data)
                
                print(f"        🎉 OBJECTIF: {found_count}/{target_results} atteint! ({contact_type})")
                
                # Sauvegarde incrémentale tous les 3 contacts
                if found_count % 3 == 0:
                    self.save_results(results, start_index, current_index, temp=True)
                    print(f"        💾 Sauvegarde: {found_count} contacts")
                
                # Vérifier si l'objectif est atteint
                if found_count >= target_results:
                    print(f"        ✅ OBJECTIF ATTEINT! {target_results} contacts trouvés")
                    break
                    
            current_index += 1
                    
        # Sauvegarde finale
        output_file = self.save_results(results, start_index, current_index)
        
        # Résumé
        print("\n🎉 RECHERCHE MODERNE TERMINÉE")
        print("=" * 50)
        print(f"📁 Fichier: {output_file}")
        print(f"✅ Objectif atteint: {found_count}/{target_results} contacts")
        print(f"📊 Associations testées: {attempts}")
        success_rate = (found_count / attempts) * 100 if attempts > 0 else 0
        print(f"� Taux de succès: {success_rate:.1f}%")
        
        if results:
            print("📧 EMAILS TROUVÉS:")
            for i, contact in enumerate(results, 1):
                contact_type_icon = "🏛️" if contact.get('contact_type') == 'Mairie' else "🏢"
                print(f"  {i}. {contact['email']} {contact_type_icon}")
                print(f"     {contact['nom_association'][:50]}...")
                print(f"     📍 {contact['ville']} ({contact['date_creation']})")
                print(f"     📝 Type: {contact.get('contact_type', 'Association')}")
                
        print("\n💡 PROCHAINES ÉTAPES:")
        print("  1. Fusionner avec contacts existants")
        print("  2. Exporter vers Brevo")
        
        if found_count < target_results and current_index < len(df):
            print(f"  3. Relancer pour plus de contacts (index {current_index})")
        elif found_count >= target_results:
            print("  3. ✅ Objectif atteint! Prêt pour la campagne")
            
        return results
        
    def save_results(self, results, start_idx, end_idx, temp=False):
        """Sauvegarde les résultats"""
        if not results:
            return None
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        suffix = "_temp" if temp else ""
        filename = f"modern_contacts{suffix}_{start_idx}_{end_idx}_{timestamp}.csv"
        filepath = os.path.join("data", filename)
        
        # Assurer que le dossier existe
        os.makedirs("data", exist_ok=True)
        
        df_results = pd.DataFrame(results)
        df_results.to_csv(filepath, index=False, encoding='utf-8')
        
        return filepath

if __name__ == "__main__":
    finder = ModernAssociationFinder()
    
    print("🏛️ Source: RNA Département 01 (associations modernes seulement)")
    print("📅 Critère: Créées après 1990")
    print("🔬 Méthode: Recherche ciblée par nombre de résultats")
    
    # Paramètres par défaut
    target = input("🎯 Nombre de contacts souhaités (défaut: 10): ").strip()
    target = int(target) if target else 10
    
    start = input("📍 Index de départ (défaut: 0): ").strip()
    start = int(start) if start else 0
    
    max_tries = input("🔢 Maximum d'essais (défaut: 50): ").strip()
    max_tries = int(max_tries) if max_tries else 50
    
    confirm = input(f"🚀 Rechercher {target} contacts modernes ? (oui/non): ").strip().lower()
    if confirm in ['oui', 'o', 'yes', 'y']:
        finder.run_modern_search(target, start, max_tries)
    else:
        print("❌ Recherche annulée")
