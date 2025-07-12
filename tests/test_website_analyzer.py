import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import requests

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzers.website_analyzer import WebsiteAnalyzer

class TestWebsiteAnalyzer(unittest.TestCase):
    """Tests pour l'analyseur de sites web"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.analyzer = WebsiteAnalyzer()
    
    def test_generate_possible_urls(self):
        """Tester la génération d'URLs possibles"""
        association = {
            'name': 'Association de Formation en Informatique'
        }
        
        urls = self.analyzer.generate_possible_urls(association)
        
        # Vérifier qu'on a plusieurs URLs
        self.assertGreater(len(urls), 0)
        self.assertLessEqual(len(urls), 5)  # Max 5 URLs
        
        # Vérifier le format des URLs
        expected_base = "association-de-formation-en-informatique"
        self.assertIn(f"{expected_base}.fr", urls)
        self.assertIn(f"{expected_base}.asso.fr", urls)
    
    @patch('requests.Session.head')
    def test_check_website_exists_success(self, mock_head):
        """Tester la vérification d'existence de site web - succès"""
        # Mock d'une réponse HTTP 200
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = "https://example.com"
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_head.return_value = mock_response
        
        result = self.analyzer.check_website_exists("https://example.com")
        
        self.assertTrue(result['exists'])
        self.assertEqual(result['status_code'], 200)
        self.assertEqual(result['final_url'], "https://example.com")
        self.assertEqual(result['response_time'], 0.5)
    
    @patch('requests.Session.head')
    def test_check_website_exists_failure(self, mock_head):
        """Tester la vérification d'existence de site web - échec"""
        # Mock d'une réponse HTTP 404
        mock_response = Mock()
        mock_response.status_code = 404
        mock_head.return_value = mock_response
        
        result = self.analyzer.check_website_exists("https://nonexistent.com")
        
        self.assertFalse(result['exists'])
        self.assertEqual(result['status_code'], 404)
    
    @patch('requests.Session.head')
    def test_check_website_exists_timeout(self, mock_head):
        """Tester la vérification avec timeout"""
        # Mock d'une exception de timeout
        mock_head.side_effect = requests.exceptions.Timeout("Timeout")
        
        result = self.analyzer.check_website_exists("https://slow-site.com")
        
        self.assertFalse(result['exists'])
        self.assertIn('error', result)
        self.assertIsNone(result['status_code'])
    
    @patch('requests.Session.get')
    def test_analyze_website_quality_modern(self, mock_get):
        """Tester l'analyse de qualité - site moderne"""
        mock_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link rel="stylesheet" href="bootstrap.min.css">
        </head>
        <body>
            <div class="container-fluid">
                <h1>Site responsive WordPress</h1>
                <p>Site moderne avec CSS responsive</p>
            </div>
        </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Mock check_website_exists pour retourner succès
        with patch.object(self.analyzer, 'check_website_exists') as mock_check:
            mock_check.return_value = {'exists': True, 'status_code': 200}
            
            analysis = self.analyzer.analyze_website_quality("https://modern-site.com")
        
        self.assertTrue(analysis['has_ssl'])  # URL HTTPS
        self.assertTrue(analysis['is_responsive'])  # Contient viewport + bootstrap
        self.assertIn('wordpress', analysis['technology_stack'])
        self.assertGreaterEqual(analysis['performance_score'], 70)
        self.assertTrue(analysis['is_modern'])
    
    @patch('requests.Session.get')
    def test_analyze_website_quality_obsolete(self, mock_get):
        """Tester l'analyse de qualité - site obsolète"""
        mock_html = """
        <html>
        <head>
            <title>Site ancien</title>
        </head>
        <body>
            <h1>Bienvenue</h1>
            <object type="application/x-shockwave-flash">Flash content</object>
            <p>Site sans responsive design</p>
        </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.text = mock_html
        mock_get.return_value = mock_response
        
        with patch.object(self.analyzer, 'check_website_exists') as mock_check:
            mock_check.return_value = {'exists': True, 'status_code': 200}
            
            analysis = self.analyzer.analyze_website_quality("http://old-site.com")
        
        self.assertFalse(analysis['has_ssl'])  # URL HTTP
        self.assertFalse(analysis['is_responsive'])  # Pas de responsive
        self.assertIn('obsolete_flash', analysis['technology_stack'])
        self.assertLess(analysis['performance_score'], 70)
        self.assertFalse(analysis['is_modern'])
    
    def test_check_association_websites(self):
        """Tester l'analyse des sites d'associations"""
        sample_associations = [
            {
                'name': 'Association Moderne',
                'email': 'contact@moderne.fr'
            },
            {
                'name': 'Vieille Association', 
                'email': 'info@vieille.org'
            }
        ]
        
        # Mock des analyses de qualité
        def mock_analyze_quality(url):
            if 'moderne' in url:
                return {
                    'exists': True,
                    'is_modern': True,
                    'has_ssl': True,
                    'performance_score': 85
                }
            else:
                return {
                    'exists': True,
                    'is_modern': False,
                    'has_ssl': False,
                    'performance_score': 30
                }
        
        with patch.object(self.analyzer, 'analyze_website_quality', side_effect=mock_analyze_quality):
            results = self.analyzer.check_association_websites(sample_associations)
        
        self.assertEqual(len(results), 2)
        
        # Vérifier les résultats
        for result in results:
            self.assertIn('website_analysis', result)
            self.assertIn('has_website', result)
            self.assertIn('needs_website', result)
            
            if 'Moderne' in result['name']:
                self.assertTrue(result['has_website'])
                self.assertFalse(result['needs_website'])
            else:
                self.assertTrue(result['has_website'])
                self.assertTrue(result['needs_website'])  # Site obsolète
    
    @patch('os.path.exists')
    @patch('os.listdir')
    def test_batch_analyze_no_files(self, mock_listdir, mock_exists):
        """Tester l'analyse en lot sans fichiers"""
        mock_exists.return_value = False
        
        with patch.object(self.analyzer.data_manager, 'load_from_csv') as mock_load:
            mock_load.return_value = []
            
            result = self.analyzer.batch_analyze("nonexistent.csv")
            
            self.assertIsNone(result)
    
    def test_url_normalization(self):
        """Tester la normalisation des URLs"""
        # Test avec protocole manquant
        result_http = self.analyzer.check_website_exists("example.com")
        # Doit essayer avec https:// par défaut
        
        # Test avec protocole présent
        result_https = self.analyzer.check_website_exists("https://example.com")
        
        # Les deux doivent fonctionner (même si elles échouent par manque de mock)
        self.assertIn('exists', result_http)
        self.assertIn('exists', result_https)

if __name__ == '__main__':
    unittest.main()
