"""
Utilitaires pour le traitement du texte des factures
"""

import json

def text_to_html(text):
    """
    Convertit le texte formaté en HTML avec mise en forme améliorée
    
    Args:
        text: Texte formaté
        
    Returns:
        str: HTML formaté
    """
    if not text:
        return ""
    
    # Remplacer les marqueurs de montants par des spans HTML
    html = text.replace('→', '<span class="amount">').replace('←', '</span>')
    
    # Convertir les sauts de ligne en balises <br>
    html = html.replace('\n', '<br>')
    
    # Mettre en évidence les en-têtes (lignes avec des tirets en dessous)
    lines = html.split('<br>')
    result = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Vérifier si la ligne suivante est une ligne de tirets
        if i + 1 < len(lines) and lines[i + 1].startswith('-'):
            # C'est un en-tête
            result.append(f'<h3>{line}</h3>')
            i += 2  # Sauter la ligne de tirets
        else:
            result.append(line)
            i += 1
    
    return '<br>'.join(result)

def create_invoice_html(invoice_data):
    """
    Crée une page HTML complète pour afficher une facture
    
    Args:
        invoice_data: Dictionnaire contenant les données de la facture
        
    Returns:
        str: Document HTML complet
    """
    formatted_text = invoice_data.get("formatted_text", "")
    structured_data = invoice_data.get("structured_data", {})
    json_output = structured_data.get("json_output", {})
    
    # Extraire les informations structurées
    invoice_number = json_output.get("numeroFacture") or structured_data.get("invoice_number", "Non disponible")
    date = json_output.get("datePiece") or structured_data.get("date", "Non disponible")
    total_amount = json_output.get("totalTTC") or structured_data.get("total_amount", "Non disponible")
    
    # Informations client
    client = json_output.get("client", {})
    client_name = client.get("societe", "Non disponible")
    client_tva = client.get("tva", "Non disponible")
    
    # Articles
    articles = json_output.get("articles", [])
    
    # Créer le HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Facture {invoice_number}</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: 'Courier New', monospace;
                line-height: 1.5;
                padding: 20px;
                max-width: 800px;
                margin: 0 auto;
                background-color: #f5f5f5;
            }}
            .invoice-header {{
                background-color: #2c3e50;
                color: white;
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 5px;
            }}
            .invoice-summary {{
                background-color: #ecf0f1;
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 5px;
                border-left: 5px solid #3498db;
            }}
            .invoice-container {{
                border: 1px solid #ccc;
                padding: 20px;
                background-color: white;
                white-space: pre-wrap;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .amount {{
                color: #e74c3c;
                font-weight: bold;
            }}
            h3 {{
                color: #2980b9;
                border-bottom: 1px solid #2980b9;
                padding-bottom: 5px;
            }}
            .info-label {{
                font-weight: bold;
                color: #7f8c8d;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            .json-data {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                border: 1px solid #e9ecef;
                font-family: monospace;
                white-space: pre-wrap;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="invoice-header">
            <h1>Facture Formatée</h1>
        </div>
        
        <div class="invoice-summary">
            <p><span class="info-label">Numéro de facture:</span> {invoice_number}</p>
            <p><span class="info-label">Date:</span> {date}</p>
            <p><span class="info-label">Client:</span> {client_name}</p>
            <p><span class="info-label">Montant total:</span> {total_amount} €</p>
        </div>
        
        <div class="invoice-container">
            {text_to_html(formatted_text)}
        </div>
        
        <h3>Données structurées extraites</h3>
        <div class="json-data">
            {json.dumps(json_output, indent=2, ensure_ascii=False)}
        </div>
    </body>
    </html>
    """
    
    return html