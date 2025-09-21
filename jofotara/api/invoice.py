import os
import uuid

import frappe
from frappe.model.document import Document

from jofotara.api.client import send_invoice_to_jofotara
from jofotara.xml.generator import generate_jofotara_invoice_xml as generate_xml


@frappe.whitelist()
def generate_and_view_xml(doctype, docname):
    """
    Generate JoFotara XML for viewing and download.
    """
    if doctype != "Sales Invoice":
        frappe.throw("Only Sales Invoice is supported")

    doc = frappe.get_doc(doctype, docname)
    xml_content = generate_xml(doc)

    # Save XML as attachment
    filename = f"{doc.name}_jofotara.xml"
    filepath = frappe.get_site_path("public", "files", filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(xml_content)

    doc.db_set("jofotara_xml_file", f"/files/{filename}")
    doc.db_set("jofotara_xml_generated", 1)

    return xml_content


def generate_jofotara_invoice_xml(docname):
    """
    Generate UBL-compliant XML for the given Sales Invoice.
    Uses the improved XML generator and saves the file.
    """
    doc = frappe.get_doc("Sales Invoice", docname)
    xml_content = generate_xml(doc)

    filename = f"{doc.name}_jofotara.xml"
    filepath = frappe.get_site_path("public", "files", filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(xml_content)

    doc.db_set("jofotara_xml_file", f"/files/{filename}")
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
