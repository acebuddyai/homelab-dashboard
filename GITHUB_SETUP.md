# GitHub Repository Setup Instructions

## Overview
This document provides step-by-step instructions to create a private GitHub repository for your homelab infrastructure and push the current code while maintaining security.

## Prerequisites
- GitHub account with repository creation permissions
- Git configured locally (already done)
- Current homelab code committed locally (✅ completed)

## Step 1: Create Private GitHub Repository

### Option A: Using GitHub Web Interface
1. Go to [GitHub.com](https://github.com) and sign in
2. Click the "+" icon in the top right corner
3. Select "New repository"
4. Configure the repository:
   - **Repository name**: `homelab` (or your preferred name)
   - **Description**: "Private homelab infrastructure with Matrix server, bot, and services"
   - **Visibility**: ⚠️ **PRIVATE** (very important for security)
   - **Initialize repository**: Leave unchecked (we already have content)
   - **Add .gitignore**: Leave as "None" (we already have one)
   - **Add a license**: Optional (can add later)
5. Click "Create repository"

### Option B: Using GitHub CLI (if available)
```bash
# Install GitHub CLI first if not available
# Then run:
gh repo create homelab --private --description "Private homelab infrastructure"
```

## Step 2: Add Remote and Push

After creating the GitHub repository, you'll see a page with setup instructions. Use the existing repository option:

```bash
# Navigate to your homelab directory
cd /home/relock/homelab

# Add the GitHub repository as remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/homelab.git

# Push the code to GitHub
git push -u origin main
```

## Step 3: Verify Security

### Check that sensitive files are excluded:
```bash
# This should NOT show any .env files in the repository
git ls-files | grep -E "\.env$"

# This should be empty - if it shows files, DO NOT PUSH
```

### Verify .gitignore is working:
```bash
# Check git status - .env files should not appear
git status

# If you see .env files listed, add them to .gitignore:
echo ".env" >> .gitignore
echo "**/.env" >> .gitignore
git add .gitignore
git commit -m "Ensure all .env files are excluded"
```

## Step 4: Environment Setup on Server

Since `.env` files are excluded from the repository, you'll need to recreate them on any new deployment:

### Matrix Bot Environment Setup
```bash
# On the server, navigate to the bot directory
cd homelab/matrix/bot

# Copy the example and edit with real values
cp .env.example .env

# Edit the .env file with your actual credentials
nano .env  # or your preferred editor

# The .env file should contain:
MATRIX_HOMESERVER_URL=https://matrix.acebuddy.quest
MATRIX_BOT_USERNAME=@subatomic6140:acebuddy.quest
MATRIX_BOT_PASSWORD=your-actual-password
MATRIX_TARGET_ROOM_ID=!your-room-id:acebuddy.quest
# ... other configuration
```

### Main Homelab Environment Setup
```bash
# In the main homelab directory
cd homelab

# Copy the example and edit with real values
cp .env.example .env

# Edit with your actual credentials
nano .env
```

## Step 5: Test Deployment

After setting up the environment files:

```bash
# Test the Matrix bot
cd homelab/matrix
docker-compose up -d matrix-bot
docker-compose logs matrix-bot

# Should see successful login and room join messages
```

## Security Checklist

- [ ] Repository is set to **PRIVATE**
- [ ] No `.env` files are committed to the repository
- [ ] `.env.example` files are included as templates
- [ ] `.gitignore` properly excludes sensitive files
- [ ] Environment variables are set up separately on each deployment
- [ ] Credentials are never hardcoded in the source code

## Cloning on New Systems

When setting up on a new server:

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/homelab.git
cd homelab

# Set up environment files
cp .env.example .env
cp matrix/bot/.env.example matrix/bot/.env

# Edit both .env files with actual credentials
nano .env
nano matrix/bot/.env

# Deploy services
./deploy.sh
```

## Backup Strategy

### What's in Git (safe to backup publicly):
- Application code and configuration templates
- Docker Compose files
- Documentation and scripts
- .env.example files

### What's NOT in Git (keep private):
- .env files with actual credentials
- Database data
- Generated keys and certificates
- User data

### Recommended Backup:
- Code: Backed up automatically via GitHub private repository
- Credentials: Store securely in password manager or vault
- Data: Regular encrypted backups of Docker volumes

## Troubleshooting

### If .env files were accidentally committed:
```bash
# Remove from git history (be careful!)
git filter-branch --force --index-filter \
'git rm --cached --ignore-unmatch matrix/bot/.env' \
--prune-empty --tag-name-filter cat -- --all

# Force push (only if repository is private and you're sure)
git push origin --force --all
```

### If credentials are exposed:
1. Immediately rotate all exposed credentials
2. Check repository visibility (should be private)
3. Review commit history for sensitive data
4. Consider creating a new repository if necessary

## Support

For issues with this setup:
1. Verify repository is private
2. Check .gitignore is working: `git status`
3. Ensure environment files exist locally: `ls -la */.env`
4. Test deployment after environment setup

Remember: **Security first** - always verify that sensitive information is not being committed to the repository.