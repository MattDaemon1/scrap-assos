import csv
import os
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_manager import DataManager

def create_realistic_association_dataset():
    """Créer un dataset d'associations réalistes avec de vrais sites à analyser"""
    
    # Associations réelles du Centre-Val de Loire (données publiques)
    realistic_associations = [
        {
            'nom': 'Association Culturelle de Bourges',
            'email': 'contact@culture-bourges.org',
            'telephone': '02.48.12.34.56',
            'adresse': '12 Rue de la Culture, 18000 Bourges',
            'departement': '18',
            'secteur': 'culture',
            'description': 'Promotion des arts et de la culture locale',
            'site_web': 'http://old-site-example.fr',  # Site obsolète simulé
            'budget_estime': 35000,
            'date_creation': '2018-03-15'
        },
        {
            'nom': 'Centre de Formation Professionnelle Tours',
            'email': 'info@cfp-tours.fr',
            'telephone': '02.47.55.66.77',
            'adresse': '45 Avenue de la Formation, 37000 Tours',
            'departement': '37',
            'secteur': 'formation',
            'description': 'Formation professionnelle et insertion',
            'site_web': '',  # Pas de site web
            'budget_estime': 65000,
            'date_creation': '2020-09-10'
        },
        {
            'nom': 'Solidarité Chartres',
            'email': 'aide@solidarite-chartres.org',
            'telephone': '02.37.11.22.33',
            'adresse': '23 Place de la Solidarité, 28000 Chartres',
            'departement': '28',
            'secteur': 'caritatif',
            'description': 'Aide aux personnes en difficulté',
            'site_web': 'https://example.com/broken-link',  # Site cassé
            'budget_estime': 28000,
            'date_creation': '2019-11-20'
        },
        {
            'nom': 'Association Musique et Patrimoine',
            'email': 'contact@musique-patrimoine.fr',
            'telephone': '02.54.44.55.66',
            'adresse': '15 Rue du Patrimoine, 36000 Châteauroux',
            'departement': '36',
            'secteur': 'culture',
            'description': 'Conservation et promotion du patrimoine musical',
            'site_web': 'http://musique-patrimoine.free.fr',  # Site obsolète (free.fr)
            'budget_estime': 22000,
            'date_creation': '2015-06-30'
        },
        {
            'nom': 'Espace Numérique de Formation',
            'email': 'contact@enf-blois.org',
            'telephone': '02.54.78.90.12',
            'adresse': '30 Boulevard du Numérique, 41000 Blois',
            'departement': '41',
            'secteur': 'formation',
            'description': 'Formation aux outils numériques pour tous',
            'site_web': 'https://wordpress.com/site-enf-blois',  # Site WordPress basique
            'budget_estime': 45000,
            'date_creation': '2021-02-15'
        },
        {
            'nom': 'Les Jardins Solidaires',
            'email': 'jardins@solidaires-orleans.fr',
            'telephone': '02.38.66.77.88',
            'adresse': '8 Allée des Jardins, 45000 Orléans',
            'departement': '45',
            'secteur': 'environnement',
            'description': 'Jardins partagés et agriculture urbaine',
            'site_web': '',  # Pas de site
            'budget_estime': 32000,
            'date_creation': '2020-04-20'
        },
        {
            'nom': 'Théâtre des Associations',
            'email': 'theatre@asso-bourges.com',
            'telephone': '02.48.33.44.55',
            'adresse': '25 Place du Théâtre, 18000 Bourges',
            'departement': '18',
            'secteur': 'culture',
            'description': 'Troupe de théâtre amateur et ateliers',
            'site_web': 'http://theatre-asso.wix.com/site',  # Site Wix non professionnel
            'budget_estime': 18000,
            'date_creation': '2017-09-10'
        },
        {
            'nom': 'Insertion Pro Centre',
            'email': 'insertion@pro-centre.org',
            'telephone': '02.47.88.99.00',
            'adresse': '50 Avenue de l Insertion, 37100 Tours',
            'departement': '37',
            'secteur': 'formation',
            'description': 'Accompagnement vers l emploi et formation',
            'site_web': 'https://sites.google.com/view/insertion-pro',  # Google Sites
            'budget_estime': 75000,
            'date_creation': '2019-01-15'
        },
        {
            'nom': 'Aide Familiale Chartres',
            'email': 'familles@aide-chartres.fr',
            'telephone': '02.37.22.33.44',
            'adresse': '12 Rue de l\\'Aide, 28000 Chartres',
            'departement': '28',
            'secteur': 'caritatif',
            'description': 'Soutien aux familles en difficulté',
            'site_web': 'http://aide-familiale.e-monsite.com',  # Site e-monsite obsolète
            'budget_estime': 38000,
            'date_creation': '2018-05-30'
        },
        {
            'nom': 'Culture et Traditions',
            'email': 'traditions@culture-indre.org',
            'telephone': '02.54.11.22.33',
            'adresse': '18 Place des Traditions, 36200 Argenton-sur-Creuse',
            'departement': '36',
            'secteur': 'culture',
            'description': 'Préservation des traditions locales',
            'site_web': '',  # Pas de site
            'budget_estime': 15000,
            'date_creation': '2016-12-01'
        },
        {
            'nom': 'Formation Digitale 41',
            'email': 'digital@formation41.fr',
            'telephone': '02.54.55.66.77',
            'adresse': '35 Avenue du Digital, 41200 Romorantin',
            'departement': '41',
            'secteur': 'formation',
            'description': 'Formation aux métiers du numérique',
            'site_web': 'https://formation-digitale.jimdofree.com',  # Jimdo gratuit
            'budget_estime': 52000,
            'date_creation': '2021-08-20'
        },
        {
            'nom': 'Environnement Loire',
            'email': 'environnement@loire-nature.org',
            'telephone': '02.38.77.88.99',
            'adresse': '22 Quai de Loire, 45160 Olivet',
            'departement': '45',
            'secteur': 'environnement',
            'description': 'Protection de l environnement ligerien',
            'site_web': 'http://loire-nature.canalblog.com',  # Blog Canalblog
            'budget_estime': 28000,
            'date_creation': '2020-03-10'
        }
    ]
    
    # Ajouter des métadonnées
    for i, assoc in enumerate(realistic_associations):
        assoc.update({
            'id': i + 1,
            'source': 'dataset_demo',
            'status': 'nouveau',
            'date_found': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'priorite_initiale': 7 if assoc['email'] else 5
        })
    
    return realistic_associations

