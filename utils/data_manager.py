import csv
import pandas as pd
import os
from datetime import datetime
import json

class DataManager:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.ensure_directories()
        
    def ensure_directories(self):
        """Créer les dossiers nécessaires"""
        directories = [self.data_dir, "output", "templates"]
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
    
    def save_to_csv(self, data, filename):
        """Sauvegarder les données en CSV"""
        filepath = os.path.join(self.data_dir, filename)
        
        if not data:
            print("Aucune donnée à sauvegarder")
            return
        
        # Obtenir toutes les clés possibles de tous les éléments
        all_fieldnames = set()
        for item in data:
            all_fieldnames.update(item.keys())
        
        # Ordonner les champs
        fieldnames = sorted(all_fieldnames)
        
        # S'assurer que tous les éléments ont tous les champs
        for item in data:
            for field in fieldnames:
                if field not in item:
                    item[field] = ''  # Valeur par défaut
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            print(f"Données sauvegardées dans {filepath}")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde: {e}")
    
    def load_from_csv(self, filename):
        """Charger les données depuis un CSV"""
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"Fichier non trouvé: {filepath}")
            return []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                return list(reader)
        except Exception as e:
            print(f"Erreur lors du chargement: {e}")
            return []
    
    def merge_csv_files(self, output_filename="merged_associations.csv"):
        """Fusionner tous les fichiers CSV d'associations"""
        all_data = []
        
        for filename in os.listdir(self.data_dir):
            if filename.startswith("associations_") and filename.endswith(".csv"):
                filepath = os.path.join(self.data_dir, filename)
                data = self.load_from_csv(filename)
                all_data.extend(data)
        
        if all_data:
            # Supprimer les doublons basés sur le nom et l'email
            seen = set()
            unique_data = []
            for item in all_data:
                key = (item.get('name', ''), item.get('email', ''))
                if key not in seen:
                    seen.add(key)
                    unique_data.append(item)
            
            self.save_to_csv(unique_data, output_filename)
            print(f"Fusionné {len(unique_data)} associations uniques dans {output_filename}")
            return unique_data
        
        return []
    
    def filter_associations(self, data, criteria):
        """Filtrer les associations selon des critères"""
        filtered = []
        
        for association in data:
            if self.meets_criteria(association, criteria):
                filtered.append(association)
        
        return filtered
    
    def meets_criteria(self, association, criteria):
        """Vérifier si une association répond aux critères"""
        # Vérifier le département
        if 'departments' in criteria:
            dept = association.get('department', '')
            if dept not in criteria['departments']:
                return False
        
        # Vérifier les mots-clés du secteur
        if 'sectors' in criteria:
            text = (association.get('name', '') + ' ' + 
                   association.get('description', '')).lower()
            found_sector = any(sector.lower() in text for sector in criteria['sectors'])
            if not found_sector:
                return False
        
        # Vérifier la présence d'email
        if criteria.get('has_email', False):
            if not association.get('email'):
                return False
        
        return True
    
    def export_for_outreach(self, data, filename="leads_for_outreach.csv"):
        """Exporter les données formatées pour la prospection"""
        outreach_data = []
        
        for association in data:
            if association.get('email'):  # Seulement ceux avec email
                outreach_item = {
                    'Nom': association.get('name', ''),
                    'Email': association.get('email', ''),
                    'Adresse': association.get('address', ''),
                    'Département': association.get('department', ''),
                    'Description': association.get('description', '')[:200] + '...' if len(association.get('description', '')) > 200 else association.get('description', ''),
                    'Secteur_Detecte': self.detect_sector(association),
                    'Statut': 'À contacter',
                    'Date_Export': datetime.now().strftime('%Y-%m-%d'),
                    'Notes': ''
                }
                outreach_data.append(outreach_item)
        
        output_path = os.path.join("output", filename)
        self.save_to_csv_direct(outreach_data, output_path)
        return outreach_data
    
    def detect_sector(self, association):
        """Détecter le secteur principal d'une association"""
        text = (association.get('name', '') + ' ' + 
               association.get('description', '')).lower()
        
        sector_map = {
            'education': ['formation', 'education', 'enseignement', 'cours', 'école'],
            'culture': ['culture', 'festival', 'théâtre', 'musique', 'art'],
            'caritatif': ['caritatif', 'solidarité', 'aide', 'social', 'humanitaire'],
            'environnement': ['environnement', 'nature', 'écologie', 'animaux']
        }
        
        for sector, keywords in sector_map.items():
            if any(keyword in text for keyword in keywords):
                return sector
        
        return 'autre'
    
    def save_to_csv_direct(self, data, filepath):
        """Sauvegarder directement avec chemin complet"""
        if not data:
            return
        
        fieldnames = data[0].keys()
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            print(f"Export réussi: {filepath}")
        except Exception as e:
            print(f"Erreur lors de l'export: {e}")
    
    def get_stats(self, data):
        """Obtenir des statistiques sur les données"""
        if not data:
            return {}
        
        stats = {
            'total': len(data),
            'with_email': len([d for d in data if d.get('email')]),
            'by_department': {},
            'by_sector': {}
        }
        
        for item in data:
            # Stats par département
            dept = item.get('department', 'inconnu')
            stats['by_department'][dept] = stats['by_department'].get(dept, 0) + 1
            
            # Stats par secteur
            sector = self.detect_sector(item)
            stats['by_sector'][sector] = stats['by_sector'].get(sector, 0) + 1
        
        return stats
