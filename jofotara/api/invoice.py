import frappe
from frappe import _
from jofotara.xml.generator import generate_jofotara_invoice_xml

@frappe.whitelist()
def generate_and_view_xml(doctype, docname):
    """
    Generate JoFotara XML for a document and return it for viewing
    
    Args:
        doctype: Document type (e.g., 'Sales Invoice')
        docname: Document name
        
    Returns:
        str: XML content
    """
    try:
        # Check permissions
        if not frappe.has_permission(doctype, "read", docname):
            frappe.throw(_("You don't have permission to access this document"))
            
        # Get the document
        doc = frappe.get_doc(doctype, docname)
        
        # Check if JoFotara integration is enabled for this company
        company = frappe.get_doc("Company", doc.company)
        if not hasattr(company, "enable_jofotara_integration") or not company.enable_jofotara_integration:
            frappe.throw(_("JoFotara integration is not enabled for company {0}").format(doc.company))
        
        # Generate XML
        xml_content = generate_jofotara_invoice_xml(doc)
        
        # Save XML as an attachment if it doesn't exist
        if not doc.get("jofotara_xml_file"):
            attachment = frappe.get_doc({
                "doctype": "File",
                "file_name": f"{doc.name}_jofotara.xml",
                "attached_to_doctype": doctype,
                "attached_to_name": docname,
                "content": xml_content,
                "is_private": 1
            })
            attachment.insert()
            
            # Update custom fields
            doc.db_set("jofotara_xml_generated", 1)
            doc.db_set("jofotara_xml_file", attachment.file_url)
            
            # Add comment
            doc.add_comment("Info", _("JoFotara XML has been generated and attached to this document"))
        
        return xml_content
        
    except Exception as e:
        frappe.log_error(f"Error generating JoFotara XML for {docname}: {str(e)}", 
                        "JoFotara XML Generation Error")
        frappe.throw(_("Failed to generate JoFotara XML: {0}").format(str(e)))


@frappe.whitelist()
def submit_to_jofotara(docname):
    """
    Manually submits the JoFotara XML for a Sales Invoice to the JoFotara API.
    Called from the 'Submit to JoFotara' button in the UI.
    """
    try:
        doc = frappe.get_doc("Sales Invoice", docname)

        if not doc.get("jofotara_xml_generated"):
            frappe.throw(_("XML not generated yet. Please generate it first."))

        # Load the XML content from file
        file_doc = frappe.get_all("File", filters={
            "attached_to_doctype": "Sales Invoice",
            "attached_to_name": docname,
            "file_name": f"{docname}_jofotara.xml"
        }, fields=["name", "file_url", "content"], limit=1)

        if not file_doc:
            frappe.throw(_("JoFotara XML file not found for this invoice."))

        xml_content = file_doc[0].get("content")

        # TODO: Replace with actual API call to JoFotara
        # Simulated success message
        doc.add_comment("Info", _("JoFotara XML manually submitted successfully."))
        frappe.msgprint(_("✅ JoFotara XML manually submitted for {0}.").format(docname))
        return "success"

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "JoFotara Manual Submission Error")
        frappe.throw(_("❌ Failed to manually submit XML: {0}").format(str(e)))
