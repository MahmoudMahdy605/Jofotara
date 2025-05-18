"""
Direct fix for JoFotara integration
Run this script from the bench console:

bench --site yoursite.local console

Then copy and paste the following:

import frappe
company_name = frappe.defaults.get_user_default("Company")
if company_name:
    # Enable JoFotara integration
    frappe.db.set_value("Company", company_name, "enable_jofotara_integration", 1)
    # Verify
    value = frappe.db.get_value("Company", company_name, "enable_jofotara_integration")
    print(f"JoFotara integration for {company_name} set to: {value}")
    frappe.db.commit()
    print("Changes committed to database")
else:
    print("No default company found")
"""

import frappe

def direct_fix():
    """
    Directly fix JoFotara integration by setting the enable_jofotara_integration field to 1
    """
    try:
        # Get all companies
        companies = frappe.get_all("Company", fields=["name"])
        
        if not companies:
            print("No companies found")
            return "No companies found"
        
        results = []
        for company_data in companies:
            company_name = company_data.name
            print(f"Processing company: {company_name}")
            
            # Enable JoFotara integration
            frappe.db.set_value("Company", company_name, "enable_jofotara_integration", 1)
            
            # Verify the update
            value = frappe.db.get_value("Company", company_name, "enable_jofotara_integration")
            result = f"JoFotara integration for {company_name} set to: {value}"
            print(result)
            results.append(result)
        
        frappe.db.commit()
        print("Changes committed to database")
        
        return "\n".join(results)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return f"Error: {str(e)}"
