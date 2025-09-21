import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def execute():
    """
    Create or refresh JoFotara custom fields in the Sales Invoice DocType.
    Ensures fields are added in correct order and cleaned up if needed.
    """
    try:
        # Clean up old fields if they exist
        custom_fields = frappe.get_all(
            "Custom Field",
            filters={"dt": "Sales Invoice", "fieldname": ["like", "jofotara%"]},
            fields=["name"]
        )
        for field in custom_fields:
            frappe.delete_doc("Custom Field", field.name)

        frappe.db.commit()
        print("🧹 Old JoFotara fields removed from Sales Invoice.")

        # Define fields
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
            },
            {
                "fieldname": "jofotara_invoice_type_label",
                "label": "JoFotara Invoice Type",
                "fieldtype": "Read Only",
                "insert_after": "jofotara_submission_response",
                "read_only": 1
            },
            {
                "fieldname": "jofotara_qr_code",
                "label": "JoFotara QR Code",
                "fieldtype": "Long Text",
                "insert_after": "jofotara_invoice_type_label",
                "read_only": 1
            }
        ]

        # Create fields
        for field in fields_to_create:
            create_custom_field("Sales Invoice", field)

        frappe.db.commit()
        print("✅ JoFotara fields successfully added to Sales Invoice.")

    except Exception as e:
        frappe.log_error(str(e), "JoFotara Sales Invoice Field Creation Error")
        print(f"❌ Error creating JoFotara fields: {str(e)}")
