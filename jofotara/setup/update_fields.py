import frappe
from frappe import _
from jofotara.setup.jofotara_custom_fields import JOFOTARA_CUSTOM_FIELDS

def execute():
    """
    Force update JoFotara custom fields for all doctypes
    """
    frappe.log_error("Starting JoFotara custom fields update", "JoFotara Setup")
    
    # Update custom fields for each doctype
    for doctype, fields in JOFOTARA_CUSTOM_FIELDS.items():
        frappe.log_error(f"Processing DocType: {doctype}", "JoFotara Setup")
        
        # Check if the doctype exists
        if not frappe.db.exists("DocType", doctype):
            frappe.log_error(f"DocType {doctype} does not exist", "JoFotara Setup")
            continue
        
        # Process each field
        for field_dict in fields:
            field_name = field_dict.get("fieldname")
            
            # Check if the field already exists
            existing_field = frappe.db.exists("Custom Field", {
                "dt": doctype,
                "fieldname": field_name
            })
            
            if existing_field:
                # Update existing field
                frappe.log_error(f"Updating existing field: {field_name} in {doctype}", "JoFotara Setup")
                custom_field = frappe.get_doc("Custom Field", existing_field)
                custom_field.update(field_dict)
                custom_field.save()
            else:
                # Create new field
                frappe.log_error(f"Creating new field: {field_name} in {doctype}", "JoFotara Setup")
                field_dict.update({
                    "doctype": "Custom Field",
                    "dt": doctype
                })
                custom_field = frappe.get_doc(field_dict)
                custom_field.insert()
    
    frappe.log_error("Completed JoFotara custom fields update", "JoFotara Setup")
    return "JoFotara custom fields updated successfully"

if __name__ == "__main__":
    execute()
