#!/usr/bin/env python
"""
Script d'installation pour Advanced ML Extractor
"""
import os
import sys
import subprocess
import platform

def check_tesseract():
    """Vérifie si Tesseract OCR est installé"""
    try:
        import pytesseract
        # Vérifier si la fonction get_tesseract_cmd existe
        if hasattr(pytesseract, 'get_tesseract_cmd'):
            path = pytesseract.get_tesseract_cmd()
            if os.path.exists(path):
                print(f"✅ Tesseract OCR trouvé: {path}")
                return True
            else:
                print("❌ Tesseract OCR non trouvé dans le chemin par défaut")
                return False
        else:
            # Méthode alternative pour vérifier Tesseract
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
    except ImportError:
        print("❌ pytesseract n'est pas installé")
        return False

def check_poppler():
    """Vérifie si Poppler est installé (nécessaire pour pdf2image)"""
    try:
        from pdf2image.pdf2image import pdfinfo_from_path
        # Tester avec un chemin fictif pour voir si l'erreur est liée à Poppler ou au fichier
        try:
            pdfinfo_from_path("test.pdf")
        except FileNotFoundError:
            print("✅ Poppler semble être installé (pdf2image peut être importé)")
            return True
        except Exception as e:
            if "poppler" in str(e).lower():
                print("❌ Poppler n'est pas installé ou n'est pas dans le PATH")
                return False
            else:
                print("✅ Poppler semble être installé (pdf2image peut être importé)")
                return True
    except ImportError:
        print("❌ pdf2image n'est pas installé")
        return False

def install_requirements():
    """Installe les dépendances Python"""
    print("Installation des dépendances Python...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dépendances Python installées avec succès")
    except subprocess.CalledProcessError:
        print("❌ Erreur lors de l'installation des dépendances Python")
        return False
    return True

def install_spacy_models():
    """Installe les modèles spaCy"""
    print("Installation des modèles spaCy...")
    try:
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "fr_core_news_lg"])
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_lg"])
        print("✅ Modèles spaCy installés avec succès")
    except subprocess.CalledProcessError:
        print("❌ Erreur lors de l'installation des modèles spaCy")
        return False
    return True

def setup_django():
    """Configure Django"""
    print("Configuration de Django...")
    try:
        os.chdir("ml_server_app")
        subprocess.check_call([sys.executable, "manage.py", "migrate"])
        print("✅ Base de données Django configurée avec succès")
        os.chdir("..")
    except subprocess.CalledProcessError:
        print("❌ Erreur lors de la configuration de Django")
        return False
    return True

def main():
    """Fonction principale"""
    print("=== Installation de Advanced ML Extractor ===")
    
    # Vérifier le système d'exploitation
    system = platform.system()
    print(f"Système d'exploitation détecté: {system}")
    
    # Installer les dépendances Python
    if not install_requirements():
        print("⚠️ Certaines dépendances n'ont pas pu être installées")
    
    # Vérifier Tesseract OCR
    if not check_tesseract():
        if system == "Windows":
            print("ℹ️ Pour installer Tesseract OCR sur Windows:")
            print("   1. Téléchargez l'installateur depuis https://github.com/UB-Mannheim/tesseract/wiki")
            print("   2. Installez-le et ajoutez-le au PATH")
        elif system == "Linux":
            print("ℹ️ Pour installer Tesseract OCR sur Linux:")
            print("   sudo apt-get install tesseract-ocr")
            print("   sudo apt-get install tesseract-ocr-fra")  # Pour le français
        elif system == "Darwin":  # macOS
            print("ℹ️ Pour installer Tesseract OCR sur macOS:")
            print("   brew install tesseract")
            print("   brew install tesseract-lang")  # Pour les langues supplémentaires
    
    # Vérifier Poppler
    if not check_poppler():
        if system == "Windows":
            print("ℹ️ Pour installer Poppler sur Windows:")
            print("   1. Téléchargez la version Windows depuis http://blog.alivate.com.au/poppler-windows/")
            print("   2. Extrayez-la et ajoutez le dossier bin au PATH")
        elif system == "Linux":
            print("ℹ️ Pour installer Poppler sur Linux:")
            print("   sudo apt-get install poppler-utils")
        elif system == "Darwin":  # macOS
            print("ℹ️ Pour installer Poppler sur macOS:")
            print("   brew install poppler")
    
    # Installer les modèles spaCy
    try:
        import spacy
        install_spacy_models()
    except ImportError:
        print("⚠️ spaCy n'est pas installé, les modèles ne seront pas téléchargés")
    
    # Configurer Django
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