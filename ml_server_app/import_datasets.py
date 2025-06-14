#!/usr/bin/env python3
"""
Script pour importer les datasets téléchargés dans la base de données Django
"""
import os
import sys
import json
import django
from pathlib import Path
from django.core.files import File

# Configuration de l'environnement Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ml_server_app.settings')
django.setup()

# Import des modèles
from invoice_extractor.models import TrainingData

def import_funsd_dataset():
    """
    Importe le dataset FUNSD dans la base de données
    """
    # Chemin vers le dataset FUNSD
    base_dir = Path(__file__).resolve().parent.parent
    funsd_dir = os.path.join(base_dir, 'datasets', 'funsd', 'dataset')
    
    # Vérification de l'existence du répertoire
    if not os.path.exists(funsd_dir):
        print(f"Le répertoire {funsd_dir} n'existe pas.")
        return
    
    # Importation des données d'entraînement
    training_dir = os.path.join(funsd_dir, 'training_data')
    annotations_dir = os.path.join(training_dir, 'annotations')
    images_dir = os.path.join(training_dir, 'images')
    
    # Compteurs
    imported_count = 0
    skipped_count = 0
    
    # Parcours des annotations
    for filename in os.listdir(annotations_dir):
        if filename.endswith('.json'):
            # Vérification si le fichier existe déjà dans la base de données
            if TrainingData.objects.filter(original_filename=filename).exists():
                print(f"Le fichier {filename} existe déjà dans la base de données. Ignoré.")
                skipped_count += 1
                continue
            
            # Chargement des annotations
            with open(os.path.join(annotations_dir, filename), 'r') as f:
                annotation = json.load(f)
            
            # Chemin vers l'image correspondante
            image_path = os.path.join(images_dir, filename.replace('.json', '.png'))
            
            if os.path.exists(image_path):
                # Création de l'objet TrainingData
                training_data = TrainingData(
                    original_filename=filename,
                    annotations=annotation,
                    dataset_type='funsd',
                    is_validated=True
                )
                
                # Sauvegarde du fichier
                with open(image_path, 'rb') as f:
                    training_data.file.save(filename.replace('.json', '.png'), File(f))
                
                training_data.save()
                imported_count += 1
                print(f"Fichier {filename} importé avec succès.")
    
    print(f"Importation terminée. {imported_count} fichiers importés, {skipped_count} fichiers ignorés.")

def import_invoice2data_dataset():
    """
    Importe le dataset Invoice2Data dans la base de données
    """
    # Chemin vers le dataset Invoice2Data
    base_dir = Path(__file__).resolve().parent.parent
    invoice2data_dir = os.path.join(base_dir, 'datasets', 'invoice2data', 'invoice2data-master')
    
    # Vérification de l'existence du répertoire
    if not os.path.exists(invoice2data_dir):
        print(f"Le répertoire {invoice2data_dir} n'existe pas.")
        return
    
    # Importation des données de test
    test_dir = os.path.join(invoice2data_dir, 'tests', 'compare')
    
    # Compteurs
    imported_count = 0
    skipped_count = 0
    
    # Parcours des fichiers
    for filename in os.listdir(test_dir):
        if filename.endswith('.pdf') or filename.endswith('.png'):
            # Recherche du fichier JSON correspondant
            json_path = os.path.join(test_dir, filename.replace('.pdf', '.json').replace('.png', '.json'))
            
            # Vérification si le fichier existe déjà dans la base de données
            if TrainingData.objects.filter(original_filename=filename).exists():
                print(f"Le fichier {filename} existe déjà dans la base de données. Ignoré.")
                skipped_count += 1
                continue
            
            if os.path.exists(json_path):
                # Chargement des annotations
                with open(json_path, 'r') as f:
                    annotation = json.load(f)
                
                # Création de l'objet TrainingData
                training_data = TrainingData(
                    original_filename=filename,
                    annotations=annotation,
                    dataset_type='invoice2data',
                    is_validated=True
                )
                
                # Sauvegarde du fichier
                with open(os.path.join(test_dir, filename), 'rb') as f:
                    training_data.file.save(filename, File(f))
                
                training_data.save()
                imported_count += 1
                print(f"Fichier {filename} importé avec succès.")
    
    print(f"Importation terminée. {imported_count} fichiers importés, {skipped_count} fichiers ignorés.")

if __name__ == "__main__":
    print("Importation des datasets...")
    
    # Importation du dataset FUNSD
    print("\nImportation du dataset FUNSD...")
    import_funsd_dataset()
    
    # Importation du dataset Invoice2Data
    print("\nImportation du dataset Invoice2Data...")
    import_invoice2data_dataset()
    
    print("\nImportation terminée.")