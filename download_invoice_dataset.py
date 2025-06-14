#!/usr/bin/env python3
"""
Script pour télécharger un dataset de factures de grande taille
"""
import os
import requests
import zipfile
from tqdm import tqdm
import shutil
import tarfile

def download_file(url, destination):
    """Télécharge un fichier avec une barre de progression"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 8192
    
    with open(destination, 'wb') as file, tqdm(
            desc=f"Téléchargement de {os.path.basename(destination)}",
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
        for data in response.iter_content(block_size):
            file.write(data)
            bar.update(len(data))

def main():
    # Créer un dossier pour les datasets
    dataset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'datasets')
    os.makedirs(dataset_dir, exist_ok=True)
    
    # Télécharger le dataset Invoice2Data
    print("Téléchargement du dataset Invoice2Data...")
    invoice2data_dir = os.path.join(dataset_dir, 'invoice2data')
    os.makedirs(invoice2data_dir, exist_ok=True)
    
    # URL du dataset Invoice2Data
    invoice2data_url = "https://github.com/invoice-x/invoice2data/archive/refs/heads/master.zip"
    invoice2data_zip = os.path.join(invoice2data_dir, 'invoice2data.zip')
    
    # Télécharger le fichier
    download_file(invoice2data_url, invoice2data_zip)
    
    # Extraire les fichiers
    print("Extraction des fichiers Invoice2Data...")
    with zipfile.ZipFile(invoice2data_zip, 'r') as zip_ref:
        zip_ref.extractall(invoice2data_dir)
    
    # Supprimer le fichier zip
    os.remove(invoice2data_zip)
    
    # Télécharger le dataset DocVQA
    print("Téléchargement du dataset DocVQA (échantillon)...")
    docvqa_dir = os.path.join(dataset_dir, 'docvqa')
    os.makedirs(docvqa_dir, exist_ok=True)
    
    # URL du dataset DocVQA (échantillon)
    docvqa_url = "https://github.com/herobd/layoutlmv2/raw/main/examples/docvqa/data/val.json"
    docvqa_file = os.path.join(docvqa_dir, 'val.json')
    
    # Télécharger le fichier
    download_file(docvqa_url, docvqa_file)
    
    # Télécharger le dataset FUNSD
    print("Téléchargement du dataset FUNSD...")
    funsd_dir = os.path.join(dataset_dir, 'funsd')
    os.makedirs(funsd_dir, exist_ok=True)
    
    # URL du dataset FUNSD
    funsd_url = "https://guillaumejaume.github.io/FUNSD/dataset.zip"
    funsd_zip = os.path.join(funsd_dir, 'dataset.zip')
    
    # Télécharger le fichier
    download_file(funsd_url, funsd_zip)
    
    # Extraire les fichiers
    print("Extraction des fichiers FUNSD...")
    with zipfile.ZipFile(funsd_zip, 'r') as zip_ref:
        zip_ref.extractall(funsd_dir)
    
    # Supprimer le fichier zip
    os.remove(funsd_zip)
    
    print("\nTéléchargement terminé!")
    print(f"Les datasets sont disponibles dans le dossier: {dataset_dir}")
    
    # Compter le nombre de factures téléchargées
    invoice2data_files = []
    for root, dirs, files in os.walk(os.path.join(invoice2data_dir)):
        for file in files:
            if file.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
                invoice2data_files.append(os.path.join(root, file))
    
    funsd_files = []
    for root, dirs, files in os.walk(os.path.join(funsd_dir)):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                funsd_files.append(os.path.join(root, file))
    
    print(f"Nombre de factures/reçus dans Invoice2Data: {len(invoice2data_files)}")
    print(f"Nombre de documents dans FUNSD: {len(funsd_files)}")
    print(f"Nombre total de documents téléchargés: {len(invoice2data_files) + len(funsd_files)}")

if __name__ == "__main__":
    main()