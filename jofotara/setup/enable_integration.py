import frappe
from frappe import _
from jofotara.setup.jofotara_custom_fields import JOFOTARA_CUSTOM_FIELDS, setup_jofotara_custom_fields

def enable_jofotara_for_company(company_name):
    """
    Enable JoFotara integration for a specific company
    
    Args:
        company_name (str): Name of the company
        
    Returns:
        dict: Status and message
    """
    try:
        # First, ensure all custom fields are created
        setup_jofotara_custom_fields()
        
        # Check if the company exists
        if not frappe.db.exists("Company", company_name):
            return {
                "status": "Error",
                "message": f"Company '{company_name}' does not exist"
            }
        
        # Get the company
        company = frappe.get_doc("Company", company_name)
        
        # Check if the enable_jofotara_integration field exists
        company_meta = frappe.get_meta("Company")
        if not company_meta.has_field("enable_jofotara_integration"):
            return {
                "status": "Error",
                "message": "JoFotara custom fields are not properly created. Run setup_jofotara_custom_fields() first."
            }
        
        # Enable JoFotara integration
        company.db_set("enable_jofotara_integration", 1)
        
        # Set default values for other fields if they're empty
        if not company.get("jofotara_api_endpoint"):
            company.db_set("jofotara_api_endpoint", "https://api.jofotara.com")
        
        if not company.get("jofotara_is_sandbox"):
            company.db_set("jofotara_is_sandbox", 1)
        
        return {
            "status": "Success",
            "message": f"JoFotara integration enabled for company '{company_name}'"
        }
        
    except Exception as e:
        frappe.log_error(f"Error enabling JoFotara for company {company_name}: {str(e)}", 
                        "JoFotara Integration Error")
        return {
            "status": "Error",
            "message": f"Error enabling JoFotara integration: {str(e)}"
        }

@frappe.whitelist()
def enable_for_current_company():
    """
    Enable JoFotara integration for the current company
    """
    # Get the default company
    default_company = frappe.defaults.get_user_default("Company")
    
    if not default_company:
        frappe.msgprint(_("No default company found. Please select a company first."))
        return
    
    result = enable_jofotara_for_company(default_company)
    
    if result["status"] == "Success":
        frappe.msgprint(_(result["message"]))
    else:
        frappe.msgprint(_(result["message"]), title=_("Error"))
    
    return result

def execute(company=None):
    """
    Command line function to enable JoFotara for a company
    """
    if not company:
        # Get the default company
        company = frappe.defaults.get_user_default("Company")
        
    if not company:
        print("No company specified and no default company found")
        return
    
    result = enable_jofotara_for_company(company)
    print(f"{result['status']}: {result['message']}")
    
    return result
