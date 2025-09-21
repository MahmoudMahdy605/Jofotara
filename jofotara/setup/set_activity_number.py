#!/usr/bin/env python3

import frappe

def execute():
    """
    Set the JoFotara activity number for the company
    """
    try:
        # Get the company
        company_name = "Mahmoud Mahdy"
        company = frappe.get_doc("Company", company_name)
        
        print(f"🏢 Configuring JoFotara Activity Number for: {company_name}")
        
        # Check if the custom field exists
        if not hasattr(company, 'jofotara_activity_number'):
            print("⚠️  Custom field 'jofotara_activity_number' not found. Creating it...")
            
            # Create the custom field
            custom_field = frappe.get_doc({
                "doctype": "Custom Field",
                "dt": "Company",
                "fieldname": "jofotara_activity_number",
                "label": "JoFotara Activity Number",
                "fieldtype": "Data",
                "insert_after": "jofotara_secret_key",
                "description": "Activity Serial Number for JoFotara e-invoicing system"
            })
            custom_field.insert()
            frappe.db.commit()
            print("✅ Custom field created successfully")
        
        # Set the activity number - you can change this value
        activity_number = "12604232"  # Correct activity number from JoFotara portal
        
        company.db_set("jofotara_activity_number", activity_number)
        frappe.db.commit()
        
        print(f"✅ Activity Number set to: {activity_number}")
        print(f"📋 Current JoFotara Configuration:")
        print(f"   Integration Enabled: {company.get('enable_jofotara_integration')}")
        print(f"   Client ID: {company.get('jofotara_client_id')}")
        print(f"   Activity Number: {company.get('jofotara_activity_number')}")
        print(f"   API URL: {company.get('jofotara_api_url')}")
        
        print(f"\n💡 To change the activity number, edit this script and run it again.")
        print(f"   Or update it directly in the Company form under JoFotara settings.")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        frappe.log_error(f"JoFotara Activity Number Setup Error: {str(e)}", "JoFotara Setup")

if __name__ == "__main__":
    execute()
