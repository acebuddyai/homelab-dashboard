#!/bin/bash

# Security Verification Script for Homelab Repository
# This script checks that sensitive files are properly excluded from git

set -e

echo "🔒 Homelab Security Verification"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track if any security issues are found
SECURITY_ISSUES=0

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        SECURITY_ISSUES=1
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "ℹ️  $1"
}

echo
echo "1. Checking Git Repository Status"
echo "─────────────────────────────────"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_status 1 "Not in a git repository"
    exit 1
fi

print_status 0 "Git repository detected"

# Check if there are any .env files staged for commit
STAGED_ENV_FILES=$(git diff --cached --name-only | grep -E "\.env$" || true)
if [ -n "$STAGED_ENV_FILES" ]; then
    print_status 1 "Environment files are staged for commit!"
    echo "   Staged .env files:"
    echo "$STAGED_ENV_FILES" | sed 's/^/   - /'
    echo "   Run: git rm --cached <file> to unstage them"
else
    print_status 0 "No .env files staged for commit"
fi

# Check if there are any .env files tracked by git
TRACKED_ENV_FILES=$(git ls-files | grep -E "\.env$" || true)
if [ -n "$TRACKED_ENV_FILES" ]; then
    print_status 1 "Environment files are tracked by git!"
    echo "   Tracked .env files:"
    echo "$TRACKED_ENV_FILES" | sed 's/^/   - /'
else
    print_status 0 "No .env files tracked by git"
fi

echo
echo "2. Checking .gitignore Configuration"
echo "───────────────────────────────────"

if [ -f .gitignore ]; then
    print_status 0 ".gitignore file exists"

    # Check if .env is in .gitignore
    if grep -q "^\.env$" .gitignore || grep -q "^\.env" .gitignore; then
        print_status 0 ".env exclusion found in .gitignore"
    else
        print_status 1 ".env exclusion NOT found in .gitignore"
    fi

    # Check if .env.* pattern is in .gitignore
    if grep -q "\.env\.\*" .gitignore; then
        print_status 0 ".env.* pattern found in .gitignore"
    else
        print_warning ".env.* pattern not found in .gitignore (optional but recommended)"
    fi
else
    print_status 1 ".gitignore file missing"
fi

echo
echo "3. Checking Environment File Status"
echo "──────────────────────────────────"

# Check for .env files in the working directory
ENV_FILES=$(find . -name ".env" -type f 2>/dev/null || true)
if [ -n "$ENV_FILES" ]; then
    print_info "Found .env files in working directory (this is normal):"
    echo "$ENV_FILES" | sed 's/^/   - /'

    # Check if these files are ignored by git
    for env_file in $ENV_FILES; do
        if git check-ignore "$env_file" > /dev/null 2>&1; then
            print_status 0 "$env_file is properly ignored by git"
        else
            print_status 1 "$env_file is NOT ignored by git"
        fi
    done
else
    print_warning "No .env files found (you may need to create them from .env.example)"
fi

# Check for .env.example files
EXAMPLE_FILES=$(find . -name ".env.example" -type f 2>/dev/null || true)
if [ -n "$EXAMPLE_FILES" ]; then
    print_status 0 "Found .env.example template files"
    echo "$EXAMPLE_FILES" | sed 's/^/   - /'
else
    print_warning "No .env.example files found"
fi

echo
echo "4. Checking Matrix Bot Configuration"
echo "──────────────────────────────────"

# Check Matrix bot specific files
if [ -f "matrix/bot/.env" ]; then
    if git check-ignore "matrix/bot/.env" > /dev/null 2>&1; then
        print_status 0 "Matrix bot .env file is properly ignored"
    else
        print_status 1 "Matrix bot .env file is NOT ignored by git"
    fi
else
    print_warning "Matrix bot .env file not found (create from .env.example)"
fi

if [ -f "matrix/bot/.env.example" ]; then
    print_status 0 "Matrix bot .env.example template exists"
else
    print_status 1 "Matrix bot .env.example template missing"
fi

# Check if bot files have hardcoded credentials
if [ -f "matrix/bot/config.py" ]; then
    if grep -q "entourage8-shuffling-poncho\|acebuddy\.quest" "matrix/bot/config.py" 2>/dev/null; then
        print_warning "Possible hardcoded credentials found in matrix/bot/config.py"
    else
        print_status 0 "No obvious hardcoded credentials in matrix/bot/config.py"
    fi
fi

if [ -f "matrix/bot/enhanced_bot.py" ]; then
    if grep -q "entourage8-shuffling-poncho\|acebuddy\.quest" "matrix/bot/enhanced_bot.py" 2>/dev/null; then
        print_warning "Possible hardcoded credentials found in matrix/bot/enhanced_bot.py"
    else
        print_status 0 "No obvious hardcoded credentials in matrix/bot/enhanced_bot.py"
    fi
fi

echo
echo "5. Checking for Sensitive Content"
echo "────────────────────────────────"

# Check for potential passwords or keys in tracked files
SENSITIVE_PATTERNS=(
    "password.*=.*['\"][^'\"]{8,}"
    "secret.*=.*['\"][^'\"]{8,}"
    "key.*=.*['\"][^'\"]{16,}"
    "token.*=.*['\"][^'\"]{16,}"
)

for pattern in "${SENSITIVE_PATTERNS[@]}"; do
    MATCHES=$(git ls-files -z | xargs -0 grep -l -i -E "$pattern" 2>/dev/null || true)
    if [ -n "$MATCHES" ]; then
        print_warning "Potential sensitive content found (pattern: $pattern)"
        echo "$MATCHES" | sed 's/^/   - /'
    fi
done

echo
echo "6. Repository Recommendations"
echo "────────────────────────────"

print_info "Ensure your GitHub repository is set to PRIVATE"
print_info "Regularly rotate credentials that may have been exposed"
print_info "Use environment variables for all sensitive configuration"
print_info "Keep .env.example files updated but without real credentials"

echo
echo "==============================================="

if [ $SECURITY_ISSUES -eq 0 ]; then
    echo -e "${GREEN}🎉 Security verification PASSED!${NC}"
    echo -e "${GREEN}✅ Repository appears secure for commit/push${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Security verification FAILED!${NC}"
    echo -e "${RED}❌ Please address the issues above before committing${NC}"
    exit 1
fi
