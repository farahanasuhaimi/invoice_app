from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from xhtml2pdf import pisa
# import os
from flask_wtf import CSRFProtect

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///invoice_app.db'
# app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')
app.config['SECRET_KEY'] = 'my_local_secret_key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
csrf = CSRFProtect(app)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    cost = db.Column(db.Numeric(10,2), nullable=False)
    type = db.Column(db.String(100), nullable=False)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(20), unique=True, nullable=False)  # Updated field name
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.now)
    total = db.Column(db.Float, nullable=False)
    client = db.relationship('Client', backref=db.backref('invoices', lazy=True))

class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    cost = db.Column(db.Float, nullable=False)
    invoice = db.relationship('Invoice', backref=db.backref('items', lazy=True))
    service = db.relationship('Service', backref=db.backref('items', lazy=True))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_invoice', methods=['GET', 'POST'])
def create_invoice():
    if request.method == 'POST':
        client_id = request.form['client']
        services = request.form.getlist('service')
        quantities = request.form.getlist('quantity')
        
        current_date = datetime.now()
        year_month = current_date.strftime("%Y%m")

        latest_invoice = db.session.query(Invoice).filter(Invoice.invoice_number.like(f"{year_month}%")).order_by(Invoice.invoice_number.desc()).first()
        if latest_invoice:
            last_invoice_number = int(latest_invoice.invoice_number[-4:])
            new_invoice_number = last_invoice_number + 1
        else:
            new_invoice_number = 1
        
        new_invoice_number_str = f"{year_month}{new_invoice_number:04d}"
        

        invoice = Invoice(invoice_number=new_invoice_number_str, client_id=client_id, total=0)
        db.session.add(invoice)
        db.session.commit()

        total_cost = 0
        for service_id, quantity in zip(services, quantities):
            service = Service.query.get(service_id)
            cost = service.cost * int(quantity)
            total_cost += cost

            invoice_item = InvoiceItem(invoice_id=invoice.id, service_id=service_id, quantity=quantity, cost=cost)
            db.session.add(invoice_item)
        
        invoice.total = total_cost
        db.session.commit()
        
        generate_invoice_pdf(invoice.id)
        return redirect(url_for('view_invoice', invoice_id=invoice.id))

    clients = Client.query.all()
    services = Service.query.all()
    return render_template('create_invoice.html', clients=clients, services=services)

@app.route('/insert_service', methods=['GET', 'POST'])
def insert_service():
    if request.method == 'POST':
        description = request.form['description']
        cost = request.form['cost']
        type = request.form['type']
        service = Service(description=description, cost=cost, type=type)
        db.session.add(service)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('insert_service.html')  

@app.route('/delete_service/<int:id>', methods=['POST'])
def delete_service(id):
    service = Service.query.get_or_404(id)
    db.session.delete(service)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/insert_client', methods=['GET', 'POST'])
def insert_client():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        client = Client(name=name, email=email, phone=phone, address=address)
        db.session.add(client)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('insert_client.html')

@app.route('/invoice/<int:invoice_id>')
def view_invoice(invoice_id):
    invoice = Invoice.query.get(invoice_id)
    return render_template('view_invoice.html', invoice=invoice)

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

if __name__ == '__main__':
    with app.app_context():  # Ensure db.create_all() runs within the application context
        # db.drop_all()
        db.create_all()
    app.run(debug=True)
