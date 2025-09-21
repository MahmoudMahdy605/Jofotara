import frappe
from jofotara.xml.generator import generate_jofotara_invoice_xml
from jofotara.api.client import send_invoice_to_jofotara

def execute():
    """
    Test JoFotara integration by creating a sample invoice and testing XML generation.
    """
    try:
        print("🧪 Testing JoFotara Integration...")
        
        # Check if we have any existing sales invoices
        invoices = frappe.get_all("Sales Invoice", 
                                filters={"docstatus": 1}, 
                                limit=1, 
                                order_by="creation desc")
        
        if not invoices:
            print("❌ No submitted Sales Invoice found. Please create and submit a Sales Invoice first.")
            return
        
        invoice_name = invoices[0].name
        print(f"📄 Testing with Sales Invoice: {invoice_name}")
        
        # Load the invoice
        invoice = frappe.get_doc("Sales Invoice", invoice_name)
        
        # Test XML generation
        print("🔧 Generating XML...")
        xml_content = generate_jofotara_invoice_xml(invoice)
        
        if xml_content:
            print("✅ XML generated successfully")
            print(f"   XML length: {len(xml_content)} characters")
            
            # Show first few lines of XML
            xml_lines = xml_content.split('\n')[:10]
            print("   XML preview:")
            for line in xml_lines:
                print(f"     {line}")
            
            # Test API submission (dry run)
            print("\n🌐 Testing API submission...")
            try:
                result = send_invoice_to_jofotara(invoice, xml_content)
                
                if result.get("status") == "success":
                    print("✅ API submission successful!")
                    print(f"   HTTP Status: {result.get('http_status')}")
                    response = result.get("response", {})
                    if isinstance(response, dict):
                        print(f"   Response keys: {list(response.keys())}")
                        if "EINV_QR" in response:
                            print(f"   QR Code received: {response['EINV_QR'][:50]}...")
                else:
                    print(f"❌ API submission failed: {result.get('error')}")
                    print(f"   HTTP Status: {result.get('http_status')}")
                    
            except Exception as api_error:
                print(f"❌ API submission error: {str(api_error)}")
        else:
            print("❌ XML generation failed")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        frappe.log_error(f"JoFotara Test Error: {str(e)}", "JoFotara Integration Test")

if __name__ == "__main__":
    execute()
