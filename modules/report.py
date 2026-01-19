from fpdf import FPDF

class PDFReport(FPDF):
    def header(self):
        # En-tête du PDF
        self.set_font('Arial', 'B', 15)
        self.set_text_color(255, 75, 75) # Rouge Streamlit
        self.cell(0, 10, 'GhostTracker - Rapport d\'Investigation', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        # Pied de page
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def add_finding(self, res):
        # Titre de la carte (Site + Username)
        # On nettoie les caractères non-latin-1 pour éviter les crashs FPDF basiques
        try:
            category = res.get('category', 'autre').upper()
            site = res['site'].encode('latin-1', 'replace').decode('latin-1')
            username = res['username'].encode('latin-1', 'replace').decode('latin-1')
            
            title = f"[{category}] {site} - {username}"
            
            self.set_font('Arial', 'B', 11)
            self.set_text_color(0, 0, 0)
            self.cell(0, 8, title, 0, 1)
            
            # Lien
            self.set_font('Arial', 'I', 9)
            self.set_text_color(0, 0, 255)
            self.cell(0, 5, res['url'], 0, 1, link=res['url'])
            
            # Métadonnées
            self.set_text_color(50, 50, 50)
            self.set_font('Arial', '', 9)
            
            meta = res.get('metadata', {})
            text_block = ""
            for k, v in meta.items():
                if "Avatar" not in k:
                    # Nettoyage des caractères spéciaux (ex: émojis) qui cassent le PDF
                    safe_v = str(v).encode('latin-1', 'replace').decode('latin-1')
                    text_block += f"- {k}: {safe_v}\n"
            
            if text_block:
                self.multi_cell(0, 5, text_block)
            
            self.ln(5)
            
        except Exception as e:
            print(f"Erreur encodage PDF sur un item: {e}")

def generate_pdf(results, target_input):
    pdf = PDFReport()
    pdf.add_page()
    
    # Titre principal
    pdf.set_font('Arial', 'B', 12)
    # Nettoyage du titre
    safe_target = target_input.encode('latin-1', 'replace').decode('latin-1')
    
    pdf.cell(0, 10, f"Cible : {safe_target}", 0, 1)
    pdf.cell(0, 10, f"Traces trouvees : {len(results)}", 0, 1)
    pdf.ln(10)

    # Boucle sur les résultats
    for res in results:
        pdf.add_finding(res)

    # Retourne le binaire du PDF compatible Streamlit
    return pdf.output(dest='S').encode('latin-1', 'replace')