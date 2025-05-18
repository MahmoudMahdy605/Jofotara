import frappe
from frappe import _
import traceback
from datetime import datetime
from jofotara.xml.generator import generate_jofotara_invoice_xml


def auto_generate_jofotara_xml(doc, method):
    """
    Generate and attach JoFotara XML when a Sales Invoice is submitted.
    Also attempt to submit it to JoFotara API.
    """
    try:
        print(f"Generating JoFotara XML for Sales Invoice: {doc.name}")

        # Generate the XML
        xml_content = generate_jofotara_invoice_xml(doc)

        # Save XML as a private file attachment
        attachment = frappe.get_doc({
            "doctype": "File",
            "file_name": f"{doc.name}_jofotara.xml",
            "attached_to_doctype": "Sales Invoice",
            "attached_to_name": doc.name,
            "content": xml_content,
            "is_private": 1
        })
        attachment.insert()

        # Update XML-related custom fields
        if frappe.get_meta("Sales Invoice").has_field("jofotara_xml_generated"):
            doc.db_set("jofotara_xml_generated", 1)
        if frappe.get_meta("Sales Invoice").has_field("jofotara_xml_file"):
            doc.db_set("jofotara_xml_file", attachment.file_url)

        doc.add_comment("Info", _("JoFotara XML has been generated and attached."))

        # Attempt to submit the XML to the JoFotara API
        try:
            company = frappe.get_doc("Company", doc.company)
            response = submit_to_jofotara_api(xml_content, company)

            if response.get("success"):
                doc.db_set("jofotara_submission_status", "Success")
                doc.db_set("jofotara_submission_date", datetime.now())
                doc.add_comment("Info", _("✅ XML submitted to JoFotara successfully."))
                frappe.msgprint(_("✅ JoFotara XML successfully submitted."))
            else:
                raise Exception(response.get("error") or "Unknown submission error")

        except Exception as api_error:
            doc.db_set("jofotara_submission_status", "Failed")
            doc.add_comment("Info", _("❌ XML was not submitted to JoFotara: {0}").format(str(api_error)))
            frappe.log_error(f"JoFotara submission failed for {doc.name}: {str(api_error)}", "JoFotara Submission Error")
            frappe.msgprint(_("⚠️ JoFotara XML was generated but submission failed."))

    except Exception as e:
        error_details = traceback.format_exc()
        frappe.log_error(f"Error generating XML for {doc.name}:\n{error_details}", "JoFotara XML Generation Error")
        frappe.msgprint(_("❌ JoFotara XML was not generated. See Error Log for details."))
        doc.db_set("jofotara_xml_generated", 0)
        doc.add_comment("Info", _("❌ Failed to generate JoFotara XML."))


def submit_to_jofotara_api(xml_content, company):
    """
    Placeholder for sending XML to JoFotara API.
    Replace this with actual API call logic.
    """
    print("Sending XML to JoFotara...")
    # Sample simulation
    return {
        "success": True,
        # "error": "Authentication failed"  # use this to simulate failure
    }


# Hook-compatible alias
def on_submit(doc, method):
    auto_generate_jofotara_xml(doc, method)
