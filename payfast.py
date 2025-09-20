#!/usr/bin/env python3
"""
PayFast Payment Testing Script
Tests credit card and Instant EFT payment methods
"""

import hashlib
import urllib.parse
import requests
from datetime import datetime
import webbrowser

class PayFastTester:
    def __init__(self, merchant_id, merchant_key, sandbox=True):
        self.merchant_id = merchant_id
        self.merchant_key = merchant_key
        self.sandbox = sandbox
        
        # PayFast URLs
        if sandbox:
            self.payfast_host = "sandbox.payfast.co.za"
            self.api_url = "https://api.sandbox.payfast.co.za"
        else:
            self.payfast_host = "www.payfast.co.za"
            self.api_url = "https://api.payfast.co.za"
    
    def generate_signature(self, data_dict):
        """Generate MD5 signature for PayFast"""
        # Create parameter string
        param_string = ""
        for key in sorted(data_dict.keys()):
            param_string += f"{key}={urllib.parse.quote_plus(str(data_dict[key]))}&"
        
        # Remove last ampersand
        param_string = param_string.rstrip("&")
        
        # Add passphrase if not sandbox (leave empty for sandbox)
        if not self.sandbox:
            param_string += "&passphrase=your_passphrase_here"
        
        # Generate MD5 hash
        return hashlib.md5(param_string.encode()).hexdigest()
    
    def create_payment_data(self, amount, item_name, payment_method=None):
        """Create payment data dictionary"""
        # Generate unique transaction ID
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        data = {
            'merchant_id': self.merchant_id,
            'merchant_key': self.merchant_key,
            'return_url': 'https://your-site.com/return',
            'cancel_url': 'https://your-site.com/cancel',
            'notify_url': 'https://your-site.com/notify',
            'name_first': 'John',
            'name_last': 'Doe',
            'email_address': 'test@example.com',
            'cell_number': '0123456789',
            'm_payment_id': f'TEST_{timestamp}',
            'amount': f'{amount:.2f}',
            'item_name': item_name,
            'item_description': f'Test payment for {item_name}',
            'custom_int1': '12345',
            'custom_str1': 'Test Payment'
        }
        
        # Add payment method if specified
        if payment_method:
            data['payment_method'] = payment_method
        
        # Generate signature
        data['signature'] = self.generate_signature(data)
        
        return data
    
    def test_credit_card_payment(self, amount=100.00):
        """Test credit card payment"""
        print("🔥 Testing Credit Card Payment")
        print("=" * 50)
        
        payment_data = self.create_payment_data(
            amount=amount,
            item_name="Credit Card Test Payment",
            payment_method="cc"
        )
        
        # Create payment URL
        payment_url = f"https://{self.payfast_host}/eng/process"
        
        print(f"Payment Amount: R{amount:.2f}")
        print(f"Payment ID: {payment_data['m_payment_id']}")
        print(f"Payment URL: {payment_url}")
        print("\nPayment Data:")
        for key, value in payment_data.items():
            if key != 'signature':
                print(f"  {key}: {value}")
        print(f"  signature: {payment_data['signature']}")
        
        # Create HTML form for testing
        html_form = self.create_payment_form(payment_url, payment_data, "Credit Card Test")
        
        return payment_url, payment_data, html_form
    
    def test_instant_eft_payment(self, amount=100.00):
        """Test Instant EFT payment"""
        print("\n💳 Testing Instant EFT Payment")
        print("=" * 50)
        
        payment_data = self.create_payment_data(
            amount=amount,
            item_name="Instant EFT Test Payment",
            payment_method="eft"
        )
        
        # Create payment URL
        payment_url = f"https://{self.payfast_host}/eng/process"
        
        print(f"Payment Amount: R{amount:.2f}")
        print(f"Payment ID: {payment_data['m_payment_id']}")
        print(f"Payment URL: {payment_url}")
        print("\nPayment Data:")
        for key, value in payment_data.items():
            if key != 'signature':
                print(f"  {key}: {value}")
        print(f"  signature: {payment_data['signature']}")
        
        # Create HTML form for testing
        html_form = self.create_payment_form(payment_url, payment_data, "Instant EFT Test")
        
        return payment_url, payment_data, html_form
    
    def create_payment_form(self, action_url, data, title):
        """Create HTML payment form"""
        form_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{title} - PayFast</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; text-align: center; }}
        .form-group {{ margin-bottom: 15px; }}
        label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
        input[type="text"] {{ width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }}
        .submit-btn {{ background: #007bff; color: white; padding: 15px 30px; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; width: 100%; }}
        .submit-btn:hover {{ background: #0056b3; }}
        .info {{ background: #e3f2fd; padding: 15px; border-radius: 4px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="info">
            <strong>Test Mode:</strong> This is a sandbox payment. No real money will be charged.
        </div>
        <form action="{action_url}" method="post">
"""
        
        # Add form fields
        for key, value in data.items():
            form_html += f'            <input type="hidden" name="{key}" value="{value}">\n'
        
        form_html += """
            <button type="submit" class="submit-btn">Proceed to Payment</button>
        </form>
    </div>
</body>
</html>
"""
        return form_html
    
    def save_test_forms(self, cc_form, eft_form):
        """Save HTML forms to files"""
        with open('payfast_cc_test.html', 'w') as f:
            f.write(cc_form)
        print(f"\n💾 Credit Card test form saved to: payfast_cc_test.html")
        
        with open('payfast_eft_test.html', 'w') as f:
            f.write(eft_form)
        print(f"💾 Instant EFT test form saved to: payfast_eft_test.html")
        
    def test_merchant_status(self):
        """Check merchant account status"""
        print("\n🔍 Checking Merchant Status")
        print("=" * 50)
        
        # This would typically require API credentials and proper authentication
        # For now, just display the merchant info
        print(f"Merchant ID: {self.merchant_id}")
        print(f"Merchant Key: {self.merchant_key}")
        print(f"Environment: {'Sandbox' if self.sandbox else 'Production'}")
        print("Note: Document verification still pending")
        

def main():
    # Your PayFast credentials
    MERCHANT_ID = "31793961"
    MERCHANT_KEY = "kuno3nwljlr52"
    
    # Initialize PayFast tester (sandbox mode)
    pf_tester = PayFastTester(MERCHANT_ID, MERCHANT_KEY, sandbox=True)
    
    print("PayFast Payment Method Tester")
    print("=" * 60)
    
    # Check merchant status
    pf_tester.test_merchant_status()
    
    # Test credit card payment
    cc_url, cc_data, cc_form = pf_tester.test_credit_card_payment(100.00)
    
    # Test instant EFT payment
    eft_url, eft_data, eft_form = pf_tester.test_instant_eft_payment(150.00)
    
    # Save test forms
    pf_tester.save_test_forms(cc_form, eft_form)
    
    print("\n" + "=" * 60)
    print("🎯 TEST INSTRUCTIONS:")
    print("1. Open the generated HTML files in your browser")
    print("2. Click 'Proceed to Payment' to test each method")
    print("3. Use PayFast sandbox test credentials:")
    print("   • Credit Card: 4000000000000002 (expires: any future date)")
    print("   • CVV: 123")
    print("   • Name: Any name")
    print("4. For EFT: Select any test bank and use test credentials")
    print("\n✅ Both forms are ready for testing!")
    print("\n⚠️  Remember: This is sandbox mode - no real payments will be processed")

if __name__ == "__main__":
    main()