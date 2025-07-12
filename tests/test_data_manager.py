import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_manager import DataManager

class TestDataManager(unittest.TestCase):
    """Tests pour le gestionnaire de données"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.data_manager = DataManager("test_data")
        self.sample_associations = [
            {
                'name': 'Association Test 1',
                'email': 'test1@example.com',
                'department': '18',
                'description': 'Association de formation en informatique',
                'address': 'Bourges 18000',
                'scraping_date': '2025-01-01'
            },
            {
                'name': 'Association Test 2', 
                'email': 'test2@example.com',
                'department': '37',
                'description': 'Festival de musique et culture',
                'address': 'Tours 37000',
                'scraping_date': '2025-01-01'
            },
            {
                'name': 'Association Test 3',
                'email': '',  # Pas d'email
                'department': '45',
                'description': 'Aide aux personnes en difficulté',
                'address': 'Orléans 45000',
                'scraping_date': '2025-01-01'
            }
        ]
    
    def test_save_and_load_csv(self):
        """Tester la sauvegarde et le chargement CSV"""
        # Sauvegarder
        filename = "test_associations.csv"
        self.data_manager.save_to_csv(self.sample_associations, filename)
        
        # Charger
        loaded_data = self.data_manager.load_from_csv(filename)
        
        # Vérifications
        self.assertEqual(len(loaded_data), len(self.sample_associations))
        self.assertEqual(loaded_data[0]['name'], 'Association Test 1')
        self.assertEqual(loaded_data[1]['email'], 'test2@example.com')
    
    def test_filter_associations_by_department(self):
        """Tester le filtrage par département"""
        criteria = {'departments': ['18', '37']}
        filtered = self.data_manager.filter_associations(self.sample_associations, criteria)
        
        self.assertEqual(len(filtered), 2)
        departments = [assoc['department'] for assoc in filtered]
        self.assertIn('18', departments)
        self.assertIn('37', departments)
        self.assertNotIn('45', departments)
    
    def test_filter_associations_by_sector(self):
        """Tester le filtrage par secteur"""
        criteria = {'sectors': ['formation', 'culture']}
        filtered = self.data_manager.filter_associations(self.sample_associations, criteria)
        
        self.assertEqual(len(filtered), 2)  # Les 2 premières associations
    
    def test_filter_associations_with_email(self):
        """Tester le filtrage avec email uniquement"""
        criteria = {'has_email': True}
        filtered = self.data_manager.filter_associations(self.sample_associations, criteria)
        
        self.assertEqual(len(filtered), 2)  # Seulement celles avec email
        for assoc in filtered:
            self.assertTrue(assoc.get('email'))
    
    def test_detect_sector(self):
        """Tester la détection de secteur"""
        # Test formation
        assoc_formation = {'name': 'École de formation', 'description': 'Cours d\'informatique'}
        sector = self.data_manager.detect_sector(assoc_formation)
        self.assertEqual(sector, 'education')
        
        # Test culture
        assoc_culture = {'name': 'Festival de jazz', 'description': 'Musique et art'}
        sector = self.data_manager.detect_sector(assoc_culture)
        self.assertEqual(sector, 'culture')
        
        # Test caritatif
        assoc_caritatif = {'name': 'Aide humanitaire', 'description': 'Solidarité sociale'}
        sector = self.data_manager.detect_sector(assoc_caritatif)
        self.assertEqual(sector, 'caritatif')
    
    def test_export_for_outreach(self):
        """Tester l'export pour prospection"""
        # Utiliser seulement les associations avec email
        valid_associations = [assoc for assoc in self.sample_associations if assoc.get('email')]
        
        exported = self.data_manager.export_for_outreach(valid_associations, "test_outreach.csv")
        
        self.assertEqual(len(exported), 2)
        self.assertIn('Nom', exported[0].keys())
        self.assertIn('Email', exported[0].keys())
        self.assertIn('Secteur_Detecte', exported[0].keys())
    
    def test_get_stats(self):
        """Tester les statistiques"""
        stats = self.data_manager.get_stats(self.sample_associations)
        
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['with_email'], 2)
        self.assertIn('18', stats['by_department'])
        self.assertIn('education', stats['by_sector'])
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        # Supprimer les fichiers de test créés
        import glob
        test_files = glob.glob("test_data/*.csv") + glob.glob("output/test_*.csv")
        for file in test_files:
            try:
                os.remove(file)
            except:
                pass

if __name__ == '__main__':
    unittest.main()
