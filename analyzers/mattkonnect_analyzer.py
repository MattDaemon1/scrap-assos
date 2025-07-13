import requests
import time
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_manager import DataManager

class SimpleWebsiteAnalyzer:
    def __init__(self):
        self.data_manager = DataManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def analyze_website(self, url):
        """Analyser un site web de manière complète"""
        print(f"🔍 Analyse de: {url}")
        
        analysis = {
            'url': url,
            'accessible': False,
            'status_code': None,
            'response_time': 0,
            'has_ssl': False,
            'content_length': 0,
            'has_viewport': False,
            'has_modern_framework': False,
            'has_outdated_design': False,
            'performance_score': 0,
            'technical_issues': [],
            'recommendations': [],
            'overall_score': 0
        }
        
        try:
            # Test d'accessibilité
            print("  📡 Test d'accessibilité...")
            start_time = time.time()
            response = self.session.get(url, timeout=10)
            response_time = time.time() - start_time
            
            analysis.update({
                'accessible': response.status_code < 400,
                'status_code': response.status_code,
                'response_time': round(response_time, 2),
                'has_ssl': url.startswith('https://'),
                'content_length': len(response.content)
            })
            
            print(f"    ✅ Status: {response.status_code}")
            print(f"    ⏱️ Temps: {response_time:.2f}s")
            
            if response.status_code == 200:
                # Analyser le contenu HTML
                print("  🔍 Analyse du contenu...")
                content = response.text.lower()
                
                # Tests techniques
                analysis['has_viewport'] = 'viewport' in content and 'width=device-width' in content
                analysis['has_modern_framework'] = any(framework in content for framework in [
                    'bootstrap', 'react', 'vue', 'angular', 'tailwind', 'css grid', 'flexbox'
                ])
                analysis['has_outdated_design'] = any(old in content for old in [
                    'table border=', 'font face=', 'bgcolor=', '<marquee', '<blink'
                ])
                
                # Score de performance
                perf_score = 10
                if response_time > 3:
                    perf_score -= 3
                    analysis['technical_issues'].append('Temps de chargement lent (>3s)')
                elif response_time > 2:
                    perf_score -= 1
                    analysis['technical_issues'].append('Temps de chargement moyen (>2s)')
                
                if not analysis['has_ssl']:
                    perf_score -= 2
                    analysis['technical_issues'].append('Pas de certificat SSL (HTTPS)')
                
                if not analysis['has_viewport']:
                    perf_score -= 2
                    analysis['technical_issues'].append('Pas de viewport mobile')
                
                if analysis['has_outdated_design']:
                    perf_score -= 3
                    analysis['technical_issues'].append('Éléments de design obsolètes')
                
                if not analysis['has_modern_framework']:
                    perf_score -= 1
                    analysis['technical_issues'].append('Framework/CSS daté')
                
                analysis['performance_score'] = max(0, perf_score)
                
                # Génération des recommandations
                analysis['recommendations'] = self.generate_recommendations(analysis)
                
                # Score global
                analysis['overall_score'] = self.calculate_overall_score(analysis)
                
                print(f"    📊 Score performance: {analysis['performance_score']}/10")
                print(f"    🎯 Score global: {analysis['overall_score']}/10")
            
        except Exception as e:
            analysis['technical_issues'].append(f'Erreur d\'analyse: {str(e)}')
            print(f"    ❌ Erreur: {e}")
        
        return analysis
    
    def generate_recommendations(self, analysis):
        """Générer des recommandations d'amélioration"""
        recommendations = []
        
        if analysis['response_time'] > 2:
            recommendations.append("⚡ Optimiser la vitesse de chargement (compression, cache, CDN)")
        
        if not analysis['has_ssl']:
            recommendations.append("🔒 Implémenter un certificat SSL/HTTPS")
        
        if not analysis['has_viewport']:
            recommendations.append("📱 Ajouter le viewport mobile pour la responsivité")
        
        if not analysis['has_modern_framework']:
            recommendations.append("🔧 Moderniser le CSS/Framework (Bootstrap, Tailwind)")
        
        if analysis['has_outdated_design']:
            recommendations.append("🎨 Éliminer les éléments de design obsolètes")
        
        if analysis['performance_score'] < 7:
            recommendations.append("🚀 Audit technique complet recommandé")
        
        if not recommendations:
            recommendations.append("✨ Site bien optimisé ! Maintenance régulière recommandée")
        
        return recommendations
    
    def calculate_overall_score(self, analysis):
        """Calculer le score global du site"""
        score = 0
        
        # Accessibilité (2 points)
        if analysis['accessible']:
            score += 2
        
        # SSL (1 point)
        if analysis['has_ssl']:
            score += 1
        
        # Performance (3 points)
        if analysis['response_time'] < 1:
            score += 3
        elif analysis['response_time'] < 2:
            score += 2
        elif analysis['response_time'] < 3:
            score += 1
        
        # Mobile/Responsive (2 points)
        if analysis['has_viewport']:
            score += 2
        
        # Framework moderne (1 point)
        if analysis['has_modern_framework']:
            score += 1
        
        # Pas d'éléments obsolètes (1 point)
        if not analysis['has_outdated_design']:
            score += 1
        
        return score

