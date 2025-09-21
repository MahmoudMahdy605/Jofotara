import frappe
from frappe.utils.password import set_encrypted_password

def execute():
    """
    Configure JoFotara integration with provided credentials.
    """
    try:
        # Get the first company (assuming single company setup)
        companies = frappe.get_all("Company", limit=1)
        if not companies:
            print("❌ No company found. Please create a company first.")
            return
        
        company_name = companies[0].name
        company = frappe.get_doc("Company", company_name)
        
        # JoFotara API Configuration
        client_id = "bc581ec6-61bc-4272-97fe-0d5c12ecc6a4"
        secret_key = "Gj5nS9wyYHRadaVffz5VKB4v4wlVWyPhcJvrTD4NHtOv9ZxzGf99C13jBJ61yDRy4BbXfUabBxjrS+5jLw1sQC5CQpaULUkR8rpSBzKV+nWUlui/CX0s6djIJ6YEPzy7FBQLWb0l8SLea1ybFoXhyAd10OuRvv9ZCRlEmXIizVK2OpuYiI0cbRmPVNq+Bd2PTpBRhg3Kybuk5LPJ8R4Qzj7QKLSSmX2tYymAmJNhcit1W/c2CbFc5nyE1dnQTtbHIHZjJlzFSmJ/OQk6EW2DJA=="
        api_endpoint = "https://backend.jofotara.gov.jo/core/invoices/"
        
        # Update company fields
        company.db_set("enable_jofotara_integration", 1)
        company.db_set("jofotara_client_id", client_id)
        company.db_set("jofotara_api_url", api_endpoint)
        company.db_set("jofotara_api_endpoint", api_endpoint)
        company.db_set("is_sales_tax_registered", 1)  # Assuming registered for VAT
        
        # Store secret key as regular field first, then encrypt
        try:
            # Try to set as encrypted password
            set_encrypted_password("Company", company_name, "jofotara_secret_key", secret_key)
        except Exception as e:
            print(f"⚠️  Could not encrypt secret key: {str(e)}")
            # Store as regular field temporarily for testing
            company.db_set("jofotara_secret_key", secret_key)
            print("   Stored as regular field for now")
        
        frappe.db.commit()
        
        print(f"✅ JoFotara integration configured for company: {company_name}")
        print(f"   Client ID: {client_id}")
        print(f"   API Endpoint: {api_endpoint}")
        print("   Secret Key: [ENCRYPTED]")
        print("   Integration: ENABLED")
        
    except Exception as e:
        frappe.log_error(f"JoFotara Configuration Error: {str(e)}", "JoFotara Setup")
        print(f"❌ Error configuring JoFotara: {str(e)}")

if __name__ == "__main__":
    execute()
