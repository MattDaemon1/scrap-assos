#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BREVO EXPORT - Export des contacts RNA vers Brevo
================================================
Formatage optimal pour import dans Brevo (ex-Sendinblue)
"""

import pandas as pd
from datetime import datetime
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from campaign_tracker import CampaignTracker

class BrevoExporter:
    """Exporteur de contacts pour Brevo"""
    
    def __init__(self):
        self.tracker = CampaignTracker()
        
    def export_for_brevo(self, include_all=True):
        """Exporter contacts au format Brevo"""
        print(f"📤 EXPORT BREVO - CONTACTS RNA")
        print(f"=" * 50)
        
        try:
            # Charger les contacts RNA
            df = pd.read_csv("data/rna_emails_clean_20250713_1608.csv")
            
            # Format Brevo optimisé
            brevo_contacts = []
            
            for _, contact in df.iterrows():
                # Nettoyer le nom de l'association
                nom_clean = str(contact['nom_association']).replace("'", "").replace("é", "e").replace("É", "E")
                
                # Déterminer le type d'association
                type_asso = self._categorize_association(nom_clean, str(contact.get('objet', '')))
                
                # Créer contact Brevo
                brevo_contact = {
                    'EMAIL': contact['email'],
                    'PRENOM': 'Responsable',  # Générique
                    'NOM': nom_clean[:50],  # Limité à 50 caractères
                    'ASSOCIATION': nom_clean,
                    'VILLE': str(contact['ville']).title(),
                    'DEPARTEMENT': '01 - Ain',
                    'SECTEUR': str(contact['secteur']),
                    'TYPE_ASSOCIATION': type_asso,
                    'TELEPHONE': self._format_phone(str(contact.get('telephone', ''))),
                    'SOURCE': 'RNA_Scraping_2025',
                    'STATUT': 'Prospect',
                    'DATE_AJOUT': datetime.now().strftime('%d/%m/%Y'),
                    'INTERET_SITE_WEB': 'OUI',  # Cible de notre campagne
                    'BUDGET_ESTIME': '400-800€',  # Basé sur notre offre
                    'PRIORITE': 'MOYENNE',
                    'NOTES': f"Association {type_asso.lower()} - {contact['ville']} - Contact extrait RNA officiel"
                }
                
                brevo_contacts.append(brevo_contact)
                print(f"  ✅ {brevo_contact['ASSOCIATION'][:40]}... → {brevo_contact['EMAIL']}")
            
            # Sauvegarder
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"data/brevo_import_{timestamp}.csv"
            
            df_brevo = pd.DataFrame(brevo_contacts)
            df_brevo.to_csv(filename, index=False, encoding='utf-8-sig')  # BOM pour Excel
            
            print(f"\n🎉 EXPORT BREVO TERMINÉ")
            print(f"📁 Fichier: {filename}")
            print(f"📧 {len(brevo_contacts)} contacts exportés")
            
            # Statistiques
            self._print_export_stats(brevo_contacts)
            
            # Instructions d'import
            self._print_import_instructions(filename)
            
            return filename
            
        except Exception as e:
            print(f"❌ Erreur export: {e}")
            return None
    
    def _categorize_association(self, nom, objet):
        """Catégoriser le type d'association"""
        nom_lower = nom.lower()
        objet_lower = str(objet).lower()
        
        if any(word in nom_lower for word in ['chasse', 'chasseur', 'gibier', 'cyneg']):
            return 'CHASSE'
        elif any(word in nom_lower for word in ['peche', 'pêche', 'gaule', 'halieutique']):
            return 'PECHE'
        elif any(word in nom_lower for word in ['sport', 'gym', 'athletic', 'football', 'basket']):
            return 'SPORT'
        elif any(word in nom_lower for word in ['culture', 'art', 'musique', 'theatre']):
            return 'CULTURE'
        elif any(word in nom_lower for word in ['combat', 'ancien', 'guerre', 'veteran']):
            return 'ANCIENS_COMBATTANTS'
        elif any(word in nom_lower for word in ['social', 'humanitaire', 'entraide']):
            return 'SOCIAL'
        else:
            return 'LOISIRS'
    
    def _format_phone(self, phone):
        """Formater numéro de téléphone"""
        if not phone or phone == 'nan':
            return ''
        
        # Nettoyer
        phone = str(phone).replace('.0', '').replace(' ', '').replace('.', '')
        
        # Formater si valide
        if len(phone) == 10 and phone.startswith('0'):
            return f"{phone[:2]}.{phone[2:4]}.{phone[4:6]}.{phone[6:8]}.{phone[8:10]}"
        elif len(phone) == 9:
            return f"0{phone[0]}.{phone[1:3]}.{phone[3:5]}.{phone[5:7]}.{phone[7:9]}"
        
        return phone
    
    def _print_export_stats(self, contacts):
        """Afficher statistiques d'export"""
        print(f"\n📊 STATISTIQUES EXPORT:")
        
        # Par type
        types = {}
        for contact in contacts:
            type_asso = contact['TYPE_ASSOCIATION']
            types[type_asso] = types.get(type_asso, 0) + 1
        
        print(f"  📋 Types d'associations:")
        for type_asso, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
            print(f"    • {type_asso}: {count}")
        
        # Par ville
        villes = {}
        for contact in contacts:
            ville = contact['VILLE']
            villes[ville] = villes.get(ville, 0) + 1
        
        print(f"\n  🏙️ Principales villes:")
        for ville, count in sorted(villes.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    • {ville}: {count}")
        
        # Téléphones
        with_phone = sum(1 for c in contacts if c['TELEPHONE'])
        print(f"\n  📞 Contacts avec téléphone: {with_phone}/{len(contacts)} ({(with_phone/len(contacts)*100):.1f}%)")
    
    def _print_import_instructions(self, filename):
        """Instructions d'import dans Brevo"""
        print(f"\n📋 INSTRUCTIONS IMPORT BREVO:")
        print(f"=" * 40)
        print(f"1. 🌐 Connectez-vous à votre compte Brevo")
        print(f"2. 📧 Allez dans 'Contacts' > 'Listes'")
        print(f"3. ➕ Cliquez 'Créer une liste' → 'RNA Associations Ain'")
        print(f"4. 📁 Importez le fichier: {os.path.basename(filename)}")
        print(f"5. 🔗 Mappez les colonnes automatiquement")
        print(f"6. ✅ Validez l'import")
        
        print(f"\n📋 COLONNES IMPORTANTES:")
        print(f"  • EMAIL → Email (obligatoire)")
        print(f"  • ASSOCIATION → Nom de l'association")
        print(f"  • VILLE → Ville")
        print(f"  • TYPE_ASSOCIATION → Catégorie")
        print(f"  • SECTEUR → Secteur d'activité")
        print(f"  • TELEPHONE → Téléphone")
        
        print(f"\n🎯 SEGMENTATION RECOMMANDÉE:")
        print(f"  • Par TYPE_ASSOCIATION (ciblage par secteur)")
        print(f"  • Par VILLE (campagnes locales)")
        print(f"  • Par BUDGET_ESTIME (personnalisation offre)")
        
        print(f"\n📧 CAMPAGNE SUGGÉRÉE:")
        print(f"  • Nom: 'Site Web Associations Ain 2025'")
        print(f"  • Objet: 'Et si [ASSOCIATION] avait un site web à son image ?'")
        print(f"  • Segmentation: TYPE_ASSOCIATION = 'CHASSE' (commencer par le plus représenté)")

def create_brevo_template():
    """Créer template email adapté Brevo"""
    template = """Objet: Et si {{ contact.ASSOCIATION }} avait un site web à son image ?

Bonjour,

Je me permets de vous contacter concernant {{ contact.ASSOCIATION }}, association {{ contact.TYPE_ASSOCIATION }} basée à {{ contact.VILLE }}.

👉 Votre association mérite-t-elle un site web moderne ?

En tant que spécialiste du web pour les associations de l'Ain, je propose :

🔹 Site vitrine clé en main dès 400€
🔹 Design responsive et professionnel  
🔹 Formulaires d'adhésion intégrés
🔹 Formation + 1 an de maintenance inclus

{{ contact.TYPE_ASSOCIATION == "CHASSE" }}
Idéal pour présenter vos territoires, calendrier des battues et adhésions.
{{ contact.TYPE_ASSOCIATION == "PECHE" }}  
Parfait pour vos parcours de pêche, réglementation et cartes.
{{ contact.TYPE_ASSOCIATION == "SPORT" }}
Excellent pour calendrier, résultats et inscriptions.
{{ /contact.TYPE_ASSOCIATION }}

Une discussion de 15 minutes vous intéresse ?
Répondez simplement ou appelez-moi au 07.82.90.15.35

Cordialement,
Matthieu ALLART
Développeur Web - MattKonnect
https://mattkonnect.com

P.S. Devis gratuit, sans engagement."""

    with open("templates/brevo_template.txt", 'w', encoding='utf-8') as f:
        f.write(template)
    
    print(f"📝 Template Brevo créé: templates/brevo_template.txt")

def main():
    """Fonction principale"""
    exporter = BrevoExporter()
    
    print(f"📤 EXPORT BREVO - RNA ASSOCIATIONS")
    print(f"=" * 50)
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"🏛️ Source: RNA Département 01 (Ain)")
    
    # Export
    filename = exporter.export_for_brevo()
    
    if filename:
        print(f"\n💡 OPTIONS SUPPLÉMENTAIRES:")
        print(f"  1. 📝 Créer template Brevo adapté")
        print(f"  2. 📊 Voir dashboard actuel")
        print(f"  3. 🚪 Terminer")
        
        choice = input(f"\n❓ Votre choix (1-3): ").strip()
        
        if choice == '1':
            create_brevo_template()
        elif choice == '2':
            exporter.tracker.get_dashboard()
        elif choice == '3':
            print(f"👋 Export terminé!")
    else:
        print(f"❌ Erreur lors de l'export")

if __name__ == "__main__":
    main()
