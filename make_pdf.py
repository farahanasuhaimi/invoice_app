# generate_pdf.py
from xhtml2pdf import pisa
from flask import render_template
from models import Invoice  

def generate_invoice_pdf(invoice_id):
    # Check if the invoice with the provided ID exists in the database
    invoice = Invoice.query.get(invoice_id)
    if invoice is None:
        return None, "Invoice not found."

    # Generate HTML content for the invoice using a template
    html = render_template('invoice.html', invoice=invoice)
    
    # Define the file path for the PDF invoice
    pdf_file = f'invoices/invoice_{invoice_id}.pdf'
    
    # Generate the PDF invoice from the HTML content
    with open(pdf_file, 'w+b') as result_file:
        pisa_status = pisa.CreatePDF(html, dest=result_file)
    
    # Check if PDF generation was successful
    if pisa_status.err:
        return None, "Failed to generate PDF."
    
    # Return the file path of the generated PDF invoice
    return pdf_file, None
