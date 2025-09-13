import frappe
import os
import uuid
from frappe.model.document import Document
from jofotara.api.client import send_invoice_to_jofotara


def generate_jofotara_invoice_xml(docname):
    """
    Generate UBL-compliant XML for the given Sales Invoice.
    Saves the XML file under public/files and updates the doc.
    """
    doc = frappe.get_doc("Sales Invoice", docname)
    company = frappe.get_doc("Company", doc.company)
    customer = frappe.get_doc("Customer", doc.customer)

    invoice_uuid = str(uuid.uuid4())

    xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    <cbc:ProfileID>reporting:1.0</cbc:ProfileID>
    <cbc:ID>{doc.name}</cbc:ID>
    <cbc:UUID>{invoice_uuid}</cbc:UUID>
    <cbc:IssueDate>{doc.posting_date}</cbc:IssueDate>
    <cbc:InvoiceTypeCode name="012">388</cbc:InvoiceTypeCode>
    <cbc:DocumentCurrencyCode>{doc.currency}</cbc:DocumentCurrencyCode>

    <cac:AccountingSupplierParty>
        <cac:Party>
            <cac:PartyTaxScheme>
                <cbc:CompanyID>{company.tax_id or "000000000"}</cbc:CompanyID>
                <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
            </cac:PartyTaxScheme>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName>{company.company_name or company.name}</cbc:RegistrationName>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingSupplierParty>

    <cac:AccountingCustomerParty>
        <cac:Party>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName>{customer.customer_name or doc.customer}</cbc:RegistrationName>
            </cac:PartyLegalEntity>
            <cac:PartyTaxScheme>
                <cbc:CompanyID>{customer.tax_id or "000000000"}</cbc:CompanyID>
                <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
            </cac:PartyTaxScheme>
        </cac:Party>
    </cac:AccountingCustomerParty>
'''

    for i, item in enumerate(doc.items, start=1):
        xml_content += f'''
    <cac:InvoiceLine>
        <cbc:ID>{i}</cbc:ID>
        <cbc:InvoicedQuantity unitCode="PCE">{item.qty}</cbc:InvoicedQuantity>
        <cbc:LineExtensionAmount currencyID="{doc.currency}">{item.amount}</cbc:LineExtensionAmount>
        <cac:Item><cbc:Name>{item.item_name}</cbc:Name></cac:Item>
        <cac:Price><cbc:PriceAmount currencyID="{doc.currency}">{item.rate}</cbc:PriceAmount></cac:Price>
    </cac:InvoiceLine>
'''

    xml_content += f'''
    <cac:LegalMonetaryTotal>
        <cbc:TaxExclusiveAmount currencyID="{doc.currency}">{doc.net_total}</cbc:TaxExclusiveAmount>
        <cbc:TaxInclusiveAmount currencyID="{doc.currency}">{doc.grand_total}</cbc:TaxInclusiveAmount>
        <cbc:PayableAmount currencyID="{doc.currency}">{doc.rounded_total}</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>
</Invoice>'''

    filename = f"{doc.name}_jofotara.xml"
    filepath = frappe.get_site_path("public", "files", filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(xml_content)

    doc.db_set("jofotara_xml_file", filename)
    return xml_content


@frappe.whitelist()
def submit_to_jofotara(docname):
    """
    Submit Sales Invoice XML to JoFotara and store response.
    """
    doc = frappe.get_doc("Sales Invoice", docname)

    # Generate XML if not already attached
    if not doc.jofotara_xml_file:
        xml = generate_jofotara_invoice_xml(docname)
    else:
        xml_path = doc.jofotara_xml_file

        if xml_path.startswith("/private/files/"):
            full_path = frappe.get_site_path("private", "files", os.path.basename(xml_path))
        else:
            full_path = frappe.get_site_path("public", "files", os.path.basename(xml_path))

        with open(full_path, "r", encoding="utf-8") as f:
            xml = f.read()

    # Submit to JoFotara
    result = send_invoice_to_jofotara(doc, xml)

    if result["status"] == "success":
        doc.db_set("jofotara_submission_status", "Submitted")
        doc.db_set("jofotara_submission_time", frappe.utils.now())
        doc.db_set("jofotara_submission_response", str(result["response"]))
    else:
        doc.db_set("jofotara_submission_status", "Rejected")
        doc.db_set("jofotara_submission_time", frappe.utils.now())
        doc.db_set("jofotara_submission_response", result.get("error") or "Unknown error")

    return result
