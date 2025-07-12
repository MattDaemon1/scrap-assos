#!/usr/bin/env python3
"""
Script pour exécuter tous les tests du projet
"""

import unittest
import sys
import os
from io import StringIO

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_all_tests(verbosity=2):
    """Exécuter tous les tests avec un rapport détaillé"""
    
    print("=" * 70)
    print("🧪 LANCEMENT DES TESTS - GÉNÉRATEUR DE LEADS ASSOCIATIONS")
    print("=" * 70)
    
    # Découvrir tous les tests dans le répertoire tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Capturer les résultats
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=verbosity,
        failfast=False
    )
    
    # Exécuter les tests
    print("🔄 Exécution des tests en cours...\n")
    result = runner.run(suite)
    
    # Afficher les résultats
    output = stream.getvalue()
    print(output)
    
    # Résumé final
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 70)
    
    print(f"✅ Tests réussis: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Tests échoués: {len(result.failures)}")
    print(f"💥 Erreurs: {len(result.errors)}")
    print(f"⏭️  Tests ignorés: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    print(f"📈 Total: {result.testsRun} tests")
    
    # Détail des échecs
    if result.failures:
        print(f"\n🔴 DÉTAIL DES ÉCHECS ({len(result.failures)}):")
        for i, (test, traceback) in enumerate(result.failures, 1):
            print(f"\n{i}. {test}")
            print("-" * 50)
            print(traceback)
    
    # Détail des erreurs
    if result.errors:
        print(f"\n💥 DÉTAIL DES ERREURS ({len(result.errors)}):")
        for i, (test, traceback) in enumerate(result.errors, 1):
            print(f"\n{i}. {test}")
            print("-" * 50)
            print(traceback)
    
    # Calcul du taux de réussite
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
        print(f"\n🎯 Taux de réussite: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 Excellent! Le système est prêt pour la production")
        elif success_rate >= 75:
            print("⚠️  Bien, mais quelques améliorations sont nécessaires")
        else:
            print("🚨 Attention! Des corrections importantes sont requises")
    
    print("\n" + "=" * 70)
    
    return result.wasSuccessful()

def run_specific_test(test_name):
    """Exécuter un test spécifique"""
    print(f"🧪 Exécution du test: {test_name}")
    
    suite = unittest.TestLoader().loadTestsFromName(test_name)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_test_coverage():
    """Analyser la couverture de code (si coverage est installé)"""
    try:
        import coverage
        print("📊 Analyse de la couverture de code...")
        
        cov = coverage.Coverage()
        cov.start()
        
        # Exécuter les tests
        run_all_tests(verbosity=1)
        
        cov.stop()
        cov.save()
        
        print("\n📈 RAPPORT DE COUVERTURE:")
        cov.report()
        
    except ImportError:
        print("ℹ️  Pour analyser la couverture, installez: pip install coverage")
        print("   Puis exécutez: coverage run run_tests.py && coverage report")

def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Exécuter les tests du générateur de leads")
    parser.add_argument('--test', help="Exécuter un test spécifique")
    parser.add_argument('--coverage', action='store_true', help="Analyser la couverture de code")
    parser.add_argument('--quick', action='store_true', help="Tests rapides (verbosité réduite)")
    
    args = parser.parse_args()
    
    if args.test:
        success = run_specific_test(args.test)
    elif args.coverage:
        run_test_coverage()
        success = True
    else:
        verbosity = 1 if args.quick else 2
        success = run_all_tests(verbosity)
    
    # Code de sortie
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
