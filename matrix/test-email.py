#!/usr/bin/env python3
"""
Matrix SMTP Email Test Script
Tests the Gmail SMTP configuration for Matrix Synapse password resets
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import argparse
from datetime import datetime

# Configuration from your Matrix setup
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "acebuddyai@gmail.com"
SMTP_PASSWORD = "qcdvtweeiobrkbhf"  # Your Gmail app password
FROM_EMAIL = "Matrix acebuddy.quest <acebuddyai@gmail.com>"

def test_smtp_connection():
    """Test basic SMTP connection and authentication"""
    print("🔍 Testing SMTP connection to Gmail...")

    try:
        # Create SMTP session
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.set_debuglevel(1)  # Enable debug output

        # Enable security
        context = ssl.create_default_context()
        server.starttls(context=context)

        # Login with credentials
        server.login(SMTP_USER, SMTP_PASSWORD)

        print("✅ SMTP connection and authentication successful!")
        server.quit()
        return True

    except Exception as e:
        print(f"❌ SMTP connection failed: {e}")
        return False

def send_test_email(to_email, test_type="connection"):
    """Send a test email to verify the configuration"""
    print(f"📧 Sending test email to {to_email}...")

    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = f"Matrix Homeserver Email Test - {test_type.title()}"
        message["From"] = FROM_EMAIL
        message["To"] = to_email

        # Create the HTML and text content
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        text_content = f"""
Matrix Homeserver Email Test

This is a test email from your Matrix homeserver (acebuddy.quest).

Test Type: {test_type.title()}
Timestamp: {timestamp}
Server: matrix.acebuddy.quest
SMTP Host: {SMTP_HOST}:{SMTP_PORT}

If you received this email, your SMTP configuration is working correctly!

Features being tested:
✅ SMTP connection to Gmail
✅ STARTTLS encryption
✅ Authentication with app password
✅ Email formatting and delivery

Next steps:
- Password reset emails should now work
- Email verification for new accounts is enabled
- Three-PID (email) functionality is active

Matrix homeserver admin panel: https://cinny.acebuddy.quest
        """

        html_content = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background: #667eea; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .success {{ color: #4CAF50; font-weight: bold; }}
        .info {{ background: #f0f9ff; padding: 15px; border-left: 4px solid #007bff; margin: 10px 0; }}
        .footer {{ background: #f8f9fa; padding: 15px; text-align: center; font-size: 0.9em; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏠 Matrix Homeserver Email Test</h1>
        <p>acebuddy.quest</p>
    </div>

    <div class="content">
        <h2>✅ Email Configuration Test Successful!</h2>

        <div class="info">
            <strong>Test Details:</strong><br>
            Type: {test_type.title()}<br>
            Timestamp: {timestamp}<br>
            Server: matrix.acebuddy.quest<br>
            SMTP: {SMTP_HOST}:{SMTP_PORT}
        </div>

        <p>If you received this email, your Matrix homeserver's SMTP configuration is working correctly!</p>

        <h3>🎯 What's Now Working:</h3>
        <ul>
            <li><span class="success">✅</span> Password reset emails</li>
            <li><span class="success">✅</span> Email verification for new accounts</li>
            <li><span class="success">✅</span> STARTTLS encryption</li>
            <li><span class="success">✅</span> Gmail app password authentication</li>
        </ul>

        <h3>🔗 Your Matrix Services:</h3>
        <ul>
            <li><a href="https://cinny.acebuddy.quest">Cinny Web Client</a></li>
            <li><a href="https://matrix.acebuddy.quest">Matrix Server API</a></li>
            <li><a href="https://status.acebuddy.quest">Homelab Status Page</a></li>
        </ul>
    </div>

    <div class="footer">
        <p>Matrix Homeserver at acebuddy.quest<br>
        This is an automated test message from your self-hosted Matrix server.</p>
    </div>
</body>
</html>
        """

        # Attach parts
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        message.attach(part1)
        message.attach(part2)

        # Send email
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SMTP_USER, SMTP_PASSWORD)
            text = message.as_string()
            server.sendmail(FROM_EMAIL, to_email, text)

        print(f"✅ Test email sent successfully to {to_email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send test email: {e}")
        return False

def test_matrix_email_endpoints():
    """Test Matrix-specific email endpoints"""
    print("🔍 Testing Matrix email endpoints...")

    import requests

    try:
        # Test if Matrix server is responding
        response = requests.get("https://matrix.acebuddy.quest/_matrix/client/versions", timeout=10)
        if response.status_code == 200:
            print("✅ Matrix server is responding")
        else:
            print(f"⚠️  Matrix server response: {response.status_code}")

        # Test well-known endpoints
        response = requests.get("https://acebuddy.quest/.well-known/matrix/server", timeout=10)
        if response.status_code == 200:
            print("✅ Matrix well-known server endpoint working")
            print(f"   Response: {response.text}")
        else:
            print(f"⚠️  Well-known server endpoint: {response.status_code}")

        response = requests.get("https://acebuddy.quest/.well-known/matrix/client", timeout=10)
        if response.status_code == 200:
            print("✅ Matrix well-known client endpoint working")
            print(f"   Response: {response.text}")
        else:
            print(f"⚠️  Well-known client endpoint: {response.status_code}")

    except Exception as e:
        print(f"❌ Matrix endpoint test failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="Test Matrix SMTP email configuration")
    parser.add_argument("--email", "-e", help="Email address to send test email to")
    parser.add_argument("--test-type", "-t", default="configuration",
                       choices=["connection", "configuration", "password-reset"],
                       help="Type of test to perform")
    parser.add_argument("--skip-send", "-s", action="store_true",
                       help="Skip sending test email, only test connection")

    args = parser.parse_args()

    print("🏠 Matrix Homeserver Email Configuration Test")
    print("=" * 50)
    print(f"Server: acebuddy.quest")
    print(f"SMTP Host: {SMTP_HOST}:{SMTP_PORT}")
    print(f"From: {FROM_EMAIL}")
    print()

    # Test SMTP connection
    if not test_smtp_connection():
        print("\n❌ SMTP connection test failed. Check your Gmail app password!")
        return 1

    # Test Matrix endpoints
    test_matrix_email_endpoints()

    # Send test email if requested
    if not args.skip_send:
        if args.email:
            if not send_test_email(args.email, args.test_type):
                return 1
        else:
            print("\n💡 To send a test email, use: python test-email.py --email your@email.com")

    print("\n🎉 All tests completed!")
    print("\n📋 Next Steps:")
    print("1. Try password reset at https://cinny.acebuddy.quest")
    print("2. Register a new account with email verification")
    print("3. Check Matrix logs: docker logs -f matrix-synapse | grep -i email")
    print("4. Visit status page: https://status.acebuddy.quest")

    return 0

if __name__ == "__main__":
    sys.exit(main())
