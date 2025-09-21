import frappe
import uuid
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

def generate_jofotara_invoice_xml(sales_invoice):
    if isinstance(sales_invoice, str):
        sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice)

    company = frappe.get_doc("Company", sales_invoice.company)

    posting_date = sales_invoice.posting_date
    if isinstance(posting_date, str):
        posting_date = datetime.strptime(posting_date, "%Y-%m-%d").date()

    # 🔍 Determine Invoice Type Code & Label
    is_credit = sales_invoice.is_return
    is_registered = getattr(company, "is_sales_tax_registered", 0)

    is_special_sales = False

    # Condition 1: Check taxes template name
    if getattr(sales_invoice, "taxes_and_charges", ""):
        tax_template_name = sales_invoice.taxes_and_charges.lower()
        if any(word in tax_template_name for word in ["special", "خاصة", "خاصه"]):
            is_special_sales = True

    # Condition 2: Check item-level tax templates
    for item in sales_invoice.items:
        if getattr(item, "item_tax_template", ""):
            item_tax_name = item.item_tax_template.lower()
            if any(word in item_tax_name for word in ["special", "خاصة", "خاصه"]):
                is_special_sales = True
                break

    # Final logic
    if not is_registered:
        invoice_type_value = "381" if is_credit else "388"
        invoice_type_label = "Credit Invoice for Income Tax" if is_credit else "Income Invoice"
    elif is_special_sales:
        invoice_type_value = "381" if is_credit else "388"
        invoice_type_label = "Credit Invoice for Special Sales" if is_credit else "Special Sales Invoice"
    else:
        invoice_type_value = "381" if is_credit else "388"
        invoice_type_label = "Credit Invoice for General Sales" if is_credit else "General Sales Invoice"

    try:
        sales_invoice.db_set("jofotara_invoice_type_label", invoice_type_label)
    except Exception as e:
        frappe.log_error(f"Failed to set invoice type label: {str(e)}")

    def generate_xml(sales_invoice):
        """
        Generate UBL 2.1 XML for JoFotara submission - Based on successful reference format
        """
        # Create root element with proper namespaces (including ext namespace)
        root = ET.Element("Invoice")
        root.set("xmlns", "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2")
        root.set("xmlns:cac", "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2")
        root.set("xmlns:cbc", "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2")
        root.set("xmlns:ext", "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2")

        # Get company
        company = frappe.get_doc("Company", sales_invoice.company)

        # Basic invoice info
        posting_date = datetime.strptime(sales_invoice.posting_date, "%Y-%m-%d").date()
    seller_name = ET.SubElement(seller_party_elem, "cac:PartyName")
    ET.SubElement(seller_name, "cbc:Name").text = company.company_name
    
    # Seller postal address
    seller_address = ET.SubElement(seller_party_elem, "cac:PostalAddress")
    ET.SubElement(seller_address, "cbc:StreetName").text = getattr(company, 'address_line_1', '') or getattr(company, 'address', '') or "N/A"
    ET.SubElement(seller_address, "cbc:CityName").text = getattr(company, 'city', '') or "N/A"
    ET.SubElement(seller_address, "cbc:PostalZone").text = getattr(company, 'pincode', '') or getattr(company, 'postal_code', '') or "00000"
    
    seller_country = ET.SubElement(seller_address, "cac:Country")
    ET.SubElement(seller_country, "cbc:IdentificationCode").text = company.country or "JO"
    
    # Seller tax scheme (fixed order) - ensure tax_id is digits only
    if company.tax_id:
        # Clean tax_id to contain only digits
        clean_tax_id = ''.join(filter(str.isdigit, company.tax_id))
        if clean_tax_id and len(clean_tax_id) <= 15:
            seller_tax = ET.SubElement(seller_party_elem, "cac:PartyTaxScheme")
            ET.SubElement(seller_tax, "cbc:CompanyID").text = clean_tax_id
            seller_tax_scheme = ET.SubElement(seller_tax, "cac:TaxScheme")
            ET.SubElement(seller_tax_scheme, "cbc:ID").text = "VAT"
    
    # Seller legal entity
    seller_legal = ET.SubElement(seller_party_elem, "cac:PartyLegalEntity")
    ET.SubElement(seller_legal, "cbc:RegistrationName").text = company.company_name
    
    # Add activity number (required by JoFotara) with proper scheme
    activity_number = getattr(company, 'jofotara_activity_number', None) or "1234567890"
    activity_number = ''.join(filter(str.isdigit, activity_number))[:15]  # Ensure digits only, max 15
    if activity_number:
        ET.SubElement(seller_legal, "cbc:CompanyID", {"schemeID": "ACTIVITY", "schemeAgencyID": "JO"}).text = activity_number

    # Buyer
    customer_party = ET.SubElement(root, "cac:AccountingCustomerParty")
    customer_party_elem = ET.SubElement(customer_party, "cac:Party")

    ET.SubElement(
        ET.SubElement(customer_party_elem, "cac:PartyLegalEntity"),
        "cbc:RegistrationName"
    ).text = sales_invoice.customer_name

    customer_doc = frappe.get_doc("Customer", sales_invoice.customer)
    if getattr(customer_doc, "tax_id", None):
        customer_tax = ET.SubElement(customer_party_elem, "cac:PartyTaxScheme")
        ET.SubElement(customer_tax, "cbc:CompanyID").text = customer_doc.tax_id
        customer_tax_scheme = ET.SubElement(customer_tax, "cac:TaxScheme")
        ET.SubElement(customer_tax_scheme, "cbc:ID").text = "VAT"

    if getattr(customer_doc, "phone", None):
        ET.SubElement(
            ET.SubElement(customer_party_elem, "cac:Contact"),
            "cbc:Telephone"
        ).text = customer_doc.phone

    # Tax Total (must come before InvoiceLine in UBL 2.1)
    tax_exclusive_amount = sum(item.amount for item in sales_invoice.items)
    total_tax_amount = sales_invoice.total_taxes_and_charges or 0
    
    if total_tax_amount > 0:
        tax_total = ET.SubElement(root, "cac:TaxTotal")
        ET.SubElement(tax_total, "cbc:TaxAmount", {"currencyID": sales_invoice.currency}).text = f"{total_tax_amount:.2f}"
        
        # Tax Subtotal
        tax_subtotal = ET.SubElement(tax_total, "cac:TaxSubtotal")
        ET.SubElement(tax_subtotal, "cbc:TaxableAmount", {"currencyID": sales_invoice.currency}).text = f"{tax_exclusive_amount:.2f}"
        ET.SubElement(tax_subtotal, "cbc:TaxAmount", {"currencyID": sales_invoice.currency}).text = f"{total_tax_amount:.2f}"
        
        tax_category = ET.SubElement(tax_subtotal, "cac:TaxCategory")
        ET.SubElement(tax_category, "cbc:ID").text = "S"
        ET.SubElement(tax_category, "cbc:Percent").text = "16.00"  # Jordan VAT rate
        ET.SubElement(
            ET.SubElement(tax_category, "cac:TaxScheme"),
            "cbc:ID"
        ).text = "VAT"

    # Legal Monetary Total (must come before InvoiceLine in UBL 2.1)
    tax_inclusive_amount = sales_invoice.grand_total
    monetary_total = ET.SubElement(root, "cac:LegalMonetaryTotal")
    ET.SubElement(monetary_total, "cbc:LineExtensionAmount", {"currencyID": sales_invoice.currency}).text = f"{tax_exclusive_amount:.2f}"
    ET.SubElement(monetary_total, "cbc:TaxExclusiveAmount", {"currencyID": sales_invoice.currency}).text = f"{tax_exclusive_amount:.2f}"
    ET.SubElement(monetary_total, "cbc:TaxInclusiveAmount", {"currencyID": sales_invoice.currency}).text = f"{tax_inclusive_amount:.2f}"
    
    # Add special taxes amount (required by JoFotara)
    special_taxes_amount = 0.0  # No special taxes in this case
    ET.SubElement(monetary_total, "cbc:AllowanceTotalAmount", {"currencyID": sales_invoice.currency}).text = f"{special_taxes_amount:.2f}"
    
    ET.SubElement(monetary_total, "cbc:PayableAmount", {"currencyID": sales_invoice.currency}).text = f"{sales_invoice.grand_total:.2f}"

    # Invoice Lines (must come last in UBL 2.1)
    for idx, item in enumerate(sales_invoice.items, 1):
        invoice_line = ET.SubElement(root, "cac:InvoiceLine")
        ET.SubElement(invoice_line, "cbc:ID").text = str(idx)
        ET.SubElement(invoice_line, "cbc:InvoicedQuantity", {"unitCode": "PCE"}).text = str(item.qty)
        ET.SubElement(invoice_line, "cbc:LineExtensionAmount", {"currencyID": sales_invoice.currency}).text = f"{item.amount:.2f}"

        # Tax information for invoice line
        if total_tax_amount > 0:
            line_tax_total = ET.SubElement(invoice_line, "cac:TaxTotal")
            line_tax_amount = (item.amount * total_tax_amount) / tax_exclusive_amount if tax_exclusive_amount > 0 else 0
            ET.SubElement(line_tax_total, "cbc:TaxAmount", {"currencyID": sales_invoice.currency}).text = f"{line_tax_amount:.2f}"
            
            line_tax_subtotal = ET.SubElement(line_tax_total, "cac:TaxSubtotal")
            ET.SubElement(line_tax_subtotal, "cbc:TaxableAmount", {"currencyID": sales_invoice.currency}).text = f"{item.amount:.2f}"
            ET.SubElement(line_tax_subtotal, "cbc:TaxAmount", {"currencyID": sales_invoice.currency}).text = f"{line_tax_amount:.2f}"
            
            line_tax_category = ET.SubElement(line_tax_subtotal, "cac:TaxCategory")
            ET.SubElement(line_tax_category, "cbc:ID").text = "S"
            ET.SubElement(line_tax_category, "cbc:Percent").text = "16.00"
            ET.SubElement(
                ET.SubElement(line_tax_category, "cac:TaxScheme"),
                "cbc:ID"
            ).text = "VAT"

        item_elem = ET.SubElement(invoice_line, "cac:Item")
        ET.SubElement(item_elem, "cbc:Name").text = item.item_name
        
        # Add item tax category
        if total_tax_amount > 0:
            item_tax_category = ET.SubElement(item_elem, "cac:ClassifiedTaxCategory")
            ET.SubElement(item_tax_category, "cbc:ID").text = "S"
            ET.SubElement(item_tax_category, "cbc:Percent").text = "16.00"
            ET.SubElement(
                ET.SubElement(item_tax_category, "cac:TaxScheme"),
                "cbc:ID"
            ).text = "VAT"

        ET.SubElement(
            ET.SubElement(invoice_line, "cac:Price"),
            "cbc:PriceAmount", {"currencyID": sales_invoice.currency}
        ).text = f"{item.rate:.2f}"

    # Format
    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = '\n'.join(line for line in reparsed.toprettyxml(indent="  ").split('\n') if line.strip())

    return pretty_xml
