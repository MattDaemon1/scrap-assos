import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from email_manager.campaign_manager import EmailCampaignManager

class TestEmailCampaignManager(unittest.TestCase):
    """Tests pour le gestionnaire de campagnes email"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.campaign_manager = EmailCampaignManager()
        self.sample_sender = {
            'prenom': 'Jean',
            'nom': 'Dupont',
            'telephone': '06.12.34.56.78',
            'email': 'jean.dupont@example.com'
        }
        self.sample_association = {
            'Nom': 'Association Test Formation',
            'Email': 'contact@test-formation.fr',
            'Département': '18',
            'Secteur_Detecte': 'education'
        }
    
    def test_load_templates(self):
        """Tester le chargement des templates"""
        # Les templates doivent être chargés
        self.assertIsInstance(self.campaign_manager.templates, dict)
        
        # Vérifier qu'on a au moins le template 1
        if 1 in self.campaign_manager.templates:
            template = self.campaign_manager.templates[1]
            self.assertIn('subject', template)
            self.assertIn('body', template)
            self.assertIsInstance(template['subject'], str)
            self.assertIsInstance(template['body'], str)
    
    def test_personalize_email_template_1(self):
        """Tester la personnalisation du template 1"""
        if 1 not in self.campaign_manager.templates:
            self.skipTest("Template 1 non disponible")
        
        personalized = self.campaign_manager.personalize_email(
            1, self.sample_association, self.sample_sender
        )
        
        # Vérifier les champs obligatoires
        self.assertIn('subject', personalized)
        self.assertIn('body', personalized)
        self.assertIn('recipient', personalized)
        self.assertIn('recipient_name', personalized)
        
        # Vérifier que les variables ont été remplacées
        self.assertIn('Association Test Formation', personalized['subject'])
        self.assertIn('Jean', personalized['body'])
        self.assertIn('Dupont', personalized['body'])
        self.assertEqual(personalized['recipient'], 'contact@test-formation.fr')
        
        # Vérifier qu'il ne reste pas de placeholders
        self.assertNotIn('{{', personalized['subject'])
        self.assertNotIn('{{', personalized['body'])
    
    def test_get_department_name(self):
        """Tester la conversion code département -> nom"""
        # Test départements Centre-Val de Loire
        self.assertEqual(self.campaign_manager.get_department_name('18'), 'Cher')
        self.assertEqual(self.campaign_manager.get_department_name('37'), 'Indre-et-Loire')
        self.assertEqual(self.campaign_manager.get_department_name('45'), 'Loiret')
        
        # Test département inconnu
        result = self.campaign_manager.get_department_name('99')
        self.assertIn('99', result)
    
    @patch('os.path.exists')
    def test_create_campaign_plan_no_file(self, mock_exists):
        """Tester création de campagne sans fichier"""
        mock_exists.return_value = False
        
        with patch.object(self.campaign_manager.data_manager, 'load_from_csv') as mock_load:
            mock_load.return_value = []
            
            result = self.campaign_manager.create_campaign_plan("nonexistent.csv")
            self.assertIsNone(result)
    
    def test_create_campaign_plan_with_prospects(self):
        """Tester création de campagne avec prospects"""
        sample_prospects = [
            {
                'Nom': 'Association A',
                'Email': 'a@example.com',
                'Département': '18',
                'Secteur_Detecte': 'education'
            },
            {
                'Nom': 'Association B', 
                'Email': 'b@example.com',
                'Département': '37',
                'Secteur_Detecte': 'culture'
            },
            {
                'Nom': 'Association C',
                'Email': '',  # Pas d'email
                'Département': '45',
                'Secteur_Detecte': 'caritatif'
            }
        ]
        
        with patch.object(self.campaign_manager.data_manager, 'load_from_csv') as mock_load:
            with patch.object(self.campaign_manager, 'save_campaign_plan') as mock_save:
                mock_load.return_value = sample_prospects
                
                plan = self.campaign_manager.create_campaign_plan("test.csv")
                
                # Seulement les prospects avec email
                self.assertEqual(len(plan), 2)
                
                # Vérifier la structure du plan
                for item in plan:
                    self.assertIn('prospect', item)
                    self.assertIn('template', item)
                    self.assertIn('send_date', item)
                    self.assertIn('status', item)
                    self.assertEqual(item['template'], 1)  # Template 1 par défaut
                    self.assertEqual(item['status'], 'planned')
    
    def test_preview_emails(self):
        """Tester la prévisualisation des emails"""
        if 1 not in self.campaign_manager.templates:
            self.skipTest("Template 1 non disponible")
        
        sample_plan = [
            {
                'prospect': self.sample_association,
                'template': 1,
                'send_date': '2025-01-15',
                'status': 'planned'
            }
        ]
        
        # Capturer la sortie (pas d'exception = succès)
        try:
            self.campaign_manager.preview_emails(sample_plan, self.sample_sender, max_preview=1)
            preview_success = True
        except Exception:
            preview_success = False
        
        self.assertTrue(preview_success)
    
    def test_personalize_email_missing_template(self):
        """Tester personnalisation avec template inexistant"""
        with self.assertRaises(ValueError):
            self.campaign_manager.personalize_email(
                999, self.sample_association, self.sample_sender
            )
    
    def test_campaign_plan_daily_limit_respect(self):
        """Tester le respect de la limite quotidienne"""
        # Créer 400 prospects (plus que la limite de 300/jour)
        many_prospects = []
        for i in range(400):
            many_prospects.append({
                'Nom': f'Association {i}',
                'Email': f'contact{i}@example.com',
                'Département': '18'
            })
        
        with patch.object(self.campaign_manager.data_manager, 'load_from_csv') as mock_load:
            with patch.object(self.campaign_manager, 'save_campaign_plan') as mock_save:
                mock_load.return_value = many_prospects
                
                plan = self.campaign_manager.create_campaign_plan("test.csv")
                
                # Vérifier que les dates d'envoi sont étalées
                send_dates = [item['send_date'] for item in plan]
                unique_dates = set(send_dates)
                
                # Doit y avoir au moins 2 dates différentes
                self.assertGreaterEqual(len(unique_dates), 2)
                
                # Compter les emails par date
                from collections import Counter
                date_counts = Counter(send_dates)
                
                # Aucune date ne doit dépasser la limite
                for count in date_counts.values():
                    self.assertLessEqual(count, 300)  # DAILY_EMAIL_LIMIT
    
    def test_variable_replacement_edge_cases(self):
        """Tester les cas limites de remplacement des variables"""
        if 1 not in self.campaign_manager.templates:
            self.skipTest("Template 1 non disponible")
        
        # Association avec données manquantes
        incomplete_association = {
            'Nom': '',  # Nom vide
            'Email': 'test@example.com',
            'Département': '',  # Département vide
            'Secteur_Detecte': ''  # Secteur vide
        }
        
        personalized = self.campaign_manager.personalize_email(
            1, incomplete_association, self.sample_sender
        )
        
        # Ne doit pas contenir de placeholders non remplacés
        self.assertNotIn('{{', personalized['subject'])
        self.assertNotIn('{{', personalized['body'])
        
        # Doit contenir des valeurs par défaut
        self.assertIn('association', personalized['subject'].lower())

if __name__ == '__main__':
    unittest.main()
