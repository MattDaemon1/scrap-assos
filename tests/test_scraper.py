import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import requests

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.journal_officiel_scraper import JournalOfficielScraper

class TestJournalOfficielScraper(unittest.TestCase):
    """Tests pour le scraper du Journal Officiel"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.scraper = JournalOfficielScraper()
    
    def test_extract_email(self):
        """Tester l'extraction d'email"""
        # Test avec email valide
        text_with_email = "Contactez-nous à contact@association.fr pour plus d'infos"
        email = self.scraper.extract_email(text_with_email)
        self.assertEqual(email, "contact@association.fr")
        
        # Test sans email
        text_without_email = "Aucun email dans ce texte"
        email = self.scraper.extract_email(text_without_email)
        self.assertEqual(email, "")
        
        # Test avec plusieurs emails (doit prendre le premier)
        text_multiple_emails = "contact@asso.fr et admin@asso.org"
        email = self.scraper.extract_email(text_multiple_emails)
        self.assertEqual(email, "contact@asso.fr")
    
    def test_extract_department(self):
        """Tester l'extraction du département"""
        # Test avec code postal valide
        address_with_postal = "123 rue de la Paix, 75001 Paris"
        dept = self.scraper.extract_department(address_with_postal)
        self.assertEqual(dept, "75")
        
        # Test avec Bourges (18000)
        address_bourges = "Association XYZ, 18000 Bourges"
        dept = self.scraper.extract_department(address_bourges)
        self.assertEqual(dept, "18")
        
        # Test sans code postal
        address_no_postal = "Quelque part en France"
        dept = self.scraper.extract_department(address_no_postal)
        self.assertEqual(dept, "")
    
    @patch('requests.Session.get')
    def test_scrape_associations_mock(self, mock_get):
        """Tester le scraping avec des données mockées"""
        # Mock HTML response
        mock_html = """
        <html>
            <div class="association-item">
                <h3>Association Test Formation</h3>
                <p class="description">Cours d'informatique et formation</p>
                <div class="adresse">123 rue Test, 18000 Bourges</div>
                <span class="date">2025-01-01</span>
                <a href="/detail/123">Voir détails</a>
                contact@test-formation.fr
            </div>
            <div class="association-item">
                <h3>Club de Culture</h3>
                <p class="description">Festival de musique locale</p>
                <div class="adresse">456 avenue Culture, 37000 Tours</div>
                <span class="date">2025-01-02</span>
                <a href="/detail/456">Voir détails</a>
            </div>
        </html>
        """
        
        # Configuration du mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = mock_html.encode('utf-8')
        mock_get.return_value = mock_response
        
        # Test du scraping
        associations = self.scraper.scrape_associations(
            department="18",
            sector_keywords=["formation", "culture"],
            max_pages=1
        )
        
        # Vérifications
        self.assertGreaterEqual(len(associations), 1)
        
        # Vérifier qu'au moins une association contient les bonnes données
        formation_found = False
        for assoc in associations:
            if "formation" in assoc.get('name', '').lower():
                formation_found = True
                self.assertIn("18", assoc.get('department', ''))
                self.assertIn("formation", assoc.get('description', '').lower())
        
        # Au moins une association de formation doit être trouvée
        self.assertTrue(formation_found, "Aucune association de formation trouvée")
    
    @patch('requests.Session.get')
    def test_scrape_with_http_error(self, mock_get):
        """Tester le comportement en cas d'erreur HTTP"""
        # Mock d'une erreur 404
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        associations = self.scraper.scrape_associations(max_pages=1)
        
        # Doit retourner une liste vide en cas d'erreur
        self.assertEqual(len(associations), 0)
    
    def test_extract_association_data_with_sector_filter(self):
        """Tester l'extraction avec filtrage par secteur"""
        from bs4 import BeautifulSoup
        
        # HTML d'une association de formation
        html_formation = """
        <div class="association-item">
            <h3>École Informatique</h3>
            <p class="description">Formation en programmation et développement web</p>
            <div class="adresse">18000 Bourges</div>
            <span class="date">2025-01-01</span>
            <a href="/detail">Détails</a>
        </div>
        """
        
        # HTML d'une association politique (à exclure)
        html_politique = """
        <div class="association-item">
            <h3>Parti Politique Local</h3>
            <p class="description">Mouvement politique démocratique</p>
            <div class="adresse">18000 Bourges</div>
            <span class="date">2025-01-01</span>
            <a href="/detail">Détails</a>
        </div>
        """
        
        soup_formation = BeautifulSoup(html_formation, 'html.parser')
        soup_politique = BeautifulSoup(html_politique, 'html.parser')
        
        # Test avec filtrage par secteur
        sector_keywords = ["formation", "culture", "caritatif"]
        
        # L'association de formation doit passer le filtre
        association_formation = self.scraper.extract_association_data(
            soup_formation.find('div'), sector_keywords
        )
        self.assertIsNotNone(association_formation)
        self.assertIn("formation", association_formation['description'].lower())
        
        # L'association politique doit être filtrée
        association_politique = self.scraper.extract_association_data(
            soup_politique.find('div'), sector_keywords
        )
        self.assertIsNone(association_politique)
    
    @patch('requests.Session.get')
    def test_scrape_detailed_info(self, mock_get):
        """Tester le scraping d'informations détaillées"""
        mock_html = """
        <html>
            <body>
                <p>Plus d'infos: contact@asso.fr</p>
                <p>Site web: <a href="https://www.asso-example.fr">Notre site</a></p>
                <p>Email secondaire: admin@asso.fr</p>
                <a href="https://facebook.com/asso">Facebook</a>
                <a href="https://www.asso-site.org">Site officiel</a>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = mock_html.encode('utf-8')
        mock_get.return_value = mock_response
        
        details = self.scraper.scrape_detailed_info("https://example.com/detail")
        
        # Vérifier qu'on a trouvé des emails
        self.assertIn('emails', details)
        self.assertGreater(len(details['emails']), 0)
        
        # Vérifier qu'on a trouvé des sites web (sans les réseaux sociaux)
        self.assertIn('websites', details)
        websites = details['websites']
        
        # Ne doit pas contenir Facebook
        facebook_found = any('facebook' in site for site in websites)
        self.assertFalse(facebook_found)

if __name__ == '__main__':
    unittest.main()
