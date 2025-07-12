import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import *

class TestIntegration(unittest.TestCase):
    """Tests d'intégration pour le workflow complet"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.sample_raw_data = [
            {
                'name': 'École Numérique Bourges',
                'email': 'contact@ecole-num-bourges.fr',
                'department': '18',
                'description': 'Formation en informatique et développement web',
                'address': '123 rue de la Formation, 18000 Bourges',
                'scraping_date': '2025-01-01',
                'status': 'new'
            },
            {
                'name': 'Festival Culture Tours',
                'email': 'info@festival-tours.fr', 
                'department': '37',
                'description': 'Festival annuel de musique et arts du spectacle',
                'address': '456 avenue des Arts, 37000 Tours',
                'scraping_date': '2025-01-01',
                'status': 'new'
            },
            {
                'name': 'Solidarité Orléans',
                'email': '',  # Pas d'email
                'department': '45',
                'description': 'Aide alimentaire et soutien aux familles en difficulté',
                'address': 'Orléans 45000',
                'scraping_date': '2025-01-01',
                'status': 'new'
            }
        ]
    
    def test_full_workflow_simulation(self):
        """Tester le workflow complet de scraping à la campagne email"""
        # Import des modules
        from utils.data_manager import DataManager
        from analyzers.website_analyzer import WebsiteAnalyzer
        from email_manager.campaign_manager import EmailCampaignManager
        
        # Étape 1: Simulation du scraping (données déjà prêtes)
        data_manager = DataManager("test_integration")
        
        # Sauvegarder les données de test
        data_manager.save_to_csv(self.sample_raw_data, "scraped_associations.csv")
        
        # Étape 2: Filtrage des données selon les critères
        filtered_data = data_manager.filter_associations(
            self.sample_raw_data,
            {
                'departments': PRIORITY_REGIONS,
                'sectors': TARGET_SECTORS,
                'has_email': False  # Garder même sans email pour l'analyse
            }
        )
        
        # Vérifier le filtrage
        self.assertEqual(len(filtered_data), 3)  # Toutes passent les critères
        
        # Étape 3: Simulation de l'analyse des sites web
        analyzer = WebsiteAnalyzer()
        
        def mock_analyze_quality(url):
            if 'ecole-num-bourges' in url:
                return {
                    'exists': True,
                    'is_modern': False,  # Site obsolète
                    'has_ssl': False,
                    'performance_score': 30
                }
            elif 'festival-tours' in url:
                return {
                    'exists': False,  # Pas de site
                    'error': 'Site inaccessible'
                }
            else:
                return {
                    'exists': True,
                    'is_modern': True,  # Site moderne
                    'has_ssl': True,
                    'performance_score': 85
                }
        
        # Simuler l'analyse des sites
        with patch.object(analyzer, 'analyze_website_quality', side_effect=mock_analyze_quality):
            analyzed_data = analyzer.check_association_websites(filtered_data)
        
        # Vérifier les résultats de l'analyse
        self.assertEqual(len(analyzed_data), 3)
        
        # École Numérique: site obsolète -> besoin nouveau site
        ecole = next(a for a in analyzed_data if 'École' in a['name'])
        self.assertTrue(ecole['needs_website'])
        
        # Festival: pas de site -> besoin nouveau site
        festival = next(a for a in analyzed_data if 'Festival' in a['name'])
        self.assertTrue(festival['needs_website'])
        
        # Solidarité: site moderne -> pas besoin
        solidarite = next(a for a in analyzed_data if 'Solidarité' in a['name'])
        self.assertFalse(solidarite['needs_website'])
        
        # Étape 4: Export des prospects qualifiés
        prospects = [a for a in analyzed_data if a.get('needs_website') and a.get('email')]
        qualified_prospects = data_manager.export_for_outreach(prospects, "test_prospects.csv")
        
        # Vérifier les prospects qualifiés (seulement ceux avec email ET besoin)
        self.assertEqual(len(qualified_prospects), 2)  # École + Festival
        
        # Étape 5: Création de campagne email
        campaign_manager = EmailCampaignManager()
        
        sender_info = {
            'prenom': 'Test',
            'nom': 'Testeur',
            'telephone': '06.00.00.00.00',
            'email': 'test@example.com'
        }
        
        # Simuler la création du plan de campagne
        with patch.object(campaign_manager.data_manager, 'load_from_csv') as mock_load:
            with patch.object(campaign_manager, 'save_campaign_plan') as mock_save:
                mock_load.return_value = qualified_prospects
                
                campaign_plan = campaign_manager.create_campaign_plan("test_prospects.csv")
                
                # Vérifier le plan de campagne
                self.assertEqual(len(campaign_plan), 2)
                
                for item in campaign_plan:
                    self.assertEqual(item['template'], 1)
                    self.assertEqual(item['status'], 'planned')
                    self.assertIn('send_date', item)
    
    def test_data_flow_consistency(self):
        """Tester la cohérence des données à travers le pipeline"""
        from utils.data_manager import DataManager
        
        data_manager = DataManager("test_consistency")
        
        # Test de round-trip: sauvegarder -> charger -> vérifier
        original_data = self.sample_raw_data
        data_manager.save_to_csv(original_data, "roundtrip_test.csv")
        loaded_data = data_manager.load_from_csv("roundtrip_test.csv")
        
        # Vérifier que les données sont identiques
        self.assertEqual(len(loaded_data), len(original_data))
        
        for orig, loaded in zip(original_data, loaded_data):
            self.assertEqual(orig['name'], loaded['name'])
            self.assertEqual(orig['email'], loaded['email'])
            self.assertEqual(orig['department'], loaded['department'])
    
    def test_configuration_validation(self):
        """Tester la validité de la configuration"""
        # Vérifier que les constantes sont définies
        self.assertIsNotNone(TARGET_SECTORS)
        self.assertIsInstance(TARGET_SECTORS, list)
        self.assertGreater(len(TARGET_SECTORS), 0)
        
        self.assertIsNotNone(PRIORITY_REGIONS)
        self.assertIsInstance(PRIORITY_REGIONS, list)
        self.assertGreater(len(PRIORITY_REGIONS), 0)
        
        # Vérifier les valeurs numériques
        self.assertIsInstance(MIN_BUDGET, int)
        self.assertIsInstance(MAX_BUDGET, int)
        self.assertGreater(MAX_BUDGET, MIN_BUDGET)
        
        self.assertIsInstance(DAILY_EMAIL_LIMIT, int)
        self.assertGreater(DAILY_EMAIL_LIMIT, 0)
        
        # Vérifier les URLs
        self.assertTrue(JOURNAL_OFFICIEL_URL.startswith('http'))
        self.assertTrue(HELLOASSO_URL.startswith('http'))
    
    def test_error_handling_workflow(self):
        """Tester la gestion d'erreurs dans le workflow"""
        from utils.data_manager import DataManager
        from analyzers.website_analyzer import WebsiteAnalyzer
        
        data_manager = DataManager("test_errors")
        analyzer = WebsiteAnalyzer()
        
        # Test avec données corrompues
        corrupted_data = [
            {
                'name': None,  # Nom invalide
                'email': 'invalid-email',  # Email invalide
                'department': '',  # Département manquant
                'description': '',
                'address': '',
            }
        ]
        
        # Le système doit gérer les données corrompues sans planter
        try:
            filtered = data_manager.filter_associations(corrupted_data, {
                'departments': ['18'],
                'has_email': True
            })
            # Doit filtrer les données invalides
            self.assertEqual(len(filtered), 0)
            error_handling_ok = True
        except Exception as e:
            error_handling_ok = False
        
        self.assertTrue(error_handling_ok, "La gestion d'erreur a échoué")
    
    def test_performance_scalability(self):
        """Tester les performances avec de gros volumes"""
        from utils.data_manager import DataManager
        
        data_manager = DataManager("test_performance")
        
        # Générer 1000 associations test
        large_dataset = []
        for i in range(1000):
            large_dataset.append({
                'name': f'Association Test {i}',
                'email': f'test{i}@example.com',
                'department': '18',
                'description': f'Description {i}',
                'address': f'Adresse {i}',
                'scraping_date': '2025-01-01'
            })
        
        # Tester la sauvegarde/chargement
        import time
        start_time = time.time()
        
        data_manager.save_to_csv(large_dataset, "large_test.csv")
        loaded_large = data_manager.load_from_csv("large_test.csv")
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Vérifier les données
        self.assertEqual(len(loaded_large), 1000)
        
        # Vérifier les performances (moins de 5 secondes pour 1000 entrées)
        self.assertLess(processing_time, 5.0, 
                       f"Performance trop lente: {processing_time:.2f}s pour 1000 entrées")

if __name__ == '__main__':
    unittest.main()
