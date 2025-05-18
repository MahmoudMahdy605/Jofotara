import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def execute():
    """
    Create JoFotara custom fields in the Sales Invoice DocType.
    This ensures the XML generation and submission process works properly.
    """
    try:
        fields_to_create = [
            {
                "fieldname": "jofotara_xml_generated",
                "label": "JoFotara XML Generated",
                "fieldtype": "Check",
                "insert_after": "posting_time",
                "default": 0
            },
            {
                "fieldname": "jofotara_xml_file",
                "label": "JoFotara XML File",
                "fieldtype": "Attach",
                "insert_after": "jofotara_xml_generated"
            },
            {
                "fieldname": "jofotara_submission_status",
                "label": "JoFotara Submission Status",
                "fieldtype": "Data",
                "insert_after": "jofotara_xml_file",
                "read_only": 1
            },
            {
                "fieldname": "jofotara_submission_time",
                "label": "JoFotara Submission Time",
                "fieldtype": "Datetime",
                "insert_after": "jofotara_submission_status",
                "read_only": 1
            },
            {
                "fieldname": "jofotara_submission_response",
                "label": "JoFotara Submission Response",
                "fieldtype": "Small Text",
                "insert_after": "jofotara_submission_time",
                "read_only": 1
            }
        ]

        for field in fields_to_create:
            create_custom_field("Sales Invoice", field)

        frappe.db.commit()
        print("✅ JoFotara fields successfully added to Sales Invoice.")
        print("You may now submit invoices and track JoFotara integration status.")
        
    except Exception as e:
        frappe.log_error(str(e), "JoFotara Sales Invoice Field Creation Error")
        print(f"❌ Error creating fields: {str(e)}")
