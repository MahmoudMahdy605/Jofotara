import frappe
from frappe import _
from jofotara.setup.jofotara_custom_fields import JOFOTARA_CUSTOM_FIELDS

def setup_jofotara():
    """
    Setup JoFotara integration
    
    This function:
    1. Creates all necessary custom fields
    2. Checks if the fields are properly created
    3. Returns a status message
    """
    success_count = 0
    error_count = 0
    messages = []
    
    # Create custom fields for each doctype
    for doctype, fields in JOFOTARA_CUSTOM_FIELDS.items():
        try:
            # Check if the doctype exists
            if not frappe.db.exists("DocType", doctype):
                messages.append(f"DocType {doctype} does not exist")
                error_count += 1
                continue
            
            # Process each field
            for field_dict in fields:
                field_name = field_dict.get("fieldname")
                
                # Check if the field already exists
                existing_field = frappe.db.exists("Custom Field", {
                    "dt": doctype,
                    "fieldname": field_name
                })
                
                if existing_field:
                    # Update existing field
                    custom_field = frappe.get_doc("Custom Field", existing_field)
                    custom_field.update(field_dict)
                    custom_field.save()
                else:
                    # Create new field
                    field_dict.update({
                        "doctype": "Custom Field",
                        "dt": doctype
                    })
                    custom_field = frappe.get_doc(field_dict)
                    custom_field.insert()
                
                success_count += 1
                
        except Exception as e:
            messages.append(f"Error processing {doctype}: {str(e)}")
            error_count += 1
    
    # Verify that all fields were created
    verification_messages = verify_setup()
    messages.extend(verification_messages)
    
    # Return summary
    summary = f"JoFotara setup completed. {success_count} fields processed successfully, {error_count} errors."
    if error_count > 0:
        summary += " Please check the messages for details."
    
    return {
        "status": "Success" if error_count == 0 else "Partial Success" if success_count > 0 else "Failed",
        "summary": summary,
        "messages": messages
    }

def verify_setup():
    """
    Verify that all JoFotara custom fields are properly created
    """
    messages = []
    
    # Check each doctype
    for doctype, fields in JOFOTARA_CUSTOM_FIELDS.items():
        # Check if the doctype exists
        if not frappe.db.exists("DocType", doctype):
            messages.append(f"DocType {doctype} does not exist")
            continue
        
        # Get the doctype metadata
        meta = frappe.get_meta(doctype)
        
        # Check each field
        for field_dict in fields:
            field_name = field_dict.get("fieldname")
            if not meta.has_field(field_name):
                messages.append(f"Field {field_name} is missing in {doctype}")
    
    if not messages:
        messages.append("All JoFotara custom fields are properly created")
    
    return messages

@frappe.whitelist()
def setup_and_verify():
    """
    Setup and verify JoFotara integration (can be called from the UI)
    """
    if not frappe.has_permission("System Manager"):
        frappe.throw(_("You need System Manager permission to run this setup"))
    
    result = setup_jofotara()
    
    # Format messages for display
    message_html = "<ul>"
    for msg in result["messages"]:
        message_html += f"<li>{msg}</li>"
    message_html += "</ul>"
    
    frappe.msgprint(
        title=_("JoFotara Setup Result"),
        msg=f"{result['summary']}<br><br>{message_html}"
    )
    
    return result
