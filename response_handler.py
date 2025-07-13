#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RESPONSE HANDLER - Gestionnaire de réponses email
===============================================
Interface simple pour traiter les réponses aux campagnes
"""

import sys
import os
from datetime import datetime

# Importer le tracker
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from campaign_tracker import CampaignTracker

class ResponseHandler:
    """Gestionnaire de réponses email"""
    
    def __init__(self):
        self.tracker = CampaignTracker()
        self.types_reponse = {
            '1': ('interesse', '✅ Intéressé'),
            '2': ('demande_info', '📄 Demande info'),
            '3': ('demande_devis', '💰 Demande devis'),
            '4': ('pas_interesse', '❌ Pas intéressé'),
            '5': ('rappeler_plus_tard', '⏰ Rappeler plus tard'),
            '6': ('desabonnement', '🚫 Désabonnement'),
            '7': ('bounce', '📧 Email invalide')
        }
    
    def process_manual_response(self):
        """Traiter une réponse manuellement"""
        print(f"💬 TRAITEMENT RÉPONSE EMAIL")
        print(f"=" * 40)
        
        # Demander l'email
        email = input(f"📧 Email de l'association: ").strip()
        if not email:
            print(f"❌ Email requis")
            return
        
        # Afficher les types de réponse
        print(f"\n📋 TYPES DE RÉPONSE:")
        for key, (code, label) in self.types_reponse.items():
            print(f"  {key}. {label}")
        
        # Demander le type
        choix = input(f"\n❓ Type de réponse (1-7): ").strip()
        if choix not in self.types_reponse:
            print(f"❌ Choix invalide")
            return
        
        type_reponse, label = self.types_reponse[choix]
        
        # Demander le contenu (optionnel)
        print(f"\n📝 Contenu de la réponse (optionnel):")
        contenu = input(f">> ").strip()
        
        # Déterminer sentiment
        sentiment = 'positif' if type_reponse in ['interesse', 'demande_info', 'demande_devis'] else 'negatif'
        if type_reponse in ['rappeler_plus_tard']:
            sentiment = 'neutre'
        
        # Enregistrer
        success = self.tracker.log_response(email, type_reponse, contenu, sentiment)
        
        if success:
            print(f"\n✅ Réponse enregistrée!")
            print(f"📧 Email: {email}")
            print(f"💬 Type: {label}")
            print(f"😊 Sentiment: {sentiment}")
            
            # Afficher action recommandée
            action = self.tracker._determine_action(type_reponse, contenu)
            print(f"⚡ Action recommandée: {action}")
        else:
            print(f"❌ Erreur lors de l'enregistrement")
    
    def bulk_import_responses(self):
        """Import en lot de réponses"""
        print(f"📥 IMPORT EN LOT - RÉPONSES")
        print(f"=" * 40)
        print(f"💡 Format: email;type;contenu")
        print(f"📋 Types: interesse, demande_info, demande_devis, pas_interesse, etc.")
        print(f"\n📝 Entrez les réponses (ligne vide pour terminer):")
        
        count = 0
        while True:
            line = input(f">> ").strip()
            if not line:
                break
            
            try:
                parts = line.split(';')
                if len(parts) >= 2:
                    email = parts[0].strip()
                    type_rep = parts[1].strip()
                    contenu = parts[2].strip() if len(parts) > 2 else ""
                    
                    sentiment = 'positif' if type_rep in ['interesse', 'demande_info', 'demande_devis'] else 'negatif'
                    
                    if self.tracker.log_response(email, type_rep, contenu, sentiment):
                        count += 1
                        print(f"  ✅ {email} → {type_rep}")
                    else:
                        print(f"  ❌ Erreur: {email}")
                else:
                    print(f"  ⚠️  Format invalide: {line}")
            except Exception as e:
                print(f"  ❌ Erreur: {e}")
        
        print(f"\n📊 Import terminé: {count} réponses ajoutées")
    
    def show_pending_actions(self):
        """Afficher les actions en attente"""
        print(f"\n⚡ ACTIONS EN ATTENTE")
        print(f"=" * 30)
        
        # Récupérer leads chauds
        leads = self.tracker.get_leads_chauds()
        
        # Suggestions d'actions
        if not leads.empty:
            print(f"\n💡 ACTIONS RECOMMANDÉES:")
            print(f"=" * 30)
            
            actions_count = {}
            for _, lead in leads.iterrows():
                action = lead.get('action_requise', 'analyser_manuellement')
                actions_count[action] = actions_count.get(action, 0) + 1
            
            for action, count in actions_count.items():
                emoji = self._get_action_emoji(action)
                print(f"  {emoji} {action}: {count} contact(s)")
    
    def _get_action_emoji(self, action):
        """Emoji pour les actions"""
        emojis = {
            'appel_commercial': '📞',
            'envoyer_documentation': '📄',
            'preparer_devis': '💰',
            'programmer_relance': '⏰',
            'analyser_manuellement': '🔍',
            'marquer_non_qualifie': '❌',
            'supprimer_liste': '🗑️',
            'verifier_email': '📧'
        }
        return emojis.get(action, '⚡')

def main():
    """Menu principal"""
    handler = ResponseHandler()
    
    while True:
        print(f"\n💬 GESTIONNAIRE RÉPONSES EMAIL")
        print(f"=" * 40)
        print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        print(f"\n📋 OPTIONS:")
        print(f"  1. 💬 Traiter une réponse")
        print(f"  2. 📥 Import en lot")
        print(f"  3. 📊 Dashboard campagne")
        print(f"  4. 🔥 Leads chauds")
        print(f"  5. ⚡ Actions en attente")
        print(f"  6. 📤 Export CRM")
        print(f"  7. 🚪 Quitter")
        
        choix = input(f"\n❓ Votre choix (1-7): ").strip()
        
        try:
            if choix == '1':
                handler.process_manual_response()
            elif choix == '2':
                handler.bulk_import_responses()
            elif choix == '3':
                handler.tracker.get_dashboard()
            elif choix == '4':
                handler.tracker.get_leads_chauds()
            elif choix == '5':
                handler.show_pending_actions()
            elif choix == '6':
                filename = handler.tracker.export_for_crm()
                print(f"📊 Export terminé: {filename}")
            elif choix == '7':
                print(f"👋 Au revoir!")
                break
            else:
                print(f"❌ Choix invalide")
                
        except KeyboardInterrupt:
            print(f"\n👋 Au revoir!")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()
