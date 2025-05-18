import frappe
from frappe.utils import cstr
from jofotara.setup.jofotara_custom_fields import setup_jofotara_custom_fields

def execute():
    """
    Force update JoFotara custom fields in the Company DocType.
    This script uses direct SQL to remove existing fields and then recreates them with the new tab structure.
    """
    try:
        # Use direct SQL to delete existing JoFotara custom fields
        print("Forcefully removing existing JoFotara custom fields...")
        
        # First check if the fields exist
        fields = frappe.db.sql("""
            SELECT name, fieldname FROM `tabCustom Field` 
            WHERE dt = 'Company' AND fieldname LIKE '%jofotara%'
        """, as_dict=1)
        
        if fields:
            print(f"Found {len(fields)} existing JoFotara custom fields:")
            for field in fields:
                print(f"  - {field.fieldname} (ID: {field.name})")
            
            # Delete the fields directly using SQL
            frappe.db.sql("""
                DELETE FROM `tabCustom Field` 
                WHERE dt = 'Company' AND fieldname LIKE '%jofotara%'
            """)
            frappe.db.commit()
            print("Existing fields deleted successfully.")
        else:
            print("No existing JoFotara custom fields found in the database.")
        
        # Also check for fields in the DocType that might not be custom fields
        doctype_fields = frappe.db.sql("""
            SELECT name, fieldname FROM `tabDocField` 
            WHERE parent = 'Company' AND fieldname LIKE '%jofotara%'
        """, as_dict=1)
        
        if doctype_fields:
            print(f"\nFound {len(doctype_fields)} JoFotara fields in DocField table:")
            for field in doctype_fields:
                print(f"  - {field.fieldname} (ID: {field.name})")
            
            # Delete the fields directly using SQL
            frappe.db.sql("""
                DELETE FROM `tabDocField` 
                WHERE parent = 'Company' AND fieldname LIKE '%jofotara%'
            """)
            frappe.db.commit()
            print("DocField entries deleted successfully.")
        else:
            print("No JoFotara fields found in DocField table.")
        
        # Create new JoFotara custom fields with tab structure
        print("\nCreating new JoFotara custom fields with tab structure...")
        setup_jofotara_custom_fields()
        
        # Clear cache to ensure changes take effect
        frappe.clear_cache(doctype="Company")
        
        print("\nJoFotara custom fields have been updated successfully.")
        print("The JoFotara settings are now available in a separate tab in the Company form.")
        print("Please refresh your browser to see the changes.")
        
    except Exception as e:
        print(f"Error updating custom fields: {cstr(e)}")
