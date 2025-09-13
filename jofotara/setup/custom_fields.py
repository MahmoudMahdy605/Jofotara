import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def create_jofotara_custom_fields():
    """
    Create custom fields for JoFotara integration in the Company DocType.
    This adds a new section with fields for configuring JoFotara integration.
    """
    # Check if the fields already exist
    existing_fields = frappe.get_all("Custom Field", 
                                    filters={"dt": "Company", "fieldname": "jofotara_settings_section"},
                                    fields=["name"])
    
    if existing_fields:
        print("JoFotara custom fields already exist in Company DocType")
        return
    
    custom_fields = {
        "Company": [
            {
                "fieldname": "jofotara_settings_section",
                "label": "JoFotara Settings",
                "fieldtype": "Section Break",
                "insert_after": "default_currency",
                "collapsible": 1,
            },
            {
                "fieldname": "enable_jofotara_integration",
                "label": "Enable JoFotara Integration",
                "fieldtype": "Check",
                "insert_after": "jofotara_settings_section",
                "default": "0",
            },
            {
                "fieldname": "jofotara_client_id",
                "label": "Client ID",
                "fieldtype": "Data",
                "insert_after": "enable_jofotara_integration",
                "depends_on": "eval:doc.enable_jofotara_integration",
            },
            {
                "fieldname": "jofotara_secret_key",
                "label": "Secret Key",
                "fieldtype": "Data",
                "insert_after": "jofotara_client_id",
                "depends_on": "eval:doc.enable_jofotara_integration",
            },
            {
                "fieldname": "jofotara_device_id",
                "label": "Device ID",
                "fieldtype": "Data",
                "insert_after": "jofotara_secret_key",
                "depends_on": "eval:doc.enable_jofotara_integration",
            },
            {
                "fieldname": "jofotara_column_break",
                "fieldtype": "Column Break",
                "insert_after": "jofotara_device_id",
            },
            {
                "fieldname": "jofotara_api_endpoint",
                "label": "API Endpoint",
                "fieldtype": "Data",
                "insert_after": "jofotara_column_break",
                "depends_on": "eval:doc.enable_jofotara_integration",
            },
            {
                "fieldname": "jofotara_is_sandbox",
                "label": "Is Sandbox Mode?",
                "fieldtype": "Check",
                "insert_after": "jofotara_api_endpoint",
                "default": "0",
                "depends_on": "eval:doc.enable_jofotara_integration",
            },
        ]
    }
    
    create_custom_fields(custom_fields)
    frappe.db.commit()
    print("JoFotara custom fields added to Company DocType")
