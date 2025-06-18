#!/usr/bin/env python
"""
Script d'installation pour LayoutLMv3 et ses dépendances
"""

import os
import sys
import subprocess
import platform
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_python_version():
    """Vérifie que la version de Python est compatible"""
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 ou supérieur est requis")
        sys.exit(1)
    logger.info(f"Version de Python: {sys.version}")

def install_dependencies():
    """Installe les dépendances requises"""
    try:
        logger.info("Installation des dépendances...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Installer les dépendances de base
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        
        # Installer les dépendances spécifiques pour LayoutLMv3
        subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "transformers", "datasets"])
        
        logger.info("Dépendances installées avec succès")
    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors de l'installation des dépendances: {e}")
        sys.exit(1)

def download_layoutlmv3_model():
    """Télécharge le modèle LayoutLMv3 pré-entraîné"""
    try:
        logger.info("Téléchargement du modèle LayoutLMv3...")
        
        # Utiliser Python pour télécharger le modèle
        import torch
        from transformers import LayoutLMv3Processor, LayoutLMv3ForTokenClassification
        
        # Créer le répertoire pour le modèle
        model_dir = os.path.join("ml_server_app", "invoice_api", "models", "layoutlmv3")
        os.makedirs(model_dir, exist_ok=True)
        
        # Télécharger le processeur et le modèle
        processor = LayoutLMv3Processor.from_pretrained("microsoft/layoutlmv3-base")
        model = LayoutLMv3ForTokenClassification.from_pretrained(
            "microsoft/layoutlmv3-base",
            num_labels=9  # Nombre d'étiquettes dans le label_map
        )
        
        # Sauvegarder le processeur et le modèle
        processor.save_pretrained(model_dir)
        model.save_pretrained(model_dir)
        
        logger.info(f"Modèle LayoutLMv3 téléchargé et sauvegardé dans {model_dir}")
    except Exception as e:
        logger.error(f"Erreur lors du téléchargement du modèle LayoutLMv3: {e}")
        logger.info("L'application fonctionnera en mode dégradé sans LayoutLMv3")

def check_tesseract():
    """Vérifie que Tesseract OCR est installé"""
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        logger.info("Tesseract OCR est installé")
    except Exception as e:
        logger.warning(f"Tesseract OCR n'est pas installé ou n'est pas dans le PATH: {e}")
        if platform.system() == "Windows":
            logger.info("Pour installer Tesseract OCR sur Windows:")
            logger.info("1. Téléchargez l'installateur depuis https://github.com/UB-Mannheim/tesseract/wiki")
            logger.info("2. Installez-le et ajoutez-le au PATH")
        elif platform.system() == "Darwin":  # macOS
            logger.info("Pour installer Tesseract OCR sur macOS:")
            logger.info("brew install tesseract")
        else:  # Linux
            logger.info("Pour installer Tesseract OCR sur Linux:")
            logger.info("sudo apt-get install tesseract-ocr")

def check_poppler():
    """Vérifie que Poppler est installé (pour pdf2image)"""
    try:
        from pdf2image import convert_from_path
        # Créer un petit fichier PDF de test
        test_pdf = os.path.join(os.path.dirname(__file__), "test.pdf")
        with open(test_pdf, "w") as f:
            f.write("%PDF-1.0\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n3 0 obj\n<</Type/Page/MediaBox[0 0 3 3]>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\n0000000102 00000 n\ntrailer\n<</Size 4/Root 1 0 R>>\nstartxref\n149\n%%EOF\n")
        
        # Essayer de convertir le PDF en image
        with open(os.devnull, 'w') as devnull:
            old_stdout = sys.stdout
            sys.stdout = devnull
            try:
                convert_from_path(test_pdf, first_page=1, last_page=1)
                logger.info("Poppler est installé")
            finally:
                sys.stdout = old_stdout
        
        # Supprimer le fichier PDF de test
        os.remove(test_pdf)
    except Exception as e:
        logger.warning(f"Poppler n'est pas installé ou n'est pas dans le PATH: {e}")
        if platform.system() == "Windows":
            logger.info("Pour installer Poppler sur Windows:")
            logger.info("1. Téléchargez les binaires depuis https://github.com/oschwartz10612/poppler-windows/releases/")
            logger.info("2. Extrayez-les et ajoutez le dossier bin au PATH")
        elif platform.system() == "Darwin":  # macOS
            logger.info("Pour installer Poppler sur macOS:")
            logger.info("brew install poppler")
        else:  # Linux
            logger.info("Pour installer Poppler sur Linux:")
            logger.info("sudo apt-get install poppler-utils")

def apply_migrations():
    """Applique les migrations Django"""
    try:
        logger.info("Application des migrations Django...")
        os.chdir("ml_server_app")
        subprocess.check_call([sys.executable, "manage.py", "migrate"])
        os.chdir("..")
        logger.info("Migrations appliquées avec succès")
    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors de l'application des migrations: {e}")
        sys.exit(1)

def main():
    """Fonction principale"""
    logger.info("=== Installation de Advanced ML Extractor ===")
    
    check_python_version()
    install_dependencies()
    check_tesseract()
    check_poppler()
    download_layoutlmv3_model()
    apply_migrations()
    
    logger.info("=== Installation terminée ===")
    logger.info("Pour lancer le serveur Django: cd ml_server_app && python manage.py runserver")
    logger.info("Pour lancer l'application Angular: cd ml_client_app && ng serve")

if __name__ == "__main__":
    main()