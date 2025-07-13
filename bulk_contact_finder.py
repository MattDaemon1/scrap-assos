#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BULK CONTACT FINDER - Recherche de contacts en lot optimisée
===========================================================
Recherche rapide et efficace de contacts pour associations RNA
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

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_manager import DataManager

class BulkContactFinder:
    """Chercheur de contacts en lot optimisé"""
    
    def __init__(self):
        self.data_manager = DataManager()
        self.session = requests.Session()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
        
    def load_rna_data(self):
        """Charger données RNA directement"""
        try:
            df = pd.read_csv("data/rna_import_20250701_dpt_01.csv", encoding='utf-8')
            print(f"✅ {len(df)} associations RNA chargées")
            
            # Nettoyer les données
            df['nom_clean'] = df['titre'].str.replace("'", "").str.replace("é", "e").str.replace("É", "E")
            df['ville_clean'] = df['libcom'].str.title()
            
            return df.to_dict('records')
            
        except Exception as e:
            print(f"❌ Erreur chargement RNA: {e}")
            return []
    
    def search_contact_simple(self, nom_association, ville):
        """Recherche contact simplifiée et rapide"""
        try:
            # Nettoyer les termes de recherche
            nom_clean = re.sub(r'[^\w\s]', ' ', nom_association).strip()
            ville_clean = re.sub(r'[^\w\s]', ' ', ville).strip()
            
            # Requête optimisée
            query = f'"{nom_clean}" {ville_clean} email contact'
            
            # Recherche Google
            headers = {'User-Agent': random.choice(self.user_agents)}
            url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
            
            response = self.session.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Extraire emails simples
                emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', response.text)
                
                # Filtrer emails valides
                valid_emails = []
                for email in emails:
                    email_lower = email.lower()
                    if (not any(word in email_lower for word in ['google', 'facebook', 'youtube', 'twitter', 'example']) 
                        and email_lower.count('@') == 1 
                        and '.' in email_lower.split('@')[1]):
                        valid_emails.append(email_lower)
                
                if valid_emails:
                    # Retourner le premier email unique
                    return list(set(valid_emails))[0]
            
            return None
            
        except Exception as e:
            print(f"    ❌ Erreur recherche: {e}")
            return None
    
    def bulk_search(self, start_index=0, max_searches=100):
        """Recherche en lot optimisée"""
        print(f"🚀 RECHERCHE CONTACTS RNA - MODE RAPIDE")
        print(f"=" * 60)
        
        # Charger données
        associations = self.load_rna_data()
        if not associations:
            return
        
        print(f"📊 Recherche: {start_index} à {start_index + max_searches}")
        print(f"📧 Stratégie: Google simplifié + extraction email")
        
        # Sélectionner subset
        subset = associations[start_index:start_index + max_searches]
        
        results = []
        found_count = 0
        
        print(f"\n🔍 RECHERCHE EN COURS...")
        
        for i, asso in enumerate(subset, 1):
            try:
                nom = asso.get('titre', asso.get('nom_clean', ''))
                ville = asso.get('libcom', asso.get('ville_clean', ''))
                
                print(f"  {i:3d}/{len(subset)} - {nom[:40]}... ({ville})")
                
                # Recherche contact
                email = self.search_contact_simple(nom, ville)
                
                if email:
                    found_count += 1
                    result = {
                        'nom_association': nom,
                        'email': email,
                        'ville': ville,
                        'secteur': 'Loisirs/Culture',  # Par défaut pour RNA
                        'telephone': '',
                        'site_web': '',
                        'adresse': asso.get('adr1', ''),
                        'code_postal': asso.get('adrs_codepostal', ''),
                        'objet': asso.get('objet', ''),
                        'source': 'RNA_Bulk_Search',
                        'date_extraction': datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'search_method': 'Google_Simple'
                    }
                    
                    results.append(result)
                    print(f"        ✅ Email trouvé: {email}")
                else:
                    print(f"        ⚠️  Aucun contact")
                
                # Délai anti-ban
                time.sleep(random.uniform(1, 3))
                
            except KeyboardInterrupt:
                print(f"\n⏹️  Recherche interrompue par l'utilisateur")
                break
            except Exception as e:
                print(f"        ❌ Erreur: {e}")
        
        # Sauvegarder résultats
        if results:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"rna_bulk_contacts_{start_index}_{start_index + len(subset)}_{timestamp}.csv"
            
            self.data_manager.save_to_csv(results, filename)
            
            print(f"\n🎉 RECHERCHE TERMINÉE")
            print(f"📁 Fichier: data/{filename}")
            print(f"✅ Contacts trouvés: {found_count}/{len(subset)}")
            print(f"📊 Taux de succès: {(found_count/len(subset)*100):.1f}%")
            
            # Afficher échantillon
            print(f"\n📧 EMAILS TROUVÉS:")
            for i, result in enumerate(results[:5], 1):
                print(f"  {i}. {result['email']} ({result['nom_association'][:30]}...)")
            
            if len(results) > 5:
                print(f"  ... et {len(results)-5} autres")
            
            return filename
        else:
            print(f"\n😞 Aucun contact trouvé dans cette plage")
            return None

def main():
    """Fonction principale"""
    finder = BulkContactFinder()
    
    print(f"🎯 BULK CONTACT FINDER")
    print(f"=" * 40)
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"🏛️ Source: RNA Département 01")
    
    print(f"\n📋 PARAMÈTRES:")
    
    try:
        start = int(input(f"📍 Index de départ (0-654): ").strip() or "0")
        max_search = int(input(f"🔢 Nombre à traiter (max 100): ").strip() or "50")
        
        if max_search > 100:
            max_search = 100
            print(f"⚠️  Limité à 100 pour éviter le ban")
        
        print(f"\n🚀 Lancement recherche {start} → {start + max_search}")
        
        # Confirmation
        confirm = input(f"❓ Continuer ? (oui/non): ").strip().lower()
        if confirm in ['oui', 'o', 'yes', 'y']:
            filename = finder.bulk_search(start, max_search)
            
            if filename:
                print(f"\n💡 SUITE RECOMMANDÉE:")
                print(f"  1. Nettoyer: python scrapers/email_cleaner.py")
                print(f"  2. Consolider avec les autres résultats")
                print(f"  3. Exporter vers Brevo: python brevo_export.py")
        else:
            print(f"❌ Recherche annulée")
            
    except KeyboardInterrupt:
        print(f"\n👋 Au revoir!")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()
