import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field
from frappe.utils import cstr

# Dictionary of all custom fields to be created by the JoFotara app
JOFOTARA_CUSTOM_FIELDS = {
    "Company": [
        {
            "fieldname": "jofotara_tab",
            "label": "JoFotara",
            "fieldtype": "Tab Break",
            "insert_after": "default_operating_cost_account"
        },
        {
            "fieldname": "jofotara_settings_section",
            "label": "JoFotara Settings",
            "fieldtype": "Section Break",
            "insert_after": "jofotara_tab"
        },
        {
            "fieldname": "enable_jofotara_integration",
            "label": "Enable JoFotara Integration",
            "fieldtype": "Check",
            "insert_after": "jofotara_settings_section",
            "default": "0"
        },
        {
            "fieldname": "jofotara_client_id",
            "label": "Client ID",
            "fieldtype": "Data",
            "insert_after": "enable_jofotara_integration",
            "depends_on": "eval:doc.enable_jofotara_integration"
        },
        {
            "fieldname": "jofotara_secret_key",
            "label": "Secret Key",
            "fieldtype": "Data",
            "insert_after": "jofotara_client_id",
            "depends_on": "eval:doc.enable_jofotara_integration"
        },
        {
            "fieldname": "jofotara_device_id",
            "label": "Device ID",
            "fieldtype": "Data",
            "insert_after": "jofotara_secret_key",
            "depends_on": "eval:doc.enable_jofotara_integration"
        },
        {
            "fieldname": "jofotara_column_break",
            "fieldtype": "Column Break",
            "insert_after": "jofotara_device_id"
        },
        {
            "fieldname": "jofotara_api_endpoint",
            "label": "API Endpoint",
            "fieldtype": "Data",
            "insert_after": "jofotara_column_break",
            "depends_on": "eval:doc.enable_jofotara_integration"
        },
        {
            "fieldname": "jofotara_is_sandbox",
            "label": "Is Sandbox Mode?",
            "fieldtype": "Check",
            "insert_after": "jofotara_api_endpoint",
            "default": "0",
            "depends_on": "eval:doc.enable_jofotara_integration"
        }
    ],
    "Sales Invoice": [
        {
            "fieldname": "jofotara_section",
            "label": "JoFotara E-Invoicing",
            "fieldtype": "Section Break",
            "insert_after": "against_income_account",
            "collapsible": 1
        },
        {
            "fieldname": "jofotara_xml_generated",
            "label": "JoFotara XML Generated",
            "fieldtype": "Check",
            "insert_after": "jofotara_section",
            "read_only": 1,
            "no_copy": 1,
            "print_hide": 1
        },
        {
            "fieldname": "jofotara_xml_file",
            "label": "JoFotara XML File",
            "fieldtype": "Attach",
            "insert_after": "jofotara_xml_generated",
            "read_only": 1,
            "no_copy": 1,
            "print_hide": 1
        },
        {
            "fieldname": "jofotara_submission_status",
            "label": "JoFotara Submission Status",
            "fieldtype": "Select",
            "insert_after": "jofotara_xml_file",
            "options": "\nPending\nSubmitted\nAccepted\nRejected",
            "read_only": 1,
            "no_copy": 1,
            "print_hide": 1
        },
        {
            "fieldname": "jofotara_submission_date",
            "label": "JoFotara Submission Date",
            "fieldtype": "Datetime",
            "insert_after": "jofotara_submission_status",
            "read_only": 1,
            "no_copy": 1,
            "print_hide": 1
        }
    ]
}

def setup_jofotara_custom_fields():
    """
    Add JoFotara custom fields to the Company DocType.
    This is the recommended way to add custom fields to standard DocTypes.
    """
    try:
        # Create custom fields for each DocType
        for doctype, fields in JOFOTARA_CUSTOM_FIELDS.items():
            for field in fields:
                try:
                    create_custom_field(doctype, field)
                    print(f"Created custom field: {field['fieldname']}")
                except Exception as e:
                    if "already exists" in str(e):
                        print(f"Field {field['fieldname']} already exists")
                    else:
                        print(f"Error creating {field['fieldname']}: {str(e)}")
        
        # Commit changes to database
        frappe.db.commit()
        print("\nJoFotara custom fields have been added successfully.")
        
    except Exception as e:
        print(f"Error setting up custom fields: {cstr(e)}")
        frappe.log_error(f"JoFotara: Error setting up custom fields: {cstr(e)}", "JoFotara Setup Error")

def execute():
    """
    Execute this function to add JoFotara custom fields to the Company DocType.
    """
    setup_jofotara_custom_fields()
    frappe.db.commit()
    print("\nJoFotara custom fields have been added to the Company DocType.")
    print("Please refresh your browser to see the changes.")
