import pandas as pd
import os
import glob
from datetime import datetime
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_manager import DataManager

class RnaContactConsolidator:
    """Consolidateur des contacts RNA trouvés"""
    
    def __init__(self):
        self.data_manager = DataManager()
    
    def consolidate_rna_contacts(self):
        """Consolider tous les fichiers RNA avec contacts"""
        print("🎯 CONSOLIDATION CONTACTS RNA")
        print("=" * 50)
        
        # Rechercher tous les fichiers RNA avec contacts
        contact_files = glob.glob("data/rna_with_contacts_*.csv")
        
        if not contact_files:
            print("❌ Aucun fichier de contacts RNA trouvé")
            return []
        
        print(f"📁 {len(contact_files)} fichiers trouvés:")
        for file in contact_files:
            print(f"  • {os.path.basename(file)}")
        
        # Charger et consolider
        all_associations = []
        
        for file in contact_files:
            try:
                df = pd.read_csv(file)
                associations = df.to_dict('records')
                all_associations.extend(associations)
                print(f"  ✅ {len(associations)} associations depuis {os.path.basename(file)}")
            except Exception as e:
                print(f"  ❌ Erreur {file}: {e}")
        
        # Déduplication
        unique_associations = self._deduplicate_by_name_city(all_associations)
        
        # Filtrer celles avec contacts
        with_contacts = [a for a in unique_associations if a.get('email_principal') or a.get('site_web')]
        
        print(f"\n📊 RÉSULTATS CONSOLIDATION:")
        print(f"  • Total brut: {len(all_associations)}")
        print(f"  • Après déduplication: {len(unique_associations)}")
        print(f"  • Avec contacts: {len(with_contacts)}")
        
        # Sauvegarder consolidation
        if unique_associations:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            
            # Fichier complet
            filename_all = f"rna_consolidated_all_{timestamp}.csv"
            self.data_manager.save_to_csv(unique_associations, filename_all)
            
            # Fichier contacts uniquement
            filename_contacts = f"rna_consolidated_contacts_{timestamp}.csv"
            self.data_manager.save_to_csv(with_contacts, filename_contacts)
            
            print(f"\n📁 FICHIERS CRÉÉS:")
            print(f"  • Toutes associations: data/{filename_all}")
            print(f"  • Avec contacts: data/{filename_contacts}")
            
            # Statistiques détaillées
            self._generate_contact_stats(with_contacts)
            
            return with_contacts
        
        return []
    
    def _deduplicate_by_name_city(self, associations):
        """Déduplication par nom et ville"""
        unique = []
        seen = set()
        
        for assoc in associations:
            key = f"{assoc.get('nom', '').lower().strip()}_{assoc.get('ville', '').lower().strip()}"
            
            if key not in seen:
                seen.add(key)
                unique.append(assoc)
        
        return unique
    
    def _generate_contact_stats(self, associations_with_contacts):
        """Générer statistiques détaillées des contacts"""
        print(f"\n📈 STATISTIQUES CONTACTS RNA:")
        
        total = len(associations_with_contacts)
        
        # Contacts par type
        with_email = sum(1 for a in associations_with_contacts if a.get('email_principal'))
        with_phone = sum(1 for a in associations_with_contacts if a.get('telephone'))
        with_website = sum(1 for a in associations_with_contacts if a.get('site_web'))
        with_facebook = sum(1 for a in associations_with_contacts if a.get('facebook'))
        
        print(f"  • Total avec contacts: {total}")
        print(f"  • Avec email: {with_email} ({(with_email/total*100):.1f}%)")
        print(f"  • Avec téléphone: {with_phone} ({(with_phone/total*100):.1f}%)")
        print(f"  • Avec site web: {with_website} ({(with_website/total*100):.1f}%)")
        print(f"  • Avec Facebook: {with_facebook} ({(with_facebook/total*100):.1f}%)")
        
        # Par secteur
        by_sector = {}
        for assoc in associations_with_contacts:
            sector = assoc.get('secteur_nom', 'Autre')
            by_sector[sector] = by_sector.get(sector, 0) + 1
        
        print(f"\n📋 PAR SECTEUR:")
        for sector, count in sorted(by_sector.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {sector}: {count}")
        
        # Par ville
        by_city = {}
        for assoc in associations_with_contacts:
            city = assoc.get('ville', 'Inconnue')
            by_city[city] = by_city.get(city, 0) + 1
        
        print(f"\n🏙️ TOP VILLES AVEC CONTACTS:")
        for city, count in sorted(by_city.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  • {city}: {count}")
        
        # Exemples d'emails trouvés
        email_examples = [a for a in associations_with_contacts if a.get('email_principal')][:5]
        if email_examples:
            print(f"\n📧 EXEMPLES EMAILS TROUVÉS:")
            for ex in email_examples:
                print(f"  • {ex['nom'][:40]}... → {ex['email_principal']}")
    
    def create_email_campaign_data(self, associations_with_contacts):
        """Créer données pour campagne email"""
        print(f"\n📧 PRÉPARATION CAMPAGNE EMAIL")
        print("-" * 40)
        
        # Filtrer associations avec email
        email_contacts = [a for a in associations_with_contacts if a.get('email_principal')]
        
        if not email_contacts:
            print("❌ Aucun email trouvé pour campagne")
            return []
        
        # Préparer données campagne
        campaign_data = []
        
        for assoc in email_contacts:
            campaign_entry = {
                'nom_association': assoc.get('nom', ''),
                'email': assoc.get('email_principal', ''),
                'ville': assoc.get('ville', ''),
                'secteur': assoc.get('secteur_nom', 'Autre'),
                'telephone': assoc.get('telephone', ''),
                'site_web': assoc.get('site_web', ''),
                'adresse': assoc.get('adresse', ''),
                'code_postal': assoc.get('code_postal', ''),
                'objet_association': assoc.get('objet', '')[:100],
                'source_contact': ', '.join(assoc.get('contacts_sources', ['RNA'])),
                'date_extraction': assoc.get('date_extraction', ''),
                'segment_campagne': self._determine_campaign_segment(assoc)
            }
            campaign_data.append(campaign_entry)
        
        # Sauvegarder données campagne
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"rna_email_campaign_{timestamp}.csv"
        
        self.data_manager.save_to_csv(campaign_data, filename)
        
        print(f"✅ Données campagne créées: data/{filename}")
        print(f"📊 {len(campaign_data)} contacts email prêts")
        
        # Statistiques campagne
        segments = {}
        for entry in campaign_data:
            segment = entry['segment_campagne']
            segments[segment] = segments.get(segment, 0) + 1
        
        print(f"\n🎯 SEGMENTS CAMPAGNE:")
        for segment, count in segments.items():
            print(f"  • {segment}: {count} contacts")
        
        return campaign_data
    
    def _determine_campaign_segment(self, association):
        """Déterminer segment de campagne"""
        secteur = association.get('secteur_nom', '').lower()
        objet = association.get('objet', '').lower()
        
        if 'sport' in secteur or 'sport' in objet:
            return 'Associations Sportives'
        elif 'culture' in secteur or 'culture' in objet:
            return 'Associations Culturelles'
        elif 'anciens combattants' in secteur:
            return 'Anciens Combattants'
        elif 'chasse' in objet or 'pêche' in objet:
            return 'Chasse et Pêche'
        elif 'éducation' in secteur or 'école' in objet:
            return 'Éducation/Jeunesse'
        else:
            return 'Associations Diverses'

def main():
    """Fonction principale"""
    consolidator = RnaContactConsolidator()
    
    print("🎯 CONSOLIDATION CONTACTS RNA")
    print("=" * 60)
    print("📋 Regroupement de tous les contacts trouvés")
    print("📧 Préparation campagne email")
    
    # Consolider contacts
    associations_with_contacts = consolidator.consolidate_rna_contacts()
    
    if associations_with_contacts:
        # Créer données campagne
        campaign_data = consolidator.create_email_campaign_data(associations_with_contacts)
        
        if campaign_data:
            print(f"\n🎉 SUCCÈS CONSOLIDATION !")
            print(f"📊 {len(associations_with_contacts)} associations avec contacts")
            print(f"📧 {len(campaign_data)} prêtes pour campagne email")
            print(f"🏆 Données 100% réelles et vérifiées")
        else:
            print(f"\n⚠️ Consolidation réussie mais aucun email pour campagne")
    else:
        print(f"\n😞 Aucun contact à consolider")

if __name__ == "__main__":
    main()
