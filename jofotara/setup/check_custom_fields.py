import frappe
from frappe.utils import cstr

def execute():
    """
    Check the current state of JoFotara fields in the Company DocType.
    This will help diagnose why the fields aren't showing up in the interface.
    """
    try:
        # Check for custom fields
        custom_fields = frappe.get_all(
            "Custom Field",
            filters={"dt": "Company", "fieldname": ["like", "%jofotara%"]},
            fields=["name", "fieldname", "label", "fieldtype", "insert_after"]
        )
        
        if custom_fields:
            print(f"Found {len(custom_fields)} JoFotara custom fields in Company DocType:")
            for field in custom_fields:
                print(f"  - {field.fieldname} ({field.fieldtype}): {field.label}")
        else:
            print("No JoFotara custom fields found in Custom Field table.")
            
        # Check for standard fields in DocType
        doctype_fields = frappe.get_all(
            "DocField",
            filters={"parent": "Company", "fieldname": ["like", "%jofotara%"]},
            fields=["name", "fieldname", "label", "fieldtype", "insert_after"]
        )
        
        if doctype_fields:
            print(f"\nFound {len(doctype_fields)} JoFotara standard fields in Company DocType:")
            for field in doctype_fields:
                print(f"  - {field.fieldname} ({field.fieldtype}): {field.label}")
        else:
            print("\nNo JoFotara standard fields found in DocField table.")
        
        # Check if the fields are in the Company DocType JSON
        company_doctype = frappe.get_doc("DocType", "Company")
        jofotara_fields = [f for f in company_doctype.fields if "jofotara" in (f.fieldname or "")]
        
        if jofotara_fields:
            print(f"\nFound {len(jofotara_fields)} JoFotara fields in Company DocType object:")
            for field in jofotara_fields:
                print(f"  - {field.fieldname} ({field.fieldtype}): {field.label}")
        else:
            print("\nNo JoFotara fields found in Company DocType object.")
            
        # Check field order
        field_order = company_doctype.field_order
        jofotara_in_order = [f for f in field_order if "jofotara" in f]
        
        if jofotara_in_order:
            print(f"\nJoFotara fields in field_order: {', '.join(jofotara_in_order)}")
        else:
            print("\nNo JoFotara fields found in field_order.")
            
    except Exception as e:
        print(f"Error while checking custom fields: {cstr(e)}")