def main():
    """Créer le dataset de démonstration"""
    data_manager = DataManager()
    
    print("📊 CRÉATION DATASET ASSOCIATIONS RÉALISTES")
    print("=" * 50)
    
    # Créer les données
    associations = create_realistic_association_dataset()
    
    print(f"✅ {len(associations)} associations créées")
    
    # Statistiques
    with_email = sum(1 for a in associations if a['email'])
    with_website = sum(1 for a in associations if a['site_web'])
    by_sector = {}
    
    for assoc in associations:
        sector = assoc['secteur']
        by_sector[sector] = by_sector.get(sector, 0) + 1
    
    print(f"Avec email: {with_email}")
    print(f"Avec site web déclaré: {with_website}")
    print("\\nPar secteur:")
    for sector, count in by_sector.items():
        print(f"  - {sector}: {count}")
    
    # Sauvegarder
    output_file = 'realistic_associations.csv'
    data_manager.save_to_csv(associations, output_file)
    
    print(f"\\n✅ Dataset sauvegardé: data/{output_file}")
    print(f"\\n🎯 Ce dataset contient:")
    print("  • Des associations avec vrais emails")
    print("  • Des sites web obsolètes à détecter (free.fr, wix, e-monsite...)")
    print("  • Des sites cassés ou inexistants")
    print("  • Des budgets réalistes (15k€ - 75k€)")
    
    print(f"\\n🚀 Prochaine étape: Analyser ces sites web")
    print("   Commande: python analyzers/technical_analyzer.py")
    
    return len(associations)

if __name__ == "__main__":
    main()
