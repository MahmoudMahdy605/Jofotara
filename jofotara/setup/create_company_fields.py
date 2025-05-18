import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def execute():
    """Ensure JoFotara fields are placed in their own tab at the very end of the Company form."""
    try:
        custom_fields = frappe.get_all(
            "Custom Field",
            filters={"dt": "Company", "fieldname": ["like", "%jofotara%"]},
            fields=["name"]
        )
        for field in custom_fields:
            frappe.delete_doc("Custom Field", field.name)
        frappe.db.commit()
        print("🧹 Removed old JoFotara fields.")

    except Exception as e:
        print(f"⚠️ Error cleaning fields: {str(e)}")

    try:
        # Target last known field in the layout
        last_field = "parent_company"

        # Tab Break — at the end
        create_custom_field("Company", {
            "fieldname": "jofotara_tab",
            "label": "JoFotara",
            "fieldtype": "Tab Break",
            "insert_after": last_field
        })

        # Section inside tab
        create_custom_field("Company", {
            "fieldname": "jofotara_settings_section",
            "label": "JoFotara Settings",
            "fieldtype": "Section Break",
            "insert_after": "jofotara_tab",
            "collapsible": 1
        })

        # Fields
        fields = [
            {
                "fieldname": "enable_jofotara_integration",
                "label": "Enable JoFotara Integration",
                "fieldtype": "Check",
                "insert_after": "jofotara_settings_section",
                "default": "0"
            },
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
                "fieldname": "jofotara_column_break",
                "fieldtype": "Column Break",
                "insert_after": "jofotara_device_id"
            },
            {
                "fieldname": "jofotara_api_endpoint",
                "label": "API Endpoint",
                "fieldtype": "Data",
                "insert_after": "jofotara_column_break"
            },
            {
                "fieldname": "jofotara_is_sandbox",
                "label": "Is Sandbox Mode?",
                "fieldtype": "Check",
                "insert_after": "jofotara_api_endpoint"
            },
            {
                "fieldname": "jofotara_api_token",
                "label": "API Token",
                "fieldtype": "Password",
                "insert_after": "jofotara_is_sandbox"
            },
            {
                "fieldname": "jofotara_api_url",
                "label": "API URL (Override)",
                "fieldtype": "Data",
                "insert_after": "jofotara_api_token"
            },
        ]

        for field in fields:
            field["depends_on"] = "eval:doc.enable_jofotara_integration"
            create_custom_field("Company", field)

        frappe.db.commit()
        print("✅ JoFotara tab created successfully at the end.")

    except Exception as e:
        print(f"❌ Failed to create fields: {str(e)}")
