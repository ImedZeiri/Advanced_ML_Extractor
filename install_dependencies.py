#!/usr/bin/env python
"""
Script d'installation simplifié pour les dépendances d'Advanced ML Extractor
"""
import os
import sys
import subprocess
import platform

def install_base_dependencies():
    """Installe les dépendances Python de base"""
    print("Installation des dépendances Python de base...")
    dependencies = [
        "Django>=3.2.0",
        "djangorestframework>=3.12.0",
        "django-cors-headers>=3.7.0",
        "Pillow>=8.0.0",
        "pytesseract>=0.3.8",
        "pdf2image>=1.16.0",
        "PyPDF2>=2.0.0",
        "opencv-python>=4.5.3",
        "numpy>=1.20.0",
        "pyyaml>=6.0.0"
    ]
    
    try:
        for dep in dependencies:
            print(f"Installation de {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
        print("✅ Dépendances Python de base installées avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation des dépendances Python: {str(e)}")
        return False

def install_ml_dependencies():
    """Installe les dépendances ML optionnelles"""
    print("\nInstallation des dépendances ML optionnelles...")
    try:
        # Installer spaCy
        print("Installation de spaCy...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "spacy>=3.0.0"])
        
        # Installer transformers (version légère)
        print("Installation de transformers...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "transformers"])
        
        print("✅ Dépendances ML installées avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation des dépendances ML: {str(e)}")
        return False

def install_spacy_models():
    """Installe les modèles spaCy"""
    print("\nInstallation des modèles spaCy (peut prendre quelques minutes)...")
    try:
        # Installer les modèles légers (plus rapides à télécharger)
        print("Installation du modèle français...")
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "fr_core_news_sm"])
        
        print("Installation du modèle anglais...")
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
        
        print("✅ Modèles spaCy installés avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation des modèles spaCy: {str(e)}")
        return False

def check_tesseract():
    """Vérifie si Tesseract OCR est installé"""
    try:
        # Essayer d'exécuter une commande simple pour voir si Tesseract est disponible
        result = subprocess.run(['tesseract', '--version'], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               text=True, 
                               check=False)
        if result.returncode == 0:
            print(f"✅ Tesseract OCR trouvé: {result.stdout.split()[0]}")
            return True
        else:
            print("❌ Tesseract OCR non trouvé dans le PATH")
            return False
    except FileNotFoundError:
        print("❌ Tesseract OCR non trouvé dans le PATH")
        return False

def setup_django():
    """Configure Django"""
    print("\nConfiguration de Django...")
    try:
        if os.path.exists("ml_server_app"):
            os.chdir("ml_server_app")
            subprocess.check_call([sys.executable, "manage.py", "migrate"])
            print("✅ Base de données Django configurée avec succès")
            os.chdir("..")
            return True
        else:
            print("❌ Répertoire ml_server_app non trouvé")
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la configuration de Django: {str(e)}")
        return False

def main():
    """Fonction principale"""
    print("=== Installation des dépendances pour Advanced ML Extractor ===")
    
    # Vérifier le système d'exploitation
    system = platform.system()
    print(f"Système d'exploitation détecté: {system}")
    
    # Installer les dépendances Python de base
    install_base_dependencies()
    
    # Vérifier Tesseract OCR
    if not check_tesseract():
        if system == "Windows":
            print("\nℹ️ Pour installer Tesseract OCR sur Windows:")
            print("   1. Téléchargez l'installateur depuis https://github.com/UB-Mannheim/tesseract/wiki")
            print("   2. Installez-le et ajoutez-le au PATH")
        elif system == "Linux":
            print("\nℹ️ Pour installer Tesseract OCR sur Linux:")
            print("   sudo apt-get install tesseract-ocr")
            print("   sudo apt-get install tesseract-ocr-fra")  # Pour le français
        elif system == "Darwin":  # macOS
            print("\nℹ️ Pour installer Tesseract OCR sur macOS:")
            print("   brew install tesseract")
            print("   brew install tesseract-lang")  # Pour les langues supplémentaires
    
    # Demander à l'utilisateur s'il souhaite installer les dépendances ML
    install_ml = input("\nSouhaitez-vous installer les dépendances ML optionnelles ? (y/n): ").lower() == 'y'
    if install_ml:
        if install_ml_dependencies():
            install_models = input("\nSouhaitez-vous installer les modèles spaCy ? (y/n): ").lower() == 'y'
            if install_models:
                install_spacy_models()
    
    # Configurer Django
    setup_django_db = input("\nSouhaitez-vous configurer la base de données Django ? (y/n): ").lower() == 'y'
    if setup_django_db:
        setup_django()
    
    print("\n=== Installation terminée ===")
    print("Pour lancer le serveur Django:")
    print("   cd ml_server_app")
    print("   python manage.py runserver")
    print("\nPour lancer l'application Angular:")
    print("   cd ml_client_app")
    print("   ng serve")

if __name__ == "__main__":
    main()