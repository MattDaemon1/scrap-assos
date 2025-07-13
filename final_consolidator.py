#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONSOLIDATEUR FINAL DE CONTACTS
Fusionne tous les contacts trouvés et prépare l'export Brevo final
"""

import pandas as pd
from datetime import datetime
import os

def consolidate_all_contacts():
    """Consolide tous les fichiers de contacts"""
    print("🔗 CONSOLIDATION FINALE DES CONTACTS")
    print("=" * 50)
    
    all_contacts = []
    
    # Fichiers à consolider
    contact_files = [
        "data/rna_emails_clean_20250713_1608.csv",  # 6 contacts RNA originaux
        "data/smart_contacts_0_30_20250713_1925.csv",  # 1 contact smart search
        "data/modern_contacts_0_12_20250713_2011.csv"  # 10 contacts modernes
    ]
    
    for file_path in contact_files:
        if os.path.exists(file_path):
            print(f"📂 Chargement: {file_path}")
            df = pd.read_csv(file_path)
            print(f"   ✅ {len(df)} contacts")
            
            # Standardiser les colonnes
            if 'nom_association' not in df.columns and 'titre' in df.columns:
                df = df.rename(columns={'titre': 'nom_association'})
            if 'libcom' in df.columns and 'ville' not in df.columns:
                df = df.rename(columns={'libcom': 'ville'})
                
            all_contacts.append(df)
        else:
            print(f"❌ Fichier non trouvé: {file_path}")
    
    if not all_contacts:
        print("❌ Aucun fichier de contact trouvé")
        return None
        
    # Fusionner tous les DataFrames
    df_combined = pd.concat(all_contacts, ignore_index=True, sort=False)
    
    # Déduplication par email
    initial_count = len(df_combined)
    df_combined = df_combined.drop_duplicates(subset=['email'], keep='first')
    final_count = len(df_combined)
    
    print(f"\n📊 RÉSULTATS CONSOLIDATION:")
    print(f"📈 Total initial: {initial_count} contacts")
    print(f"🗑️ Doublons supprimés: {initial_count - final_count}")
    print(f"✅ Total final: {final_count} contacts uniques")
    
    # Analyser les types de contacts
    if 'contact_type' in df_combined.columns:
        contact_types = df_combined['contact_type'].value_counts()
        print(f"\n📊 RÉPARTITION PAR TYPE:")
        for contact_type, count in contact_types.items():
            icon = "🏛️" if contact_type == "Mairie" else "🏢"
            print(f"   {icon} {contact_type}: {count}")
    
    # Sauvegarder le fichier consolidé
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    output_file = f"data/contacts_consolidated_{timestamp}.csv"
    
    # Colonnes standard pour l'export
    standard_columns = [
        'nom_association', 'ville', 'email', 'objet', 'adresse', 
        'contact_type', 'date_creation', 'source', 'search_method', 
        'date_extraction', 'secteur'
    ]
    
    # Réorganiser les colonnes
    df_export = pd.DataFrame()
    for col in standard_columns:
        if col in df_combined.columns:
            df_export[col] = df_combined[col]
        else:
            df_export[col] = ''
    
    df_export.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"\n💾 FICHIER CONSOLIDÉ SAUVÉ:")
    print(f"📁 {output_file}")
    print(f"📧 {final_count} contacts prêts pour Brevo")
    
    return output_file, df_export

def create_brevo_export(df_contacts, consolidated_file):
    """Crée un export optimisé pour Brevo"""
    print("\n🚀 PRÉPARATION EXPORT BREVO")
    print("=" * 40)
    
    brevo_data = []
    
    for _, contact in df_contacts.iterrows():
        # Catégoriser l'association
        objet = str(contact.get('objet', '')).lower()
        nom = str(contact.get('nom_association', '')).lower()
        
        if any(word in objet or word in nom for word in ['sport', 'football', 'tennis', 'boule', 'cycliste']):
            category = "Sport"
        elif any(word in objet or word in nom for word in ['culture', 'cinema', 'bibliotheque', 'theatre']):
            category = "Culture"
        elif any(word in objet or word in nom for word in ['chasse', 'peche', 'environnement']):
            category = "Environnement"
        elif any(word in objet or word in nom for word in ['fete', 'animation', 'jumelage']):
            category = "Animation"
        else:
            category = "Autre"
            
        # Déterminer la priorité
        contact_type = contact.get('contact_type', 'Association')
        if contact_type == 'Association':
            priority = "Haute"
        else:
            priority = "Moyenne"  # Mairies
            
        brevo_contact = {
            'EMAIL': contact['email'],
            'PRENOM': '',  # Sera personnalisé dans la campagne
            'NOM': '',
            'ENTREPRISE': contact['nom_association'][:50],
            'VILLE': contact['ville'],
            'SECTEUR': category,
            'PRIORITE': priority,
            'CONTACT_TYPE': contact_type,
            'SOURCE': 'RNA_AUTOMATISE',
            'DATE_AJOUT': datetime.now().strftime('%Y-%m-%d'),
            'NOTES': f"Association: {contact['nom_association'][:100]}"
        }
        brevo_data.append(brevo_contact)
    
    # Créer le DataFrame Brevo
    df_brevo = pd.DataFrame(brevo_data)
    
    # Analyser la répartition
    print(f"📊 ANALYSE EXPORT BREVO:")
    print(f"📧 Total contacts: {len(df_brevo)}")
    print(f"🏆 Priorité haute: {len(df_brevo[df_brevo['PRIORITE'] == 'Haute'])}")
    print(f"📈 Priorité moyenne: {len(df_brevo[df_brevo['PRIORITE'] == 'Moyenne'])}")
    
    category_counts = df_brevo['SECTEUR'].value_counts()
    print(f"\n📊 RÉPARTITION PAR SECTEUR:")
    for sector, count in category_counts.items():
        print(f"   • {sector}: {count}")
    
    # Sauvegarder l'export Brevo
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    brevo_file = f"data/brevo_export_final_{timestamp}.csv"
    df_brevo.to_csv(brevo_file, index=False, encoding='utf-8')
    
    print(f"\n🎯 EXPORT BREVO PRÊT:")
    print(f"📁 {brevo_file}")
    print(f"✅ {len(df_brevo)} contacts formatés pour import")
    
    return brevo_file

if __name__ == "__main__":
    print("🎯 CONSOLIDATION ET EXPORT FINAL")
    print("Fusion de tous les contacts trouvés + Export Brevo")
    print("=" * 60)
    
    # Consolidation
    result = consolidate_all_contacts()
    if result:
        consolidated_file, df_contacts = result
        
        # Export Brevo
        brevo_file = create_brevo_export(df_contacts, consolidated_file)
        
        print("\n🎉 PROCESSUS TERMINÉ")
        print("=" * 30)
        print("💡 PROCHAINES ÉTAPES:")
        print("  1. ✅ Contacts consolidés et dédupliqués")
        print("  2. ✅ Export Brevo prêt")
        print("  3. 🚀 Importer dans Brevo et lancer la campagne")
        print(f"  4. 📧 {len(df_contacts)} contacts prêts à recevoir vos emails")
    else:
        print("❌ Échec de la consolidation")