def test_mattkonnect_analysis():
    """Test spécifique pour le site MattKonnect"""
    analyzer = SimpleWebsiteAnalyzer()
    
    print("🚀 ANALYSE TECHNIQUE - MATTKONNECT.COM")
    print("=" * 50)
    
    # Analyser le site principal
    analysis = analyzer.analyze_website("https://www.mattkonnect.com")
    
    # Affichage détaillé
    print(f"\n📊 RÉSULTATS DÉTAILLÉS")
    print("=" * 30)
    print(f"URL: {analysis['url']}")
    print(f"Accessible: {'✅ Oui' if analysis['accessible'] else '❌ Non'}")
    print(f"Status HTTP: {analysis['status_code']}")
    print(f"Temps de réponse: {analysis['response_time']}s")
    print(f"HTTPS/SSL: {'✅ Oui' if analysis['has_ssl'] else '❌ Non'}")
    print(f"Viewport mobile: {'✅ Oui' if analysis['has_viewport'] else '❌ Non'}")
    print(f"Framework moderne: {'✅ Oui' if analysis['has_modern_framework'] else '❌ Non'}")
    print(f"Design obsolète: {'❌ Oui' if analysis['has_outdated_design'] else '✅ Non'}")
    
    print(f"\n🎯 SCORES")
    print(f"Performance: {analysis['performance_score']}/10")
    print(f"Global: {analysis['overall_score']}/10")
    
    if analysis['technical_issues']:
        print(f"\n⚠️ PROBLÈMES DÉTECTÉS:")
        for issue in analysis['technical_issues']:
            print(f"  • {issue}")
    
    if analysis['recommendations']:
        print(f"\n💡 RECOMMANDATIONS:")
        for rec in analysis['recommendations']:
            print(f"  • {rec}")
    
    # Déterminer le statut prospect
    print(f"\n🎯 ÉVALUATION PROSPECT")
    if analysis['overall_score'] >= 8:
        prospect_status = "✅ Site excellent - Maintenance/SEO uniquement"
        priority = 3
    elif analysis['overall_score'] >= 6:
        prospect_status = "⚡ Site correct - Optimisations recommandées"
        priority = 5
    elif analysis['overall_score'] >= 4:
        prospect_status = "🎯 PROSPECT - Améliorations importantes nécessaires"
        priority = 7
    else:
        prospect_status = "🚨 PROSPECT PRIORITAIRE - Refonte recommandée"
        priority = 9
    
    print(f"Statut: {prospect_status}")
    print(f"Priorité prospect: {priority}/10")
    
    # Créer une fiche prospect réaliste
    prospect_data = {
        'nom': 'MattKonnect - Services Web',
        'email': 'matthieu@mattkonnect.com',
        'telephone': '07.82.90.15.35',
        'site_web': 'https://www.mattkonnect.com',
        'secteur': 'services_numeriques',
        'statut_site': prospect_status,
        'score_technique': analysis['overall_score'],
        'priorite': priority,
        'problemes_detectes': '; '.join(analysis['technical_issues']),
        'recommandations': '; '.join(analysis['recommendations']),
        'date_analyse': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    print(f"\n📋 FICHE PROSPECT GÉNÉRÉE")
    print(f"Contact: {prospect_data['email']}")
    print(f"Score: {prospect_data['score_technique']}/10")
    print(f"Priorité: {prospect_data['priorite']}/10")
    
    return prospect_data

def create_realistic_prospect_with_mattkonnect():
    """Créer un dataset avec MattKonnect et d'autres prospects"""
    data_manager = DataManager()
    
    print("\n📊 CRÉATION DATASET AVEC MATTKONNECT")
    print("=" * 40)
    
    # Analyser MattKonnect
    mattkonnect_data = test_mattkonnect_analysis()
    
    # Ajouter d'autres prospects avec différents niveaux de problèmes
    all_prospects = [
        mattkonnect_data,
        {
            'nom': 'Association Culturelle de Bourges',
            'email': 'contact@culture-bourges.org',
            'telephone': '02.48.12.34.56',
            'site_web': '',  # Pas de site
            'secteur': 'culture',
            'statut_site': '🚨 PROSPECT PRIORITAIRE - Aucun site web',
            'score_technique': 0,
            'priorite': 9,
            'problemes_detectes': 'Aucun site web',
            'recommandations': 'Création complète d\'un site web professionnel',
            'date_analyse': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            'nom': 'Centre de Formation Tours',
            'email': 'info@cfp-tours.fr',
            'telephone': '02.47.55.66.77',
            'site_web': 'http://old-site-example.fr',
            'secteur': 'formation',
            'statut_site': '🎯 PROSPECT - Site obsolète sans SSL',
            'score_technique': 3,
            'priorite': 8,
            'problemes_detectes': 'Pas de SSL; Design obsolète; Pas responsive',
            'recommandations': 'Refonte complète; SSL; Design moderne; Mobile-first',
            'date_analyse': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ]
    
    # Sauvegarder
    output_file = 'prospects_analysis.csv'
    data_manager.save_to_csv(all_prospects, output_file)
    
    print(f"\n✅ {len(all_prospects)} prospects analysés et sauvegardés")
    print(f"📁 Fichier: data/{output_file}")
    
    # Statistiques
    high_priority = sum(1 for p in all_prospects if p['priorite'] >= 7)
    no_website = sum(1 for p in all_prospects if not p['site_web'])
    
    print(f"\nStatistiques:")
    print(f"  • Haute priorité (≥7): {high_priority}")
    print(f"  • Sans site web: {no_website}")
    print(f"  • Score moyen: {sum(p['score_technique'] for p in all_prospects) / len(all_prospects):.1f}/10")
    
    print(f"\n🎯 Prochaine étape: Campagne email ciblée")
    print("   Commande: python email_manager/campaign_manager.py")
    
    return all_prospects

def main():
    """Fonction principale"""
    prospects = create_realistic_prospect_with_mattkonnect()
    return len(prospects)

if __name__ == "__main__":
    main()
