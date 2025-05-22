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

    # 🧱 XML Build
    root = ET.Element("Invoice", {
        "xmlns": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
        "xmlns:cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
        "xmlns:cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
    })

    ET.SubElement(root, "cbc:ProfileID").text = "reporting:1.0"
    ET.SubElement(root, "cbc:ID").text = sales_invoice.name
    ET.SubElement(root, "cbc:UUID").text = str(uuid.uuid4())
    ET.SubElement(root, "cbc:IssueDate").text = posting_date.strftime('%Y-%m-%d')

    invoice_type_code = ET.SubElement(root, "cbc:InvoiceTypeCode")
    invoice_type_code.set("name", "012")
    invoice_type_code.text = invoice_type_value

    ET.SubElement(root, "cbc:DocumentCurrencyCode").text = sales_invoice.currency

    # Seller
    supplier_party = ET.SubElement(root, "cac:AccountingSupplierParty")
    supplier_party_elem = ET.SubElement(supplier_party, "cac:Party")
    tax_scheme = ET.SubElement(
        ET.SubElement(supplier_party_elem, "cac:PartyTaxScheme"),
        "cac:TaxScheme"
    )
    ET.SubElement(tax_scheme, "cbc:ID").text = "VAT"
    ET.SubElement(supplier_party_elem.find("cac:PartyTaxScheme"), "cbc:CompanyID").text = company.tax_id or "NA"

    ET.SubElement(
        ET.SubElement(supplier_party_elem, "cac:PartyLegalEntity"),
        "cbc:RegistrationName"
    ).text = company.company_name

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
        ET.SubElement(
            ET.SubElement(customer_tax, "cac:TaxScheme"),
            "cbc:ID"
        ).text = "VAT"

    if getattr(customer_doc, "phone", None):
        ET.SubElement(
            ET.SubElement(customer_party_elem, "cac:Contact"),
            "cbc:Telephone"
        ).text = customer_doc.phone

    # Lines
    tax_exclusive_amount = 0
    for idx, item in enumerate(sales_invoice.items, 1):
        invoice_line = ET.SubElement(root, "cac:InvoiceLine")
        ET.SubElement(invoice_line, "cbc:ID").text = str(idx)
        ET.SubElement(invoice_line, "cbc:InvoicedQuantity", {"unitCode": "PCE"}).text = str(item.qty)
        ET.SubElement(invoice_line, "cbc:LineExtensionAmount", {"currencyID": sales_invoice.currency}).text = "{:.2f}".format(item.amount)

        item_elem = ET.SubElement(invoice_line, "cac:Item")
        ET.SubElement(item_elem, "cbc:Name").text = item.item_name

        ET.SubElement(
            ET.SubElement(invoice_line, "cac:Price"),
            "cbc:PriceAmount", {"currencyID": sales_invoice.currency}
        ).text = "{:.2f}".format(item.rate)

        tax_exclusive_amount += item.amount

    tax_inclusive_amount = sales_invoice.grand_total

    monetary_total = ET.SubElement(root, "cac:LegalMonetaryTotal")
    ET.SubElement(monetary_total, "cbc:TaxExclusiveAmount", {"currencyID": sales_invoice.currency}).text = "{:.2f}".format(tax_exclusive_amount)
    ET.SubElement(monetary_total, "cbc:TaxInclusiveAmount", {"currencyID": sales_invoice.currency}).text = "{:.2f}".format(tax_inclusive_amount)
    ET.SubElement(monetary_total, "cbc:PayableAmount", {"currencyID": sales_invoice.currency}).text = "{:.2f}".format(sales_invoice.grand_total)

    # Format
    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = '\n'.join(line for line in reparsed.toprettyxml(indent="  ").split('\n') if line.strip())

    return pretty_xml
