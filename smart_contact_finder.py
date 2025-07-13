#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMART CONTACT FINDER - Recherche intelligente optimisée
======================================================
Recherche avancée nom + ville avec analyse contextuelle
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
import random
from datetime import datetime
import sys
import os
from urllib.parse import quote_plus
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_manager import DataManager

class SmartContactFinder:
    """Chercheur de contacts intelligent"""
    
    def __init__(self):
        self.data_manager = DataManager()
        self.session = requests.Session()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
        # Patterns de recherche intelligents
        self.search_patterns = [
            '"{nom}" {ville} email',
            '"{nom}" {ville} contact',
            '"{nom}" {ville} site',
            'association "{nom}" {ville}',
            '{nom} {ville} association contact',
            '{nom} {ville} secretaire',
            '{nom} {ville} président',
            '{nom} {ville} mairie',
            'site:mairie-{ville_clean}.fr "{nom}"',
            'site:{ville_clean}.fr "{nom}"',
            'site:helloasso.com "{nom}" {ville}',
            'site:associations.gouv.fr "{nom}"'
        ]
        
        # Indicateurs de qualité
        self.quality_indicators = {
            'domain_quality': {
                '.fr': 15,
                '.org': 10,
                '.com': 5,
                'mairie': 20,
                'cc-': 15
            },
            'email_type': {
                'contact': 20,
                'info': 15,
                'secretaire': 25,
                'president': 20,
                'asso': 15,
                'association': 20
            }
        }
    
    def clean_association_name(self, nom):
        """Nettoyer nom association pour recherche"""
        if not nom:
            return ""
        
        # Supprimer caractères spéciaux et accents
        nom_clean = nom.upper()
        replacements = {
            'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
            'À': 'A', 'Â': 'A', 'Ä': 'A',
            'Ç': 'C', 'Ô': 'O', 'Ù': 'U', 'Û': 'U',
            "'": "", '"': '', '(': '', ')': '',
            'SOCIéTé': 'SOCIETE', 'AMICALé': 'AMICALE'
        }
        
        for old, new in replacements.items():
            nom_clean = nom_clean.replace(old, new)
        
        # Supprimer mots génériques en fin
        generic_endings = [
            'ASSOCIATION DISSOUTE DANS MULTI',
            'ASSOCIATION',
            'SOCIéTé',
            'SOCIETE',
            'AMICALé',
            'AMICALE'
        ]
        
        for ending in generic_endings:
            if nom_clean.endswith(ending):
                nom_clean = nom_clean[:-len(ending)].strip()
        
        return nom_clean.strip()
    
    def clean_ville_name(self, ville):
        """Nettoyer nom ville pour recherche"""
        if not ville:
            return ""
        
        ville_clean = ville.upper()
        replacements = {
            'É': 'E', 'È': 'E', 'Ê': 'E',
            'À': 'A', 'Â': 'A',
            'Ç': 'C', 'Ô': 'O'
        }
        
        for old, new in replacements.items():
            ville_clean = ville_clean.replace(old, new)
        
        return ville_clean.strip()
    
    def generate_search_queries(self, nom, ville):
        """Générer requêtes de recherche intelligentes"""
        nom_clean = self.clean_association_name(nom)
        ville_clean = self.clean_ville_name(ville)
        ville_simple = ville_clean.replace('-', '').replace(' ', '')
        
        queries = []
        
        for pattern in self.search_patterns:
            try:
                query = pattern.format(
                    nom=nom_clean,
                    ville=ville_clean,
                    ville_clean=ville_simple.lower()
                )
                queries.append(query)
            except KeyError:
                # Si le pattern n'a pas toutes les variables
                continue
        
        return queries
    
    def extract_emails_advanced(self, html_content, nom_association, ville):
        """Extraction d'emails avec analyse contextuelle"""
        if not html_content:
            return []
        
        # Pattern email amélioré
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails_found = re.findall(email_pattern, html_content, re.IGNORECASE)
        
        if not emails_found:
            return []
        
        # Filtrer et scorer les emails
        scored_emails = []
        
        for email in set(emails_found):  # Dédupliquer
            email_lower = email.lower()
            
            # Exclure emails non pertinents
            if any(domain in email_lower for domain in [
                'google', 'facebook', 'youtube', 'twitter', 'instagram',
                'example', 'test', 'noreply', 'no-reply', 'donotreply'
            ]):
                continue
            
            # Scorer l'email
            score = self.score_email(email, nom_association, ville, html_content)
            
            if score > 10:  # Seuil minimum
                scored_emails.append((email, score))
        
        # Trier par score et retourner les meilleurs
        scored_emails.sort(key=lambda x: x[1], reverse=True)
        return [email for email, score in scored_emails[:3]]  # Top 3
    
    def score_email(self, email, nom_association, ville, context=""):
        """Scorer un email selon pertinence"""
        score = 0
        email_lower = email.lower()
        nom_lower = nom_association.lower()
        ville_lower = ville.lower()
        context_lower = context.lower()
        
        # Score domaine
        domain = email_lower.split('@')[1] if '@' in email_lower else ""
        
        if ville_lower.replace('-', '').replace(' ', '') in domain:
            score += 25  # Domaine contient ville
        
        if 'mairie' in domain:
            score += 20  # Email mairie
        
        if domain.endswith('.fr'):
            score += 15  # Domaine français
        
        if any(word in domain for word in ['cc-', 'communaute', 'agglo']):
            score += 15  # Collectivité
        
        # Score partie locale
        local_part = email_lower.split('@')[0] if '@' in email_lower else email_lower
        
        if any(word in local_part for word in ['contact', 'info', 'secretaire', 'president']):
            score += 20  # Email générique approprié
        
        if any(word in local_part for word in ['asso', 'association', 'club']):
            score += 15  # Email d'association
        
        # Score contexte
        nom_words = [word for word in nom_lower.split() if len(word) > 3]
        if any(word in context_lower for word in nom_words):
            score += 10  # Contexte pertinent
        
        # Score activité
        if any(word in context_lower for word in ['chasse', 'peche', 'sport', 'culture']):
            score += 5  # Contexte activité
        
        return score
    
    def search_with_engine(self, query, engine="google", max_results=10):
        """Recherche avec moteur spécifique"""
        try:
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive'
            }
            
            if engine == "google":
                url = f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}"
            elif engine == "bing":
                url = f"https://www.bing.com/search?q={quote_plus(query)}&count={max_results}"
            elif engine == "qwant":
                url = f"https://www.qwant.com/?q={quote_plus(query)}&count={max_results}"
            else:
                return ""
            
            response = self.session.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                return response.text
            else:
                return ""
                
        except Exception as e:
            print(f"        ⚠️ Erreur {engine}: {e}")
            return ""
    
    def smart_search_contact(self, nom_association, ville):
        """Recherche intelligente multi-étapes"""
        try:
            print(f"    🔍 Recherche: {nom_association[:30]}... à {ville}")
            
            # Générer requêtes
            queries = self.generate_search_queries(nom_association, ville)
            
            all_emails = []
            engines = ["google", "bing"]  # Qwant souvent bloque
            
            # Recherche progressive
            for i, query in enumerate(queries[:6]):  # Limiter à 6 requêtes max
                for engine in engines:
                    if len(all_emails) >= 3:  # Stop si assez d'emails
                        break
                    
                    print(f"        📡 {engine.title()}: {query[:50]}...")
                    
                    html_content = self.search_with_engine(query, engine)
                    
                    if html_content:
                        emails = self.extract_emails_advanced(html_content, nom_association, ville)
                        all_emails.extend(emails)
                    
                    # Délai progressif
                    delay = random.uniform(1, 3) + (i * 0.5)
                    time.sleep(delay)
                
                if len(all_emails) >= 3:
                    break
            
            # Retourner meilleur email unique
            if all_emails:
                # Scorer et dédupliquer
                unique_emails = list(set(all_emails))
                
                if len(unique_emails) == 1:
                    best_email = unique_emails[0]
                else:
                    # Re-scorer avec contexte complet
                    scored = [(email, self.score_email(email, nom_association, ville)) 
                             for email in unique_emails]
                    scored.sort(key=lambda x: x[1], reverse=True)
                    best_email = scored[0][0]
                
                print(f"        ✅ Email trouvé: {best_email}")
                return best_email
            else:
                print(f"        ❌ Aucun email trouvé")
                return None
                
        except Exception as e:
            print(f"        ⚠️ Erreur recherche: {e}")
            return None
    
    def batch_search(self, start_index=0, batch_size=50):
        """Recherche par lot avec sauvegarde incrémentale"""
        print(f"🚀 SMART CONTACT FINDER - RECHERCHE AVANCÉE")
        print(f"=" * 70)
        
        # Charger données RNA
        try:
            df = pd.read_csv("data/rna_import_20250701_dpt_01.csv", encoding='utf-8')
            print(f"✅ {len(df)} associations RNA chargées")
        except Exception as e:
            print(f"❌ Erreur chargement: {e}")
            return
        
        # Sélectionner subset
        end_index = min(start_index + batch_size, len(df))
        subset = df.iloc[start_index:end_index]
        
        print(f"📊 Traitement: {start_index} → {end_index} ({len(subset)} associations)")
        print(f"🎯 Méthode: Nom + Ville + Analyse contextuelle")
        print(f"⚡ Moteurs: Google + Bing")
        
        results = []
        found_count = 0
        
        print(f"\n🔍 RECHERCHE EN COURS...")
        print(f"-" * 50)
        
        for i, (_, row) in enumerate(subset.iterrows(), 1):
            try:
                nom = row.get('titre', '')
                ville = row.get('libcom', '')
                
                if not nom or not ville:
                    print(f"  {i:3d}/{len(subset)} - ⚠️ Données manquantes")
                    continue
                
                print(f"  {i:3d}/{len(subset)} - {nom[:40]}...")
                
                # Recherche intelligente
                email = self.smart_search_contact(nom, ville)
                
                if email:
                    found_count += 1
                    
                    result = {
                        'nom_association': nom,
                        'email': email,
                        'ville': ville,
                        'secteur': 'Loisirs/Culture',
                        'telephone': '',
                        'site_web': '',
                        'adresse': row.get('adr1', ''),
                        'code_postal': row.get('adrs_codepostal', ''),
                        'objet': row.get('objet', ''),
                        'source': 'Smart_Search',
                        'date_extraction': datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'search_method': 'Multi_Engine_Smart'
                    }
                    
                    results.append(result)
                
                # Sauvegarde incrémentale tous les 10
                if i % 10 == 0 and results:
                    self._save_incremental(results, start_index, i)
                
            except KeyboardInterrupt:
                print(f"\n⏹️ Recherche interrompue par l'utilisateur")
                break
            except Exception as e:
                print(f"    ❌ Erreur: {e}")
        
        # Sauvegarde finale
        if results:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"smart_contacts_{start_index}_{end_index}_{timestamp}.csv"
            
            self.data_manager.save_to_csv(results, filename)
            
            print(f"\n🎉 RECHERCHE TERMINÉE")
            print(f"=" * 40)
            print(f"📁 Fichier: data/{filename}")
            print(f"✅ Contacts trouvés: {found_count}/{len(subset)}")
            print(f"📊 Taux de succès: {(found_count/len(subset)*100):.1f}%")
            
            # Afficher échantillon
            print(f"\n📧 EMAILS TROUVÉS:")
            for i, result in enumerate(results[:8], 1):
                print(f"  {i}. {result['email']}")
                print(f"     {result['nom_association'][:50]}...")
                print(f"     📍 {result['ville']}")
                print()
            
            return filename
        else:
            print(f"\n😞 Aucun contact trouvé")
            return None
    
    def _save_incremental(self, results, start_index, current_index):
        """Sauvegarde incrémentale"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"smart_contacts_temp_{start_index}_{current_index}_{timestamp}.csv"
        self.data_manager.save_to_csv(results, filename)
        print(f"        💾 Sauvegarde: {len(results)} contacts")

def main():
    """Fonction principale"""
    finder = SmartContactFinder()
    
    print(f"🎯 SMART CONTACT FINDER")
    print(f"=" * 50)
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"🏛️ Source: RNA Département 01 (654 associations)")
    print(f"🔬 Méthode: IA + Multi-moteurs + Analyse contextuelle")
    
    print(f"\n💡 AMÉLIORATIONS:")
    print(f"  ✅ Requêtes intelligentes nom + ville")
    print(f"  ✅ Scoring avancé des emails")
    print(f"  ✅ Analyse contextuelle")
    print(f"  ✅ Sauvegarde incrémentale")
    print(f"  ✅ Anti-détection renforcé")
    
    try:
        start = int(input(f"\n📍 Index de départ (0-654): ").strip() or "0")
        batch_size = int(input(f"🔢 Nombre à traiter (recommandé: 30): ").strip() or "30")
        
        if batch_size > 100:
            batch_size = 100
            print(f"⚠️ Limité à 100 pour éviter les blocages")
        
        print(f"\n🚀 Lancement recherche intelligente...")
        
        confirm = input(f"❓ Continuer ? (oui/non): ").strip().lower()
        if confirm in ['oui', 'o', 'yes', 'y']:
            filename = finder.batch_search(start, batch_size)
            
            if filename:
                print(f"\n💡 PROCHAINES ÉTAPES:")
                print(f"  1. Consolider: Fusionner avec contacts existants")
                print(f"  2. Nettoyer: python scrapers/email_cleaner.py")
                print(f"  3. Exporter: python brevo_export.py")
                print(f"  4. Continuer: Relancer avec index {start + batch_size}")
        else:
            print(f"❌ Recherche annulée")
            
    except KeyboardInterrupt:
        print(f"\n👋 Au revoir!")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()
