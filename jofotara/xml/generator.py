import frappe
import uuid
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

def generate_jofotara_invoice_xml(sales_invoice):
    """
    Generate XML for JoFotara e-invoicing system based on UBL 2.1 standard.
    
    Args:
        sales_invoice: Frappe Sales Invoice document
        
    Returns:
        str: Formatted XML string
    """
    # Get the sales invoice document if string is passed
    if isinstance(sales_invoice, str):
        sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice)
    
    # Get company details
    company = frappe.get_doc("Company", sales_invoice.company)

    # Fix posting_date format if it's a string
    posting_date = sales_invoice.posting_date
    if isinstance(posting_date, str):
        posting_date = datetime.strptime(posting_date, "%Y-%m-%d").date()
    
    # Create root element with namespaces
    root = ET.Element("Invoice", {
        "xmlns": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
        "xmlns:cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
        "xmlns:cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
    })
    
    # Add ProfileID
    profile_id = ET.SubElement(root, "cbc:ProfileID")
    profile_id.text = "reporting:1.0"
    
    # Add Invoice ID
    invoice_id = ET.SubElement(root, "cbc:ID")
    invoice_id.text = sales_invoice.name
    
    # Add UUID
    uuid_elem = ET.SubElement(root, "cbc:UUID")
    uuid_elem.text = str(uuid.uuid4())
    
    # Add Issue Date
    issue_date = ET.SubElement(root, "cbc:IssueDate")
    issue_date.text = posting_date.strftime('%Y-%m-%d')
    
    # Add Invoice Type Code
    invoice_type_code = ET.SubElement(root, "cbc:InvoiceTypeCode")
    invoice_type_code.set("name", "012")
    invoice_type_code.text = "388"  # Standard sales invoice
    
    # Add Document Currency Code
    currency_code = ET.SubElement(root, "cbc:DocumentCurrencyCode")
    currency_code.text = sales_invoice.currency
    
    # Add Accounting Supplier Party (Seller)
    supplier_party = ET.SubElement(root, "cac:AccountingSupplierParty")
    supplier_party_elem = ET.SubElement(supplier_party, "cac:Party")
    
    # Add Tax Scheme for supplier
    party_tax_scheme = ET.SubElement(supplier_party_elem, "cac:PartyTaxScheme")
    company_id = ET.SubElement(party_tax_scheme, "cbc:CompanyID")
    company_id.text = company.tax_id if company.tax_id else "NA"
    
    tax_scheme = ET.SubElement(party_tax_scheme, "cac:TaxScheme")
    tax_scheme_id = ET.SubElement(tax_scheme, "cbc:ID")
    tax_scheme_id.text = "VAT"
    
    # Add Legal Entity for supplier
    party_legal_entity = ET.SubElement(supplier_party_elem, "cac:PartyLegalEntity")
    registration_name = ET.SubElement(party_legal_entity, "cbc:RegistrationName")
    registration_name.text = company.company_name
    
    # Add Accounting Customer Party (Buyer)
    customer_party = ET.SubElement(root, "cac:AccountingCustomerParty")
    customer_party_elem = ET.SubElement(customer_party, "cac:Party")
    
    # Add Legal Entity for customer
    customer_legal_entity = ET.SubElement(customer_party_elem, "cac:PartyLegalEntity")
    customer_registration_name = ET.SubElement(customer_legal_entity, "cbc:RegistrationName")
    customer_registration_name.text = sales_invoice.customer_name
    
    # Add customer tax ID if available
    customer_doc = frappe.get_doc("Customer", sales_invoice.customer)
    if hasattr(customer_doc, 'tax_id') and customer_doc.tax_id:
        customer_tax_scheme = ET.SubElement(customer_party_elem, "cac:PartyTaxScheme")
        customer_company_id = ET.SubElement(customer_tax_scheme, "cbc:CompanyID")
        customer_company_id.text = customer_doc.tax_id
        customer_tax_scheme_elem = ET.SubElement(customer_tax_scheme, "cac:TaxScheme")
        customer_tax_scheme_id = ET.SubElement(customer_tax_scheme_elem, "cbc:ID")
        customer_tax_scheme_id.text = "VAT"
    
    # Add contact information if available
    if hasattr(customer_doc, 'phone') and customer_doc.phone:
        contact = ET.SubElement(customer_party_elem, "cac:Contact")
        telephone = ET.SubElement(contact, "cbc:Telephone")
        telephone.text = customer_doc.phone
    
    # Calculate totals
    tax_exclusive_amount = 0
    tax_inclusive_amount = 0
    
    # Add Invoice Lines
    for idx, item in enumerate(sales_invoice.items, 1):
        invoice_line = ET.SubElement(root, "cac:InvoiceLine")
        
        # Line ID
        line_id = ET.SubElement(invoice_line, "cbc:ID")
        line_id.text = str(idx)
        
        # Quantity
        quantity = ET.SubElement(invoice_line, "cbc:InvoicedQuantity")
        quantity.set("unitCode", "PCE")  # Piece as default unit code
        quantity.text = str(item.qty)
        
        # Line Extension Amount (Amount without tax)
        line_amount = ET.SubElement(invoice_line, "cbc:LineExtensionAmount")
        line_amount.set("currencyID", sales_invoice.currency)
        line_extension_amount = item.amount
        line_amount.text = "{:.2f}".format(line_extension_amount)
        
        # Item details
        item_elem = ET.SubElement(invoice_line, "cac:Item")
        item_name = ET.SubElement(item_elem, "cbc:Name")
        item_name.text = item.item_name
        
        # Price
        price_elem = ET.SubElement(invoice_line, "cac:Price")
        price_amount = ET.SubElement(price_elem, "cbc:PriceAmount")
        price_amount.set("currencyID", sales_invoice.currency)
        price_amount.text = "{:.2f}".format(item.rate)
        
        # Accumulate totals
        tax_exclusive_amount += line_extension_amount
    
    # Calculate tax inclusive amount
    tax_inclusive_amount = sales_invoice.grand_total
    
    # Add Legal Monetary Total
    monetary_total = ET.SubElement(root, "cac:LegalMonetaryTotal")
    
    # Tax Exclusive Amount
    tax_exclusive_elem = ET.SubElement(monetary_total, "cbc:TaxExclusiveAmount")
    tax_exclusive_elem.set("currencyID", sales_invoice.currency)
    tax_exclusive_elem.text = "{:.2f}".format(tax_exclusive_amount)
    
    # Tax Inclusive Amount
    tax_inclusive_elem = ET.SubElement(monetary_total, "cbc:TaxInclusiveAmount")
    tax_inclusive_elem.set("currencyID", sales_invoice.currency)
    tax_inclusive_elem.text = "{:.2f}".format(tax_inclusive_amount)
    
    # Payable Amount
    payable_amount_elem = ET.SubElement(monetary_total, "cbc:PayableAmount")
    payable_amount_elem.set("currencyID", sales_invoice.currency)
    payable_amount_elem.text = "{:.2f}".format(sales_invoice.grand_total)
    
    # Convert to string and format
    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Remove extra blank lines that minidom sometimes adds
    lines = [line for line in pretty_xml.split('\n') if line.strip()]
    pretty_xml = '\n'.join(lines)
    
    return pretty_xml
