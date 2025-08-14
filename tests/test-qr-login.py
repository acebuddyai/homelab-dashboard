#!/usr/bin/env python3
"""
Test script to verify QR Code login setup for Matrix with MAS
Tests the integration between Synapse, MAS, and QR code login capabilities
"""

import json
import sys
import requests
from urllib.parse import urljoin
from typing import Dict, Tuple, List

# Configuration
MATRIX_DOMAIN = "acebuddy.quest"
MATRIX_URL = f"https://matrix.{MATRIX_DOMAIN}"
AUTH_URL = f"https://auth.{MATRIX_DOMAIN}"
CINNY_URL = f"https://cinny.{MATRIX_DOMAIN}"

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{title:^60}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def check_endpoint(url: str, expected_status: int = 200, description: str = "") -> Tuple[bool, str]:
    """Check if an endpoint is accessible"""
    try:
        response = requests.get(url, timeout=5, allow_redirects=False)
        if response.status_code == expected_status:
            return True, f"{GREEN}✓{RESET} {description or url}"
        else:
            return False, f"{RED}✗{RESET} {description or url} (Status: {response.status_code})"
    except requests.exceptions.RequestException as e:
        return False, f"{RED}✗{RESET} {description or url} (Error: {str(e)})"

def check_json_endpoint(url: str, required_fields: List[str] = None, description: str = "") -> Tuple[bool, str]:
    """Check if a JSON endpoint returns expected data"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return False, f"{RED}✗{RESET} {description or url} (Status: {response.status_code})"

        data = response.json()
        if required_fields:
            missing = [field for field in required_fields if field not in data]
            if missing:
                return False, f"{YELLOW}⚠{RESET} {description or url} (Missing fields: {', '.join(missing)})"

        return True, f"{GREEN}✓{RESET} {description or url}"
    except requests.exceptions.JSONDecodeError:
        return False, f"{RED}✗{RESET} {description or url} (Invalid JSON)"
    except requests.exceptions.RequestException as e:
        return False, f"{RED}✗{RESET} {description or url} (Error: {str(e)})"

def test_basic_connectivity():
    """Test basic service connectivity"""
    print_header("Basic Service Connectivity")

    tests = [
        (CINNY_URL, 200, "Cinny Web Client"),
        (MATRIX_URL + "/_matrix/client/versions", 200, "Matrix Client API"),
        (AUTH_URL, 200, "MAS Authentication Service"),
        (f"{MATRIX_URL}/.well-known/matrix/client", 200, "Matrix Well-known Client"),
        (f"{MATRIX_URL}/.well-known/matrix/server", 200, "Matrix Well-known Server"),
    ]

    results = []
    for url, expected_status, desc in tests:
        success, message = check_endpoint(url, expected_status, desc)
        print(message)
        results.append(success)

    return all(results)

def test_mas_oidc_configuration():
    """Test MAS OIDC configuration"""
    print_header("MAS OIDC Configuration")

    oidc_url = f"{AUTH_URL}/.well-known/openid-configuration"
    required_fields = [
        "issuer",
        "authorization_endpoint",
        "token_endpoint",
        "jwks_uri",
        "registration_endpoint",
        "scopes_supported",
        "response_types_supported"
    ]

    success, message = check_json_endpoint(oidc_url, required_fields, "OpenID Configuration")
    print(message)

    if success:
        try:
            response = requests.get(oidc_url, timeout=5)
            config = response.json()
            print(f"\n  Issuer: {config.get('issuer')}")
            print(f"  Authorization: {config.get('authorization_endpoint')}")
            print(f"  Token: {config.get('token_endpoint')}")
            print(f"  Scopes: {', '.join(config.get('scopes_supported', []))}")
        except:
            pass

    return success

def test_matrix_authentication_mode():
    """Test if Matrix is properly configured for MSC3861"""
    print_header("Matrix MSC3861 Configuration")

    # When MSC3861 is enabled, traditional login endpoints should not work
    legacy_login_url = f"{MATRIX_URL}/_matrix/client/r0/login"

    try:
        response = requests.get(legacy_login_url, timeout=5)
        if response.status_code == 404 or "M_UNRECOGNIZED" in response.text:
            print(f"{GREEN}✓{RESET} MSC3861 Mode Active (Legacy login disabled)")
            msc3861_active = True
        else:
            print(f"{YELLOW}⚠{RESET} Legacy login still active (MSC3861 might not be properly configured)")
            msc3861_active = False
    except:
        print(f"{RED}✗{RESET} Could not verify MSC3861 status")
        msc3861_active = False

    # Check if client well-known points to the correct homeserver
    try:
        response = requests.get(f"{MATRIX_URL}/.well-known/matrix/client", timeout=5)
        data = response.json()
        homeserver_url = data.get("m.homeserver", {}).get("base_url")

        if homeserver_url == MATRIX_URL:
            print(f"{GREEN}✓{RESET} Client well-known configured correctly")
        else:
            print(f"{YELLOW}⚠{RESET} Client well-known points to: {homeserver_url}")

        # Check for authentication configuration in well-known
        if "org.matrix.msc3861" in data:
            auth_config = data["org.matrix.msc3861"]
            print(f"{GREEN}✓{RESET} MSC3861 authentication configured in well-known")
            print(f"  Issuer: {auth_config.get('issuer')}")
        elif "m.authentication" in data:
            auth_config = data["m.authentication"]
            print(f"{GREEN}✓{RESET} Authentication service configured in well-known")
            print(f"  Issuer: {auth_config.get('issuer')}")
    except Exception as e:
        print(f"{RED}✗{RESET} Error checking well-known configuration: {e}")

    return msc3861_active

def test_qr_login_endpoints():
    """Test QR code login specific endpoints"""
    print_header("QR Code Login Endpoints")

    # QR login might be at different paths depending on MAS version
    qr_endpoints = [
        f"{AUTH_URL}/login/qr",
        f"{AUTH_URL}/qr",
        f"{AUTH_URL}/api/qr-login",
        f"{AUTH_URL}/oauth2/qr"
    ]

    found_qr = False
    for endpoint in qr_endpoints:
        try:
            response = requests.get(endpoint, timeout=5, allow_redirects=False)
            if response.status_code in [200, 302, 401]:  # 401 might mean it exists but needs auth
                print(f"{GREEN}✓{RESET} Potential QR endpoint found: {endpoint} (Status: {response.status_code})")
                found_qr = True
                break
            else:
                print(f"{YELLOW}·{RESET} Checked: {endpoint} (Status: {response.status_code})")
        except:
            print(f"{YELLOW}·{RESET} Checked: {endpoint} (Connection error)")

    if not found_qr:
        print(f"\n{YELLOW}Note:{RESET} QR login endpoints not found at expected paths.")
        print("This might be normal - QR login might be integrated into the main login flow.")

    return found_qr

def test_synapse_health():
    """Test Synapse server health"""
    print_header("Synapse Server Health")

    health_url = f"{MATRIX_URL}/health"
    success, message = check_endpoint(health_url, 200, "Synapse Health Check")
    print(message)

    # Check version endpoint
    versions_url = f"{MATRIX_URL}/_matrix/client/versions"
    try:
        response = requests.get(versions_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            versions = data.get("versions", [])
            unstable_features = data.get("unstable_features", {})

            print(f"{GREEN}✓{RESET} Matrix versions endpoint working")
            print(f"  Supported versions: {', '.join(versions[:3])}...")

            # Check for MSC4108 support
            if "org.matrix.msc4108" in unstable_features:
                if unstable_features["org.matrix.msc4108"]:
                    print(f"{GREEN}✓{RESET} MSC4108 (QR Login) support detected")
                else:
                    print(f"{YELLOW}⚠{RESET} MSC4108 (QR Login) present but disabled")
            else:
                print(f"{YELLOW}⚠{RESET} MSC4108 (QR Login) not in unstable features")
    except:
        pass

    return success

def main():
    """Run all tests"""
    print(f"\n{BLUE}Matrix QR Code Login Setup Test{RESET}")
    print(f"Testing domain: {MATRIX_DOMAIN}")
    print(f"Matrix URL: {MATRIX_URL}")
    print(f"Auth URL: {AUTH_URL}")

    all_tests_passed = True

    # Run tests
    if not test_basic_connectivity():
        all_tests_passed = False

    if not test_mas_oidc_configuration():
        all_tests_passed = False

    if not test_matrix_authentication_mode():
        all_tests_passed = False

    test_qr_login_endpoints()  # This is informational

    if not test_synapse_health():
        all_tests_passed = False

    # Summary
    print_header("Test Summary")

    if all_tests_passed:
        print(f"{GREEN}✓ Core services are properly configured{RESET}")
        print(f"\n{BLUE}Next Steps:{RESET}")
        print("1. Test login at https://cinny.acebuddy.quest")
        print("2. Try logging in with a Matrix client that supports QR codes")
        print("3. Check if existing sessions need to be re-authenticated")
        print("\nNote: QR code login requires client support. Not all Matrix clients")
        print("support MSC4108 yet. Element X and newer Element versions should work.")
    else:
        print(f"{YELLOW}⚠ Some tests failed or returned warnings{RESET}")
        print("\nTroubleshooting:")
        print("1. Check docker logs: docker logs matrix-synapse")
        print("2. Check MAS logs: docker logs matrix-auth-service")
        print("3. Verify all containers are running: docker ps")

    print(f"\n{BLUE}Documentation:{RESET}")
    print("- MSC3861: https://github.com/matrix-org/matrix-spec-proposals/pull/3861")
    print("- MSC4108: https://github.com/matrix-org/matrix-spec-proposals/pull/4108")
    print("- MAS Docs: https://element-hq.github.io/matrix-authentication-service/")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Unexpected error: {e}{RESET}")
        sys.exit(1)
