#!/usr/bin/env python3
"""
Basic verification script for Matrix bot server monitoring features
"""

import os
import sys

def check_file_exists(filepath, description):
    """Check if a file exists and report status"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - NOT FOUND")
        return False

def check_file_contains(filepath, search_terms, description):
    """Check if file contains specific terms"""
    if not os.path.exists(filepath):
        print(f"❌ {description}: {filepath} - FILE NOT FOUND")
        return False

    try:
        with open(filepath, 'r') as f:
            content = f.read()

        found_terms = []
        missing_terms = []

        for term in search_terms:
            if term in content:
                found_terms.append(term)
            else:
                missing_terms.append(term)

        if missing_terms:
            print(f"⚠️  {description}: Missing terms - {missing_terms}")
            return False
        else:
            print(f"✅ {description}: All required terms found")
            return True

    except Exception as e:
        print(f"❌ {description}: Error reading file - {e}")
        return False

def main():
    """Main verification function"""
    print("🔍 Matrix Bot Server Monitoring Verification")
    print("=" * 50)

    bot_dir = "matrix/bot"
    all_checks_passed = True

    # Check core files exist
    print("\n📁 Checking core files...")
    files_to_check = [
        (f"{bot_dir}/enhanced_bot.py", "Enhanced bot file"),
        (f"{bot_dir}/requirements.txt", "Requirements file"),
        (f"{bot_dir}/Dockerfile", "Dockerfile"),
        (f"{bot_dir}/test_monitoring.py", "Test monitoring script")
    ]

    for filepath, description in files_to_check:
        if not check_file_exists(filepath, description):
            all_checks_passed = False

    # Check requirements.txt has new dependencies
    print("\n📦 Checking dependencies...")
    required_deps = ["psutil", "GPUtil"]
    if not check_file_contains(f"{bot_dir}/requirements.txt", required_deps, "Server monitoring dependencies"):
        all_checks_passed = False

    # Check enhanced_bot.py has monitoring functions
    print("\n🤖 Checking bot monitoring features...")
    monitoring_features = [
        "get_server_stats",
        "format_bytes",
        "!bot server",
        "!bot cpu",
        "!bot memory",
        "!bot disk",
        "!bot network",
        "!bot temp",
        "!bot gpu",
        "psutil",
        "CPU Information",
        "Memory Information",
        "Temperature Sensors"
    ]

    if not check_file_contains(f"{bot_dir}/enhanced_bot.py", monitoring_features, "Bot monitoring features"):
        all_checks_passed = False

    # Check help menu is updated
    print("\n📋 Checking help menu...")
    help_features = [
        "!bot server - Server system stats",
        "!bot cpu - CPU information",
        "!bot memory - Memory usage",
        "!bot disk - Disk usage",
        "!bot network - Network statistics",
        "!bot temp - Temperature sensors",
        "!bot gpu - GPU information"
    ]

    if not check_file_contains(f"{bot_dir}/enhanced_bot.py", help_features, "Updated help menu"):
        all_checks_passed = False

    # Summary
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("✅ All verification checks PASSED!")
        print("\n🚀 Next steps:")
        print("1. Build and run the Docker container:")
        print("   cd matrix && docker-compose up --build -d matrix-bot")
        print("2. Test the new commands in Matrix:")
        print("   !bot help")
        print("   !bot server")
        print("   !bot cpu")
        print("   !bot memory")
        print("3. Monitor logs:")
        print("   docker logs -f matrix-bot")
    else:
        print("❌ Some verification checks FAILED!")
        print("Please review the issues above before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()
