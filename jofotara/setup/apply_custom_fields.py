import frappe
from frappe.utils import cstr
from jofotara.setup.custom_fields import create_jofotara_custom_fields

def execute():
    """
    Execute this script to apply JoFotara custom fields to the Company DocType.
    Run this from the Frappe bench using:
    bench execute jofotara.setup.apply_custom_fields.execute
    """
    try:
        create_jofotara_custom_fields()
        print("JoFotara custom fields have been successfully added to the Company DocType.")
        print("Please refresh your browser to see the changes.")
    except Exception as e:
        print(f"Error while creating custom fields: {cstr(e)}")
