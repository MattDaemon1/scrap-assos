#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAMPAIGN TRACKER - Gestionnaire de campagne email
=================================================
Suivi des envois, retours, réponses et lead management
"""

import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta
import json
from email.utils import parseaddr
import re

class CampaignTracker:
    """Gestionnaire de suivi de campagne email"""
    
    def __init__(self, db_path="data/campaign_tracker.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialiser la base de données SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table des contacts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom_association TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                ville TEXT,
                secteur TEXT,
                telephone TEXT,
                statut TEXT DEFAULT 'prospect',
                source TEXT DEFAULT 'RNA',
                date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        ''')
        
        # Table des envois
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS envois (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER,
                objet TEXT,
                template_utilise TEXT,
                date_envoi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                statut_envoi TEXT DEFAULT 'envoye',
                bounce BOOLEAN DEFAULT 0,
                ouvert BOOLEAN DEFAULT 0,
                clique BOOLEAN DEFAULT 0,
                FOREIGN KEY (contact_id) REFERENCES contacts (id)
            )
        ''')
        
        # Table des réponses
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reponses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER,
                envoi_id INTEGER,
                date_reponse TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                type_reponse TEXT,
                contenu_reponse TEXT,
                sentiment TEXT,
                action_requise TEXT,
                traite BOOLEAN DEFAULT 0,
                FOREIGN KEY (contact_id) REFERENCES contacts (id),
                FOREIGN KEY (envoi_id) REFERENCES envois (id)
            )
        ''')
        
        # Table des suivis
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suivis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER,
                date_suivi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                type_action TEXT,
                description TEXT,
                prochaine_action TEXT,
                date_prochaine_action DATE,
                priorite INTEGER DEFAULT 3,
                FOREIGN KEY (contact_id) REFERENCES contacts (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Base de données initialisée: {self.db_path}")
    
    def import_rna_contacts(self, csv_file="data/rna_emails_clean_20250713_1608.csv"):
        """Importer les contacts RNA dans la base"""
        print(f"📥 IMPORT CONTACTS RNA")
        print(f"=" * 40)
        
        try:
            df = pd.read_csv(csv_file)
            conn = sqlite3.connect(self.db_path)
            
            imported = 0
            skipped = 0
            
            for _, row in df.iterrows():
                try:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR IGNORE INTO contacts 
                        (nom_association, email, ville, secteur, telephone, source)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        row['nom_association'],
                        row['email'],
                        row['ville'],
                        row['secteur'],
                        row['telephone'],
                        'RNA_Scraping'
                    ))
                    
                    if cursor.rowcount > 0:
                        imported += 1
                        print(f"  ✅ {row['nom_association'][:40]}... → {row['email']}")
                    else:
                        skipped += 1
                        print(f"  ⚠️  Déjà existant: {row['email']}")
                        
                except Exception as e:
                    skipped += 1
                    print(f"  ❌ Erreur: {e}")
            
            conn.commit()
            conn.close()
            
            print(f"\n📊 RÉSULTAT IMPORT:")
            print(f"  ✅ Contacts importés: {imported}")
            print(f"  ⚠️  Contacts ignorés: {skipped}")
            
            return imported
            
        except Exception as e:
            print(f"❌ Erreur import: {e}")
            return 0
    
    def log_email_sent(self, email, objet, template="email_template_1"):
        """Enregistrer un envoi d'email"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Trouver le contact
        cursor.execute('SELECT id FROM contacts WHERE email = ?', (email,))
        contact = cursor.fetchone()
        
        if contact:
            contact_id = contact[0]
            cursor.execute('''
                INSERT INTO envois (contact_id, objet, template_utilise)
                VALUES (?, ?, ?)
            ''', (contact_id, objet, template))
            
            envoi_id = cursor.lastrowid
            
            # Mettre à jour le statut du contact
            cursor.execute('''
                UPDATE contacts SET statut = 'contacte' WHERE id = ?
            ''', (contact_id,))
            
            conn.commit()
            conn.close()
            
            print(f"📧 Envoi enregistré: {email} (ID: {envoi_id})")
            return envoi_id
        else:
            print(f"❌ Contact non trouvé: {email}")
            conn.close()
            return None
    
    def log_response(self, email, type_reponse, contenu="", sentiment="neutre"):
        """Enregistrer une réponse reçue"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Trouver contact et dernier envoi
        cursor.execute('''
            SELECT c.id, e.id FROM contacts c
            LEFT JOIN envois e ON c.id = e.contact_id
            WHERE c.email = ?
            ORDER BY e.date_envoi DESC
            LIMIT 1
        ''', (email,))
        
        result = cursor.fetchone()
        if result:
            contact_id, envoi_id = result
            
            # Analyser le type de réponse
            action_requise = self._determine_action(type_reponse, contenu)
            
            cursor.execute('''
                INSERT INTO reponses 
                (contact_id, envoi_id, type_reponse, contenu_reponse, sentiment, action_requise)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (contact_id, envoi_id, type_reponse, contenu, sentiment, action_requise))
            
            # Mettre à jour statut contact
            nouveau_statut = self._determine_statut(type_reponse)
            cursor.execute('''
                UPDATE contacts SET statut = ? WHERE id = ?
            ''', (nouveau_statut, contact_id))
            
            conn.commit()
            conn.close()
            
            print(f"📬 Réponse enregistrée: {email} → {type_reponse}")
            return True
        else:
            print(f"❌ Contact/envoi non trouvé: {email}")
            conn.close()
            return False
    
    def _determine_action(self, type_reponse, contenu):
        """Déterminer l'action requise selon la réponse"""
        actions = {
            'interesse': 'appel_commercial',
            'demande_info': 'envoyer_documentation',
            'demande_devis': 'preparer_devis',
            'pas_interesse': 'marquer_non_qualifie',
            'rappeler_plus_tard': 'programmer_relance',
            'desabonnement': 'supprimer_liste',
            'bounce': 'verifier_email'
        }
        return actions.get(type_reponse, 'analyser_manuellement')
    
    def _determine_statut(self, type_reponse):
        """Déterminer le nouveau statut selon la réponse"""
        statuts = {
            'interesse': 'lead_chaud',
            'demande_info': 'lead_tiede',
            'demande_devis': 'lead_chaud',
            'pas_interesse': 'non_qualifie',
            'rappeler_plus_tard': 'lead_tiede',
            'desabonnement': 'desabonne',
            'bounce': 'email_invalide'
        }
        return statuts.get(type_reponse, 'contacte')
    
    def get_dashboard(self):
        """Générer tableau de bord de campagne"""
        conn = sqlite3.connect(self.db_path)
        
        print(f"\n📊 DASHBOARD CAMPAGNE EMAIL")
        print(f"=" * 50)
        print(f"📅 Dernière mise à jour: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        # Statistiques contacts
        df_contacts = pd.read_sql_query('''
            SELECT statut, COUNT(*) as nombre
            FROM contacts 
            GROUP BY statut
            ORDER BY nombre DESC
        ''', conn)
        
        print(f"\n👥 CONTACTS PAR STATUT:")
        total_contacts = 0
        for _, row in df_contacts.iterrows():
            print(f"  • {row['statut']}: {row['nombre']}")
            total_contacts += row['nombre']
        print(f"  📊 Total: {total_contacts}")
        
        # Statistiques envois
        df_envois = pd.read_sql_query('''
            SELECT COUNT(*) as total_envois,
                   SUM(CASE WHEN bounce = 1 THEN 1 ELSE 0 END) as bounces,
                   SUM(CASE WHEN ouvert = 1 THEN 1 ELSE 0 END) as ouvertures
            FROM envois
        ''', conn)
        
        print(f"\n📧 ENVOIS EMAIL:")
        envois_stats = df_envois.iloc[0]
        print(f"  • Total envoyé: {envois_stats['total_envois']}")
        print(f"  • Bounces: {envois_stats['bounces']}")
        print(f"  • Ouvertures: {envois_stats['ouvertures']}")
        
        if envois_stats['total_envois'] > 0:
            taux_bounce = (envois_stats['bounces'] / envois_stats['total_envois']) * 100
            taux_ouverture = (envois_stats['ouvertures'] / envois_stats['total_envois']) * 100
            print(f"  📈 Taux bounce: {taux_bounce:.1f}%")
            print(f"  📈 Taux ouverture: {taux_ouverture:.1f}%")
        
        # Réponses par type
        df_reponses = pd.read_sql_query('''
            SELECT type_reponse, COUNT(*) as nombre
            FROM reponses 
            GROUP BY type_reponse
            ORDER BY nombre DESC
        ''', conn)
        
        if not df_reponses.empty:
            print(f"\n💬 RÉPONSES REÇUES:")
            for _, row in df_reponses.iterrows():
                print(f"  • {row['type_reponse']}: {row['nombre']}")
        
        # Actions requises
        df_actions = pd.read_sql_query('''
            SELECT action_requise, COUNT(*) as nombre
            FROM reponses 
            WHERE traite = 0
            GROUP BY action_requise
            ORDER BY nombre DESC
        ''', conn)
        
        if not df_actions.empty:
            print(f"\n⚡ ACTIONS REQUISES:")
            for _, row in df_actions.iterrows():
                print(f"  • {row['action_requise']}: {row['nombre']}")
        
        conn.close()
    
    def get_leads_chauds(self):
        """Obtenir la liste des leads chauds"""
        conn = sqlite3.connect(self.db_path)
        
        df_leads = pd.read_sql_query('''
            SELECT c.nom_association, c.email, c.telephone, c.ville,
                   r.type_reponse, r.date_reponse, r.action_requise
            FROM contacts c
            LEFT JOIN reponses r ON c.id = r.contact_id
            WHERE c.statut IN ('lead_chaud', 'lead_tiede')
            ORDER BY r.date_reponse DESC
        ''', conn)
        
        conn.close()
        
        if not df_leads.empty:
            print(f"\n🔥 LEADS CHAUDS À TRAITER:")
            print(f"=" * 50)
            
            for _, lead in df_leads.iterrows():
                print(f"📧 {lead['email']}")
                print(f"  🏢 {lead['nom_association']}")
                print(f"  📍 {lead['ville']}")
                print(f"  📞 {lead['telephone']}")
                print(f"  💬 {lead['type_reponse']} → {lead['action_requise']}")
                print()
        else:
            print(f"\n😎 Aucun lead chaud en attente")
        
        return df_leads
    
    def export_for_crm(self, filename="data/leads_export.csv"):
        """Exporter les leads pour CRM externe"""
        conn = sqlite3.connect(self.db_path)
        
        df_export = pd.read_sql_query('''
            SELECT 
                c.nom_association,
                c.email,
                c.telephone,
                c.ville,
                c.secteur,
                c.statut,
                c.date_ajout,
                COUNT(e.id) as nb_emails_envoyes,
                MAX(e.date_envoi) as dernier_envoi,
                COUNT(r.id) as nb_reponses,
                r.type_reponse as derniere_reponse,
                r.action_requise
            FROM contacts c
            LEFT JOIN envois e ON c.id = e.contact_id
            LEFT JOIN reponses r ON c.id = r.contact_id
            GROUP BY c.id
            ORDER BY c.statut, c.date_ajout DESC
        ''', conn)
        
        conn.close()
        
        df_export.to_csv(filename, index=False, encoding='utf-8')
        print(f"📊 Export CRM sauvé: {filename}")
        print(f"📈 {len(df_export)} contacts exportés")
        
        return filename

def main():
    """Fonction principale - Demo du tracker"""
    tracker = CampaignTracker()
    
    print(f"🎯 CAMPAIGN TRACKER - DEMO")
    print(f"=" * 40)
    
    # Import des contacts RNA
    imported = tracker.import_rna_contacts()
    
    if imported > 0:
        print(f"\n📧 Simulation d'envois...")
        # Simuler quelques envois (en réalité, ceci serait appelé après chaque envoi)
        conn = sqlite3.connect(tracker.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT email FROM contacts LIMIT 3')
        emails = cursor.fetchall()
        conn.close()
        
        for email_tuple in emails:
            email = email_tuple[0]
            tracker.log_email_sent(email, "Et si Association Test avait un site web à son image ?")
    
    # Afficher dashboard
    tracker.get_dashboard()
    
    # Exemple d'enregistrement de réponses
    print(f"\n💡 EXEMPLE D'UTILISATION:")
    print(f"# Pour enregistrer une réponse positive:")
    print(f"tracker.log_response('email@association.fr', 'interesse', 'Bonjour, votre offre m\\'intéresse...')")
    print(f"")
    print(f"# Pour voir les leads chauds:")
    print(f"tracker.get_leads_chauds()")
    print(f"")
    print(f"# Pour exporter vers CRM:")
    print(f"tracker.export_for_crm()")

if __name__ == "__main__":
    main()
