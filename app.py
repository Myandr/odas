from flask import Flask, render_template, request,send_from_directory
import fitz  # PyMuPDF
import spacy
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'handbuch.pdf'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Lade das Spacy-Modell für die deutsche Sprache
nlp = spacy.load('de_core_news_sm')

# Funktion, um die PDF zu laden und Texte sowie Überschriften zu extrahieren
def extrahiere_texte_und_ueberschriften(pdf_document):
    ueberschriften = []
    texte_unter_ueberschriften = {}
    
    # Alle Seiten durchlaufen
    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        
        # Extrahiere Text und überprüfe Formatierung
        blocks = page.get_text("dict")["blocks"]
        
        aktuelle_ueberschrift = None  # Initialisiert die Überschrift, wenn eine gefunden wird
        
        for block in blocks:
            if block['type'] == 0:  # Nur Textblöcke
                for line in block['lines']:
                    for span in line['spans']:
                        text = span['text']
                        # Wenn der Text fett ist, nehmen wir ihn als Überschrift
                        if "bold" in span['font'].lower():
                            aktuelle_ueberschrift = text.strip()  # Setze die aktuelle Überschrift
                            ueberschriften.append(aktuelle_ueberschrift)  # Füge die Überschrift zur Liste hinzu
                            texte_unter_ueberschriften[aktuelle_ueberschrift] = []  # Lege einen Eintrag für den Text unter der Überschrift an
                        elif aktuelle_ueberschrift:  # Wenn eine Überschrift existiert
                            texte_unter_ueberschriften[aktuelle_ueberschrift].append(text.strip())  # Füge den Text unter der Überschrift hinzu
    
    return ueberschriften, texte_unter_ueberschriften

# Funktion, um Füllwörter zu entfernen und nur die Schlüsselwörter zu extrahieren
def bereinige_frage(frage):
    doc = nlp(frage.lower())  # Frage in ein Spacy-Dokument umwandeln und normalisieren
    schluesselwoerter = [token.text for token in doc if not token.is_stop and not token.is_punct]
    return schluesselwoerter

# Funktion, die nach der Frage sucht und die passenden Antworten ausgibt
def beantworte_frage(question, ueberschriften, texte_unter_ueberschriften):
    # Bereinige die Frage, um nur Schlüsselwörter zu verwenden
    bereinigte_frage = bereinige_frage(question)
    
    passende_antworten = []
    
    # Suche nach der besten Übereinstimmung in den Überschriften
    for ueberschrift in ueberschriften:
        match_count = sum(1 for word in bereinigte_frage if word in ueberschrift.lower())
        
        if match_count > 0:  # Wenn es eine Übereinstimmung gibt
            passende_antworten.append({
                'ueberschrift': ueberschrift,
                'antwort': "\n".join(texte_unter_ueberschriften[ueberschrift])
            })
    
    if passende_antworten:
        return passende_antworten
    else:
        return "Keine passende Antwort gefunden."

# Route für die Startseite und Fragebeantwortung
@app.route('/', methods=['GET', 'POST'])
def index():
    frage = ""
    antwort_text = ""
    
    if request.method == 'POST':
        frage = request.form['frage']
        
        # PDF laden
        pdf_document = fitz.open("handbuch.pdf")
        
        # Extrahiere Überschriften und Texte
        ueberschriften, texte_unter_ueberschriften = extrahiere_texte_und_ueberschriften(pdf_document)
        
        # Beantworte die Frage
        antwort_text = beantworte_frage(frage, ueberschriften, texte_unter_ueberschriften)
    
    return render_template('index.html', frage=frage, antwort=antwort_text)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
