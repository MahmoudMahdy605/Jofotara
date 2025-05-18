import frappe
import requests
from frappe import _
from frappe.utils import now
from frappe.utils.file_manager import get_file
from frappe.utils.password import get_decrypted_password


@frappe.whitelist()  # <-- ADD THIS TO MAKE IT CALLABLE FROM JS
def submit_to_jofotara(docname):
    """
    Submit XML of Sales Invoice to JoFotara API.

    Args:
        docname (str): Name of the Sales Invoice to submit

    Returns:
        str: Response from JoFotara API or error message
    """
    doc = frappe.get_doc("Sales Invoice", docname)

    if not doc.jofotara_xml_file:
        frappe.throw(_("No XML file found to submit."))

    file_doc = frappe.get_doc("File", {"file_url": doc.jofotara_xml_file})
    file_content = get_file(file_doc.file_url)[1]

    company = frappe.get_doc("Company", doc.company)
    endpoint = company.get("jofotara_api_url")
    token = get_decrypted_password("Company", company.name, "jofotara_api_token", raise_exception=False)

    if not endpoint or not token:
        frappe.throw(_("JoFotara API URL or Token not configured."))

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/xml"
    }

    try:
        response = requests.post(endpoint, data=file_content, headers=headers, timeout=10)

        doc.db_set("jofotara_submission_status", "Success" if response.status_code == 200 else "Failed")
        doc.db_set("jofotara_submission_time", now())
        doc.db_set("jofotara_submission_response", response.text[:2000])  # limit long responses

        frappe.msgprint(_("✅ JoFotara submission complete: Status Code {0}").format(response.status_code))

        return "success" if response.status_code == 200 else f"Error: {response.text[:200]}"

    except Exception as e:
        error = f"Submission failed: {str(e)}"
        doc.db_set("jofotara_submission_status", "Error")
        doc.db_set("jofotara_submission_response", error)
        frappe.log_error(error, "JoFotara Submission Error")
        frappe.msgprint(_("❌ JoFotara submission failed. See error log."))
        return error
