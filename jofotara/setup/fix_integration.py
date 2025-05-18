import frappe
from frappe import _
import json

def fix_jofotara_integration():
    """
    Fix JoFotara integration by directly updating the database
    """
    try:
        # Get all companies
        companies = frappe.get_all("Company", fields=["name"])
        
        if not companies:
            print("No companies found")
            return
        
        for company_data in companies:
            company_name = company_data.name
            print(f"Processing company: {company_name}")
            
            # Check if custom field exists in the database
            custom_field = frappe.db.get_value(
                "Custom Field", 
                {"dt": "Company", "fieldname": "enable_jofotara_integration"},
                ["name", "fieldname", "fieldtype", "insert_after", "label", "options"],
                as_dict=1
            )
            
            if not custom_field:
                print("Creating enable_jofotara_integration custom field...")
                # Create the custom field
                cf = frappe.get_doc({
                    "doctype": "Custom Field",
                    "dt": "Company",
                    "fieldname": "enable_jofotara_integration",
                    "fieldtype": "Check",
                    "label": "Enable JoFotara Integration",
                    "insert_after": "jofotara_settings_section",
                    "default": "0"
                })
                cf.insert(ignore_permissions=True)
                print("Custom field created")
            else:
                print(f"Custom field already exists: {json.dumps(custom_field)}")
            
            # Directly update the database
            print(f"Enabling JoFotara integration for {company_name}")
            frappe.db.set_value("Company", company_name, "enable_jofotara_integration", 1)
            
            # Verify the update
            value = frappe.db.get_value("Company", company_name, "enable_jofotara_integration")
            print(f"Verification - enable_jofotara_integration for {company_name}: {value}")
            
            # Create other required fields if they don't exist
            required_fields = [
                {
                    "fieldname": "jofotara_client_id",
                    "label": "Client ID",
                    "fieldtype": "Data",
                    "insert_after": "enable_jofotara_integration"
                },
                {
                    "fieldname": "jofotara_secret_key",
                    "label": "Secret Key",
                    "fieldtype": "Password",
                    "insert_after": "jofotara_client_id"
                },
                {
                    "fieldname": "jofotara_device_id",
                    "label": "Device ID",
                    "fieldtype": "Data",
                    "insert_after": "jofotara_secret_key"
                },
                {
                    "fieldname": "jofotara_api_endpoint",
                    "label": "API Endpoint",
                    "fieldtype": "Data",
                    "insert_after": "jofotara_device_id"
                },
                {
                    "fieldname": "jofotara_is_sandbox",
                    "label": "Is Sandbox Mode?",
                    "fieldtype": "Check",
                    "insert_after": "jofotara_api_endpoint",
                    "default": "1"
                }
            ]
            
            for field in required_fields:
                exists = frappe.db.get_value(
                    "Custom Field", 
                    {"dt": "Company", "fieldname": field["fieldname"]},
                    "name"
                )
                
                if not exists:
                    print(f"Creating {field['fieldname']} custom field...")
                    field_doc = frappe.get_doc({
                        "doctype": "Custom Field",
                        "dt": "Company",
                        **field
                    })
                    field_doc.insert(ignore_permissions=True)
                
                # Set default values
                if field["fieldname"] == "jofotara_api_endpoint":
                    frappe.db.set_value("Company", company_name, field["fieldname"], "https://api.jofotara.com")
                elif field["fieldname"] == "jofotara_is_sandbox":
                    frappe.db.set_value("Company", company_name, field["fieldname"], 1)
                elif field["fieldname"] == "jofotara_client_id" and not frappe.db.get_value("Company", company_name, field["fieldname"]):
                    frappe.db.set_value("Company", company_name, field["fieldname"], "test_client_id")
                elif field["fieldname"] == "jofotara_secret_key" and not frappe.db.get_value("Company", company_name, field["fieldname"]):
                    frappe.db.set_value("Company", company_name, field["fieldname"], "test_secret_key")
                elif field["fieldname"] == "jofotara_device_id" and not frappe.db.get_value("Company", company_name, field["fieldname"]):
                    frappe.db.set_value("Company", company_name, field["fieldname"], "test_device_id")
            
            print(f"JoFotara integration enabled for {company_name}")
        
        frappe.db.commit()
        print("Database committed. JoFotara integration has been enabled for all companies.")
        
        return "JoFotara integration enabled successfully"
        
    except Exception as e:
        print(f"Error: {str(e)}")
        frappe.log_error(f"Error fixing JoFotara integration: {str(e)}", "JoFotara Integration Fix Error")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    fix_jofotara_integration()
