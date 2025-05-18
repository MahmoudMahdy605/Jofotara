import frappe
from frappe.utils import cstr
from jofotara.setup.jofotara_custom_fields import setup_jofotara_custom_fields

def execute():
    """
    Update JoFotara custom fields in the Company DocType.
    This script removes existing JoFotara fields and recreates them with the new tab structure.
    """
    try:
        # Delete existing JoFotara custom fields
        print("Removing existing JoFotara custom fields...")
        custom_fields = frappe.get_all(
            "Custom Field",
            filters={"dt": "Company", "fieldname": ["like", "%jofotara%"]},
            fields=["name", "fieldname"]
        )
        
        if custom_fields:
            for field in custom_fields:
                print(f"Deleting field: {field.fieldname}")
                frappe.delete_doc("Custom Field", field.name)
            frappe.db.commit()
            print(f"Deleted {len(custom_fields)} existing JoFotara custom fields.")
        else:
            print("No existing JoFotara custom fields found.")
        
        # Create new JoFotara custom fields with tab structure
        print("\nCreating new JoFotara custom fields with tab structure...")
        setup_jofotara_custom_fields()
        
        print("\nJoFotara custom fields have been updated successfully.")
        print("The JoFotara settings are now available in a separate tab in the Company form.")
        print("Please refresh your browser to see the changes.")
        
    except Exception as e:
        print(f"Error updating custom fields: {cstr(e)}")
