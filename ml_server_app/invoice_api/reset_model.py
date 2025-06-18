"""
Script pour réinitialiser le modèle LayoutLMv3
"""

import os
import shutil
import logging
from django.conf import settings

# Configurer le logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def reset_model():
    """Réinitialise le modèle LayoutLMv3 en supprimant le répertoire du modèle"""
    try:
        # Chemin du modèle
        model_path = os.path.join(settings.BASE_DIR, 'invoice_api', 'models', 'layoutlmv3')
        
        # Vérifier si le répertoire existe
        if os.path.exists(model_path):
            logger.info(f"Suppression du répertoire du modèle: {model_path}")
            shutil.rmtree(model_path)
            logger.info("Répertoire du modèle supprimé avec succès")
        else:
            logger.info(f"Le répertoire du modèle n'existe pas: {model_path}")
        
        # Créer un nouveau répertoire vide
        os.makedirs(model_path, exist_ok=True)
        logger.info(f"Nouveau répertoire du modèle créé: {model_path}")
        
        # Réinitialiser le singleton
        from invoice_api.ml_models import layoutlmv3_extractor
        layoutlmv3_extractor.load_model()
        logger.info("Modèle réinitialisé avec succès")
        
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la réinitialisation du modèle: {str(e)}")
        return False

if __name__ == "__main__":
    # Ce code s'exécute uniquement si le script est exécuté directement
    import django
    import sys
    import os
    
    # Configurer Django
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ml_server_app.settings')
    django.setup()
    
    # Réinitialiser le modèle
    reset_model()