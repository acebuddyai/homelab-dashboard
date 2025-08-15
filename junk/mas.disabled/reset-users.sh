#!/bin/bash
# =============================================================================
# MAS User Database Reset Script
# =============================================================================

echo "🗑️  Dropping all users from MAS database..."

# Stop MAS service but keep database running
docker-compose stop matrix-auth-service

echo "🗃️  Clearing user data from database..."

# Clear all users and related data
docker exec mas-postgres psql -U mas_user -d mas -c "
DO \$\$
BEGIN
    TRUNCATE TABLE user_sessions CASCADE;
    TRUNCATE TABLE user_emails CASCADE;
    TRUNCATE TABLE user_passwords CASCADE;
    TRUNCATE TABLE user_terms CASCADE;
    TRUNCATE TABLE users CASCADE;

    RAISE NOTICE 'All user data cleared successfully!';
    RAISE NOTICE 'Users remaining: %', (SELECT COUNT(*) FROM users);
END
\$\$;
"

echo "✅ User database reset complete!"
echo "🚀 Ready for fresh testing - restart MAS to continue"
