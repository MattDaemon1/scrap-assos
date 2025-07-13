# RNA Campaign Sender

Envoi d'emails de prospection aux associations officielles du département 01 (Ain).
Données 100% réelles extraites du RNA (Répertoire National des Associations).

## 🎯 Fonctionnalités

- ✅ **6 contacts email réels** extraits du RNA officiel
- ✅ **Associations vérifiées** du Journal Officiel  
- ✅ **Envoi d'emails automatisé** avec personnalisation
- ✅ **Mode test et production** intégré
- ✅ **Template email professionnel** inclus

## 📧 Contacts Disponibles

```
1. accueil-laval@pl.chambagri.fr (Société de chasse - Saint-Benoit)
2. asgym.villebois@gmail.com (Société de chasse - Villebois) 
3. mairie@tenay.fr (Association de pêche - Tenay)
4. thierco@orange.fr (Association chasse - Chazey-sur-Ain)
5. contact@mairie-serriersdebriord.fr (Association pêche - Briord)
6. contact@hautrhone-tourisme.fr (Association chasse - Seyssel)
```

## 🚀 Utilisation Rapide

### 1. Envoyer un email de test
```bash
python rna_campaign_sender.py
# Choisir option 1 pour test
```

### 2. Campagne complète
```bash
python rna_campaign_sender.py  
# Choisir option 3 pour envoi réel
```

## 📁 Fichiers Importants

- `rna_campaign_sender.py` - **Script principal d'envoi**
- `data/rna_emails_clean_20250713_1608.csv` - **Contacts finaux**
- `templates/email_template_rna_20250713_1608.txt` - **Template email**
- `config/sender_config.txt` - **Configuration SMTP**
- `send_real_email.py` - Script de test email simple

## ⚙️ Configuration SMTP

Le fichier `config/sender_config.txt` contient :
```
SMTP_SERVER=mail.mattkonnect.com
SMTP_PORT=465
EMAIL_USER=votre_email@mattkonnect.com
EMAIL_PASSWORD=votre_mot_de_passe
```

## 🔧 Scripts Disponibles

### Core
- `rna_campaign_sender.py` - Envoi de campagne email principal

### Utilitaires  
- `scrapers/rna_processor.py` - Traitement des données RNA
- `scrapers/rna_contact_scraper.py` - Extraction de contacts
- `scrapers/email_cleaner.py` - Nettoyage des emails

### Test
- `send_real_email.py` - Test rapide envoi email

## 📊 Statistiques Actuelles

- **654 associations** traitées du département 01
- **70 associations** analysées pour contacts  
- **6 emails valides** extraits (taux 8.5%)
- **100% données officielles** du Journal Officiel
- **Prêt pour campagne** immédiate
