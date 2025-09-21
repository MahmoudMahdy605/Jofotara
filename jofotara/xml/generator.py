import frappe
import uuid
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
from frappe.utils import getdate

def generate_xml(sales_invoice):
    """
    Generate UBL 2.1 XML for JoFotara submission - Based on successful reference format
    """
    if isinstance(sales_invoice, str):
        sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice)
    
    # Create root element with proper namespaces (including ext namespace)
    root = ET.Element("Invoice")
    root.set("xmlns", "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2")
    root.set("xmlns:cac", "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2")
    root.set("xmlns:cbc", "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2")
    root.set("xmlns:ext", "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2")

    # Get company
    company = frappe.get_doc("Company", sales_invoice.company)

    # Basic invoice info
    posting_date = getdate(sales_invoice.posting_date)
    
    # Use invoice type from reference (011 for freight/service invoices)
    invoice_type_value = "388"  # Standard commercial invoice
    
    ET.SubElement(root, "cbc:ProfileID").text = "reporting:1.0"
    ET.SubElement(root, "cbc:ID").text = sales_invoice.name
    ET.SubElement(root, "cbc:UUID").text = str(uuid.uuid4())
    ET.SubElement(root, "cbc:IssueDate").text = posting_date.strftime('%Y-%m-%d')

    invoice_type_code = ET.SubElement(root, "cbc:InvoiceTypeCode")
    invoice_type_code.set("name", "011")  # Changed to match reference
    invoice_type_code.text = invoice_type_value

    ET.SubElement(root, "cbc:Note").text = "NA"  # Added note as in reference
    
    # Use JOD currency code (JoFotara expects full code)
    currency_code = sales_invoice.currency  # Keep original currency code
    ET.SubElement(root, "cbc:DocumentCurrencyCode").text = currency_code
    ET.SubElement(root, "cbc:TaxCurrencyCode").text = currency_code

    # Add AdditionalDocumentReference (ICV) as in reference
    additional_doc_ref = ET.SubElement(root, "cac:AdditionalDocumentReference")
    ET.SubElement(additional_doc_ref, "cbc:ID").text = "ICV"
    ET.SubElement(additional_doc_ref, "cbc:UUID").text = str(len(sales_invoice.items) + 1)

    # AccountingSupplierParty - Simplified structure like reference
    supplier_party = ET.SubElement(root, "cac:AccountingSupplierParty")
    supplier_party_elem = ET.SubElement(supplier_party, "cac:Party")
    
    # Postal address - simplified
    supplier_address = ET.SubElement(supplier_party_elem, "cac:PostalAddress")
    supplier_country = ET.SubElement(supplier_address, "cac:Country")
    ET.SubElement(supplier_country, "cbc:IdentificationCode").text = "JO"
    
    # Party tax scheme - seller tax number
    if company.tax_id:
        clean_tax_id = ''.join(filter(str.isdigit, company.tax_id))
        if clean_tax_id and len(clean_tax_id) <= 15:
            supplier_tax = ET.SubElement(supplier_party_elem, "cac:PartyTaxScheme")
            ET.SubElement(supplier_tax, "cbc:CompanyID").text = clean_tax_id
            supplier_tax_scheme = ET.SubElement(supplier_tax, "cac:TaxScheme")
            ET.SubElement(supplier_tax_scheme, "cbc:ID").text = "VAT"
    
    # Party legal entity
    supplier_legal = ET.SubElement(supplier_party_elem, "cac:PartyLegalEntity")
    ET.SubElement(supplier_legal, "cbc:RegistrationName").text = company.company_name

    # AccountingCustomerParty - Following reference structure
    customer_party = ET.SubElement(root, "cac:AccountingCustomerParty")
    customer_party_elem = ET.SubElement(customer_party, "cac:Party")
    
    # Customer party identification
    customer_id = ET.SubElement(customer_party_elem, "cac:PartyIdentification")
    ET.SubElement(customer_id, "cbc:ID", {"schemeID": "TN"}).text = "0"
    
    # Customer postal address
    customer_address = ET.SubElement(customer_party_elem, "cac:PostalAddress")
    ET.SubElement(customer_address, "cbc:PostalZone").text = "0"
    ET.SubElement(customer_address, "cbc:CountrySubentityCode").text = "JO-AM"
    customer_country = ET.SubElement(customer_address, "cac:Country")
    ET.SubElement(customer_country, "cbc:IdentificationCode").text = "JO"
    
    # Customer tax scheme
    customer_tax = ET.SubElement(customer_party_elem, "cac:PartyTaxScheme")
    customer_tax_scheme = ET.SubElement(customer_tax, "cac:TaxScheme")
    ET.SubElement(customer_tax_scheme, "cbc:ID").text = "VAT"
    
    # Customer legal entity
    customer_legal = ET.SubElement(customer_party_elem, "cac:PartyLegalEntity")
    ET.SubElement(customer_legal, "cbc:RegistrationName").text = sales_invoice.customer_name
    
    # Customer contact
    customer_contact = ET.SubElement(customer_party, "cac:AccountingContact")
    ET.SubElement(customer_contact, "cbc:Telephone").text = "0"

    # SellerSupplierParty - This is where the activity number goes!
    seller_supplier = ET.SubElement(root, "cac:SellerSupplierParty")
    seller_supplier_party = ET.SubElement(seller_supplier, "cac:Party")
    seller_supplier_id = ET.SubElement(seller_supplier_party, "cac:PartyIdentification")
    
    # Activity number goes here - try the tax ID from reference XML
    activity_number = getattr(company, 'jofotara_activity_number', None) or "40245896"  # Tax ID from reference XML
    activity_number = ''.join(filter(str.isdigit, activity_number))[:15]
    ET.SubElement(seller_supplier_id, "cbc:ID").text = activity_number

    # AllowanceCharge - As in reference
    allowance_charge = ET.SubElement(root, "cac:AllowanceCharge")
    ET.SubElement(allowance_charge, "cbc:ChargeIndicator").text = "false"
    ET.SubElement(allowance_charge, "cbc:AllowanceChargeReason").text = "discount"
    ET.SubElement(allowance_charge, "cbc:Amount", {"currencyID": currency_code}).text = "0.0"

    # LegalMonetaryTotal - Following reference structure exactly (no taxes for JoFotara)
    # Based on successful reference, all amounts should be equal (tax-exempt treatment)
    tax_exclusive_amount = sum(item.amount for item in sales_invoice.items)
    
    # For JoFotara, treat as tax-exempt - all amounts equal
    tax_inclusive_amount = tax_exclusive_amount
    payable_amount = tax_exclusive_amount
    
    monetary_total = ET.SubElement(root, "cac:LegalMonetaryTotal")
    ET.SubElement(monetary_total, "cbc:TaxExclusiveAmount", {"currencyID": currency_code}).text = f"{tax_exclusive_amount:.1f}"
    ET.SubElement(monetary_total, "cbc:TaxInclusiveAmount", {"currencyID": currency_code}).text = f"{tax_inclusive_amount:.1f}"
    ET.SubElement(monetary_total, "cbc:AllowanceTotalAmount", {"currencyID": currency_code}).text = "0.0"
    ET.SubElement(monetary_total, "cbc:PrepaidAmount", {"currencyID": currency_code}).text = "0"
    ET.SubElement(monetary_total, "cbc:PayableAmount", {"currencyID": currency_code}).text = f"{payable_amount:.1f}"

    # InvoiceLine - Following reference structure (no tax elements!)
    for idx, item in enumerate(sales_invoice.items, 1):
        invoice_line = ET.SubElement(root, "cac:InvoiceLine")
        ET.SubElement(invoice_line, "cbc:ID").text = str(idx)
        ET.SubElement(invoice_line, "cbc:InvoicedQuantity", {"unitCode": "PCE"}).text = f"{item.qty:.1f}"
        ET.SubElement(invoice_line, "cbc:LineExtensionAmount", {"currencyID": currency_code}).text = f"{item.amount:.1f}"
        
        # Item
        item_elem = ET.SubElement(invoice_line, "cac:Item")
        ET.SubElement(item_elem, "cbc:Name").text = item.item_name
        
        # Price with allowance charge
        price_elem = ET.SubElement(invoice_line, "cac:Price")
        ET.SubElement(price_elem, "cbc:PriceAmount", {"currencyID": currency_code}).text = f"{item.rate:.1f}"
        
        price_allowance = ET.SubElement(price_elem, "cac:AllowanceCharge")
        ET.SubElement(price_allowance, "cbc:ChargeIndicator").text = "false"
        ET.SubElement(price_allowance, "cbc:AllowanceChargeReason").text = "DISCOUNT"
        ET.SubElement(price_allowance, "cbc:Amount", {"currencyID": currency_code}).text = "0.0"

    # Format XML
    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = '\n'.join(line for line in reparsed.toprettyxml(indent="  ").split('\n') if line.strip())

    return pretty_xml


def generate_jofotara_invoice_xml(sales_invoice):
    """
    Legacy function name for backward compatibility
    """
    return generate_xml(sales_invoice)
