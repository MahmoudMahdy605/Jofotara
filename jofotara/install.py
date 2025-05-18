import frappe
from frappe.utils import cstr
from jofotara.setup.jofotara_custom_fields import setup_jofotara_custom_fields

def before_install():
    """
    Actions to be performed before installing the JoFotara app.
    """
    pass

def after_install():
    """
    Actions to be performed after installing the JoFotara app.
    This function is called by the Frappe framework when the app is installed.
    """
    try:
        # Setup custom fields
        setup_jofotara_custom_fields()
        
        # Log successful installation
        frappe.logger().info("JoFotara app installed successfully")
        
    except Exception as e:
        frappe.logger().error(f"Error during JoFotara app installation: {cstr(e)}")
        frappe.log_error(f"JoFotara: Installation Error: {cstr(e)}", "JoFotara Installation Error")
