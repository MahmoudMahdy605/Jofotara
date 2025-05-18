import frappe
import requests
from frappe.utils.password import get_decrypted_password

def send_invoice_to_jofotara(sales_invoice, xml_string):
    """
    Sends the generated XML to the JoFotara API.

    Args:
        sales_invoice (Document): The Sales Invoice document
        xml_string (str): The generated UBL XML string

    Returns:
        dict: Response from JoFotara API
    """
    company = frappe.get_doc("Company", sales_invoice.company)

    if not company.enable_jofotara_integration:
        frappe.throw("JoFotara integration is not enabled for this company.")

    # Read settings
    url = company.jofotara_api_url or company.jofotara_api_endpoint
    token = get_decrypted_password("Company", company.name, "jofotara_api_token", raise_exception=False)

    if not url or not token:
        frappe.throw("JoFotara API URL or API Token is missing.")

    # Prepare headers and payload
    headers = {
        "Content-Type": "application/xml",
        "Authorization": f"Bearer {token.strip()}"
    }

    try:
        response = requests.post(url.strip(), headers=headers, data=xml_string)
        response.raise_for_status()
        return {
            "status": "success",
            "http_status": response.status_code,
            "text": response.text
        }

    except requests.exceptions.RequestException as e:
        frappe.log_error(f"JoFotara API Error: {str(e)}", "JoFotara Submission Failed")
        return {
            "status": "error",
            "error": str(e),
            "http_status": getattr(e.response, 'status_code', None)
        }
