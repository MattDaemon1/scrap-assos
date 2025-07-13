#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMART CONTACT FINDER AVEC FILTRAGE INTELLIGENT
Version propre qui ignore les associations problématiques

Améliorations:
- Filtre les associations avec noms problématiques
- Priorise les associations actives avec de vrais noms
- Recherche plus ciblée et efficace
- Meilleur taux de succès attendu
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

class SmartContactFinderClean:
    def __init__(self):
        self.session = requests.Session()
        self.setup_session()
        self.base_delay = 1.5
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
        
    def is_valid_association(self, nom):
        """Filtre les associations problématiques"""
        nom_clean = nom.upper().strip()
        
        # Préfixes problématiques à ignorer
        problematic_prefixes = [
            'ERREUR D\'ENREGIST',
            'VOIR NUMERO',
            'VOIR -',
            'VOIR N°',
            'DISSOLUTION',
            'ASSOCIATION DISSOUTE',
            '(',
            'ERREUR D',
            'VOIR NRO',
            'TRANSFERT',
            'FUSION'
        ]
        
        # Vérifier les préfixes problématiques
        for prefix in problematic_prefixes:
            if nom_clean.startswith(prefix):
                return False
                
        # Ignorer les noms trop courts ou bizarres
        if len(nom_clean) < 3:
            return False
            
        # Ignorer les noms avec trop de caractères spéciaux
        special_chars = sum(1 for char in nom_clean if not char.isalnum() and char != ' ')
        if special_chars > len(nom_clean) * 0.3:
            return False
            
        return True
        
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
        
    def generate_search_queries(self, nom, ville):
        """Génère des requêtes de recherche intelligentes"""
        nom_clean = self.clean_association_name(nom)
        queries = []
        
        if not nom_clean or not ville:
            return queries
            
        ville_clean = ville.replace('-', ' ')
        
        # Requêtes de base avec email/contact
        queries.extend([
            f'"{nom_clean}" {ville_clean} email',
            f'"{nom_clean}" {ville_clean} contact',
            f'"{nom_clean}" {ville_clean} site',
            f'{nom_clean} {ville_clean} association email',
            f'{nom_clean} {ville_clean} association contact',
            f'{nom_clean} {ville_clean} secretaire',
            f'{nom_clean} {ville_clean} president'
        ])
        
        # Recherche sur les sites officiels
        queries.extend([
            f'site:mairie-{ville_clean.lower().replace(" ", "-")}.fr {nom_clean}',
            f'site:{ville_clean.lower().replace(" ", "-")}.fr {nom_clean}',
            f'site:cc-{ville_clean.lower().replace(" ", "-")}.fr {nom_clean}'
        ])
        
        return queries[:8]  # Limiter à 8 requêtes max
        
    def search_engine_request(self, query, engine="google"):
        """Effectue une recherche sur un moteur donné"""
        try:
            # Rotation des user agents
            self.session.headers['User-Agent'] = random.choice(self.user_agents)
            
            if engine == "google":
                url = f"https://www.google.com/search?q={quote(query)}&num=10"
            elif engine == "bing":
                url = f"https://www.bing.com/search?q={quote(query)}&count=10"
            else:
                return None
                
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return response.text
                
        except Exception as e:
            print(f"        ❌ Erreur {engine}: {e}")
            
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
            if any(spam in email for spam in ['noreply', 'no-reply', 'donotreply', 'exemple', 'example', 'test']):
                continue
                
            # Ignorer les domaines suspects
            if any(domain in email for domain in ['googleads', 'doubleclick', 'facebook', 'google-analytics']):
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
        
        # Domaines officiels/municipaux
        if any(x in domain for x in ['mairie', 'ville', 'commune', 'cc-', ville_lower.replace(' ', '-')]):
            score += 30
            
        # Domaines associatifs
        if any(x in domain for x in ['asso', 'association', 'club']):
            score += 25
            
        # Correspondance avec le nom de l'association
        nom_mots = nom_lower.split()
        for mot in nom_mots:
            if len(mot) > 3 and mot in email_lower:
                score += 20
                
        # Correspondance avec la ville
        if ville_lower.replace('-', '').replace(' ', '') in domain:
            score += 15
            
        # Types d'emails prioritaires
        if any(x in email_lower for x in ['contact', 'info', 'secretaire', 'president']):
            score += 10
            
        return score
        
    def smart_search_contact(self, nom, ville, index=0):
        """Recherche intelligente d'un contact"""
        print(f"    🔍 Recherche: {nom[:30]}... à {ville}")
        
        all_emails = []
        queries = self.generate_search_queries(nom, ville)
        
        for query in queries:
            for engine in ['google', 'bing']:
                print(f"        📡 {engine.title()}: {query[:60]}...")
                
                html = self.search_engine_request(query, engine)
                if html:
                    emails = self.extract_emails(html)
                    all_emails.extend(emails)
                    
                # Délai anti-détection
                time.sleep(self.base_delay + random.uniform(0.5, 1.5))
                
        # Déduplication et scoring
        unique_emails = list(set(all_emails))
        if unique_emails:
            # Scorer et trier
            scored_emails = [(email, self.score_email(email, nom, ville)) for email in unique_emails]
            scored_emails.sort(key=lambda x: x[1], reverse=True)
            
            best_email = scored_emails[0][0]
            print(f"        ✅ Email trouvé: {best_email}")
            return best_email
        else:
            print(f"        ❌ Aucun email trouvé")
            return None
            
    def load_rna_data(self, file_path):
        """Charge et filtre les données RNA"""
        print("📂 Chargement et filtrage des données RNA...")
        df = pd.read_csv(file_path)
        
        initial_count = len(df)
        print(f"📊 {initial_count} associations dans le fichier")
        
        # Filtrer les associations valides
        df_valid = df[df['titre'].apply(self.is_valid_association)].copy()
        
        valid_count = len(df_valid)
        filtered_count = initial_count - valid_count
        
        print(f"✅ {valid_count} associations valides")
        print(f"🗑️ {filtered_count} associations filtrées (erreurs, dissolutions, etc.)")
        
        return df_valid
        
    def run_smart_search(self, start_index=0, count=20):
        """Lance la recherche intelligente"""
        print("🎯 SMART CONTACT FINDER - VERSION PROPRE")
        print("=" * 60)
        print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print("🧹 AMÉLIORATIONS:")
        print("  ✅ Filtrage des associations problématiques")
        print("  ✅ Priorisation des associations actives")
        print("  ✅ Recherches ciblées et efficaces")
        print("  ✅ Meilleur taux de succès attendu")
        
        # Charger et filtrer les données
        rna_file = "data/rna_import_20250701_dpt_01.csv"
        df = self.load_rna_data(rna_file)
        
        if start_index >= len(df):
            print(f"❌ Index {start_index} trop élevé (max: {len(df)-1})")
            return
            
        end_index = min(start_index + count, len(df))
        associations_to_process = df.iloc[start_index:end_index]
        
        print(f"📍 Index de départ: {start_index}")
        print(f"🔢 Associations à traiter: {len(associations_to_process)}")
        print("🚀 Lancement recherche propre...")
        print("-" * 60)
        
        results = []
        found_count = 0
        
        for idx, (_, row) in enumerate(associations_to_process.iterrows(), 1):
            nom = row['titre']
            ville = row['libcom']
            adresse = row.get('adr1', '')
            objet = row.get('objet', '')
            
            print(f"{idx:4d}/{len(associations_to_process)} - {nom[:40]}...")
            
            email = self.smart_search_contact(nom, ville, start_index + idx - 1)
            
            if email:
                found_count += 1
                contact_data = {
                    'nom_association': nom,
                    'ville': ville,
                    'adresse': adresse,
                    'objet': objet,
                    'email': email,
                    'source': 'Smart_Search_Clean',
                    'search_method': 'Multi_Engine_Intelligent',
                    'date_extraction': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'secteur': 'À analyser'
                }
                results.append(contact_data)
                
                # Sauvegarde incrémentale tous les 5 contacts
                if found_count % 5 == 0:
                    self.save_results(results, start_index, start_index + idx, temp=True)
                    print(f"        💾 Sauvegarde: {found_count} contacts")
                    
        # Sauvegarde finale
        output_file = self.save_results(results, start_index, end_index)
        
        # Résumé
        print("\n🎉 RECHERCHE PROPRE TERMINÉE")
        print("=" * 50)
        print(f"📁 Fichier: {output_file}")
        print(f"✅ Contacts trouvés: {found_count}/{len(associations_to_process)}")
        success_rate = (found_count / len(associations_to_process)) * 100
        print(f"📊 Taux de succès: {success_rate:.1f}%")
        
        if results:
            print("📧 EMAILS TROUVÉS:")
            for i, contact in enumerate(results, 1):
                print(f"  {i}. {contact['email']}")
                print(f"     {contact['nom_association'][:50]}...")
                print(f"     📍 {contact['ville']}")
                
        print("\n💡 PROCHAINES ÉTAPES:")
        print("  1. Consolider: Fusionner avec contacts existants")
        print("  2. Exporter: python brevo_export.py")
        if end_index < len(df):
            print(f"  3. Continuer: Relancer avec index {end_index}")
            
        return results
        
    def save_results(self, results, start_idx, end_idx, temp=False):
        """Sauvegarde les résultats"""
        if not results:
            return None
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        suffix = "_temp" if temp else ""
        filename = f"smart_contacts_clean{suffix}_{start_idx}_{end_idx}_{timestamp}.csv"
        filepath = os.path.join("data", filename)
        
        # Assurer que le dossier existe
        os.makedirs("data", exist_ok=True)
        
        df_results = pd.DataFrame(results)
        df_results.to_csv(filepath, index=False, encoding='utf-8')
        
        return filepath

if __name__ == "__main__":
    finder = SmartContactFinderClean()
    
    print("🏛️ Source: RNA Département 01 (associations filtrées)")
    print("🔬 Méthode: Recherche intelligente + Filtrage des erreurs")
    
    # Paramètres par défaut
    start = input("📍 Index de départ (défaut: 0): ").strip()
    start = int(start) if start else 0
    
    count = input("🔢 Nombre à traiter (défaut: 25): ").strip()
    count = int(count) if count else 25
    
    confirm = input("🚀 Lancer la recherche propre ? (oui/non): ").strip().lower()
    if confirm in ['oui', 'o', 'yes', 'y']:
        finder.run_smart_search(start, count)
    else:
        print("❌ Recherche annulée")
