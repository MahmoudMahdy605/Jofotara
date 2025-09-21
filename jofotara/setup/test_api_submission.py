import frappe
import base64
import requests
import json

def execute():
    """
    Check JoFotara credentials and test actual API submission.
    """
    try:
        # Get company credentials
        company = frappe.get_doc('Company', 'Mahmoud Mahdy')
        
        print("🔍 JoFotara Configuration:")
        print(f"   Integration Enabled: {company.get('enable_jofotara_integration')}")
        print(f"   Client ID: {company.get('jofotara_client_id')}")
        print(f"   API URL: {company.get('jofotara_api_url')}")
        
        secret_key = company.get('jofotara_secret_key')
        if secret_key:
            print(f"   Secret Key (first 50 chars): {secret_key[:50]}...")
        else:
            print("   Secret Key: Not found")
            
        # Generate corrected XML for ACC-SINV-2025-00009
        try:
            from jofotara.xml.generator import generate_jofotara_invoice_xml
            invoice = frappe.get_doc('Sales Invoice', 'ACC-SINV-2025-00009')
            xml_content = generate_jofotara_invoice_xml(invoice)
            
            # Save corrected XML file
            xml_file_path = "/Users/mahmoudmahdy/Code/Bench/ACC-SINV-2025-00009_corrected.xml"
            with open(xml_file_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            print(f"\n📄 Generated corrected XML: {len(xml_content)} characters")
            print(f"   Saved to: {xml_file_path}")
            
            # Debug invoice amounts
            print(f"\n💰 Invoice Amounts Debug:")
            print(f"   Net Total: {invoice.net_total}")
            print(f"   Total Taxes: {invoice.total_taxes_and_charges or 0}")
            print(f"   Grand Total: {invoice.grand_total}")
            print(f"   Items Total: {sum(item.amount for item in invoice.items)}")
        except Exception as e:
            print(f"❌ Could not generate XML: {str(e)}")
            return
            
        # Prepare API request
        client_id = company.get('jofotara_client_id')
        api_url = company.get('jofotara_api_url') or "https://backend.jofotara.gov.jo/core/invoices/"
        
        if not client_id or not secret_key:
            print("❌ Missing credentials")
            return
            
        # Encode XML as base64
        xml_bytes = xml_content.encode('utf-8')
        encoded_invoice = base64.b64encode(xml_bytes).decode('utf-8')
        
        payload = {
            "invoice": encoded_invoice
        }
        
        headers = {
            "Client-Id": client_id.strip(),
            "Secret-Key": secret_key.strip(),
            "Content-Type": "application/json"
        }
        
        print(f"\n🌐 Testing API submission to: {api_url}")
        print(f"   Client-Id: {client_id}")
        print(f"   Payload size: {len(json.dumps(payload))} bytes")
        
        # Make the request
        try:
            response = requests.post(api_url.strip(), json=payload, headers=headers, timeout=60)
            
            print(f"\n📡 API Response:")
            print(f"   Status Code: {response.status_code}")
            print(f"   Headers: {dict(response.headers)}")
            
            try:
                response_json = response.json()
                print(f"   Response JSON: {json.dumps(response_json, indent=2)}")
                
                if response.status_code == 200 and "EINV_QR" in response_json:
                    print("✅ SUCCESS: Invoice submitted successfully!")
                    print(f"   QR Code: {response_json['EINV_QR'][:100]}...")
                else:
                    print("❌ FAILED: Check response details above")
                    
            except json.JSONDecodeError:
                print(f"   Response Text: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {str(e)}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        frappe.log_error(f"JoFotara API Test Error: {str(e)}", "JoFotara API Test")

if __name__ == "__main__":
    execute()
