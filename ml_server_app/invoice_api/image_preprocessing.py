"""
Module pour le prétraitement des images avant OCR
"""
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

def preprocess_image(image):
    """
    Prétraite une image pour améliorer la qualité de l'OCR
    
    Args:
        image: Image PIL
        
    Returns:
        Image PIL prétraitée
    """
    # Convertir en niveaux de gris si ce n'est pas déjà fait
    if image.mode != 'L':
        image = image.convert('L')
    
    # Améliorer le contraste
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    
    # Améliorer la netteté
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(2.0)
    
    # Appliquer un filtre de réduction de bruit
    image = image.filter(ImageFilter.MedianFilter(size=3))
    
    return image

def preprocess_image_cv2(image_path):
    """
    Prétraite une image avec OpenCV pour améliorer la qualité de l'OCR
    
    Args:
        image_path: Chemin vers l'image
        
    Returns:
        Image OpenCV prétraitée
    """
    # Charger l'image
    img = cv2.imread(image_path)
    
    # Convertir en niveaux de gris
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Appliquer un flou gaussien pour réduire le bruit
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Appliquer un seuillage adaptatif
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                  cv2.THRESH_BINARY, 11, 2)
    
    # Appliquer une opération de dilatation pour renforcer le texte
    kernel = np.ones((1, 1), np.uint8)
    img_dilation = cv2.dilate(thresh, kernel, iterations=1)
    
    # Appliquer une opération d'érosion pour affiner le texte
    img_erosion = cv2.erode(img_dilation, kernel, iterations=1)
    
    return img_erosion

def pil_to_cv2(pil_image):
    """
    Convertit une image PIL en image OpenCV
    
    Args:
        pil_image: Image PIL
        
    Returns:
        Image OpenCV
    """
    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

def cv2_to_pil(cv2_image):
    """
    Convertit une image OpenCV en image PIL
    
    Args:
        cv2_image: Image OpenCV
        
    Returns:
        Image PIL
    """
    return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB))

def deskew_image(image):
    """
    Redresse une image inclinée
    
    Args:
        image: Image PIL
        
    Returns:
        Image PIL redressée
    """
    # Convertir en OpenCV
    img = pil_to_cv2(image)
    
    # Convertir en niveaux de gris
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Appliquer un seuillage
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    
    # Trouver les contours
    coords = np.column_stack(np.where(thresh > 0))
    
    # Calculer l'angle de rotation
    angle = cv2.minAreaRect(coords)[-1]
    
    # Ajuster l'angle
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    
    # Rotation de l'image
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    
    # Convertir en PIL
    return cv2_to_pil(rotated)