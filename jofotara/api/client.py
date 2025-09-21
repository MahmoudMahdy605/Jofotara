import frappe
import requests
import base64
from frappe.utils.password import get_decrypted_password

def send_invoice_to_jofotara(sales_invoice, xml_string):
    """
    Sends the generated UBL XML to the JoFotara API in the required format.

    Args:
        sales_invoice (Document): The Sales Invoice document
        xml_string (str): The generated UBL XML string

    Returns:
        dict: Response from JoFotara API
    """
    try:
        company = frappe.get_doc("Company", sales_invoice.company)

        if not company.enable_jofotara_integration:
            frappe.throw("JoFotara integration is not enabled for this company.")

        # Get API config
        url = company.jofotara_api_url or company.jofotara_api_endpoint or "https://backend.jofotara.gov.jo/core/invoices/"
        client_id = company.jofotara_client_id
        
        # Try to get encrypted secret key first, fallback to regular field
        secret_key = get_decrypted_password("Company", company.name, "jofotara_secret_key", raise_exception=False)
        if not secret_key:
            secret_key = company.get("jofotara_secret_key")

        if not client_id or not secret_key:
            frappe.throw("JoFotara Client ID or Secret Key is missing. Please configure them in Company settings.")

        # Encode XML as base64
        xml_bytes = xml_string.encode('utf-8')
        encoded_invoice = base64.b64encode(xml_bytes).decode('utf-8')

        payload = {
            "invoice": encoded_invoice
        }

        headers = {
            "Client-Id": client_id.strip(),
            "Secret-Key": secret_key.strip(),
            "Content-Type": "application/json"
        }

        # Debug output
        print("📤 Sending invoice to JoFotara...")
        print("URL:", url)
        print("Headers:", headers)
        print("Payload (truncated):", encoded_invoice[:100] + "...")  # Show start only

        # Send request
        response = requests.post(url.strip(), json=payload, headers=headers, timeout=15)
        response.raise_for_status()

        # Optionally, extract and save QR code
        response_json = response.json()
        qr_code = response_json.get("EINV_QR")
        if qr_code:
            sales_invoice.db_set("jofotara_qr_code", qr_code)

        return {
            "status": "success",
            "http_status": response.status_code,
            "response": response_json
        }

    except requests.exceptions.RequestException as e:
        frappe.log_error(f"JoFotara API Error: {str(e)}", "JoFotara Submission Failed")
        return {
            "status": "error",
            "error": str(e),
            "http_status": getattr(e.response, 'status_code', None)
        }
