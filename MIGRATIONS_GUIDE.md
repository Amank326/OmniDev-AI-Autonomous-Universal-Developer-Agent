# 🔄 Alembic Migrations Setup Guide

## Overview

Alembic is already installed in requirements.txt. This guide shows how to set up and use it for database migrations.

## Current Status

✅ Alembic is installed  
✅ Alembic directory exists at `backend/migrations/`  
⏳ Needs initial configuration for automatic model detection  

## Setup Instructions

### 1. Initialize Alembic (if not already done)

```bash
cd backend
alembic init migrations
```

### 2. Configure Alembic

Edit `migrations/env.py`:

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
from app.database import Base
from app.database.models import *  # Import all models

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/omnidev"
)

config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)
target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = DATABASE_URL
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 3. Create Initial Migration

```bash
# Generate migration file from current models
alembic revision --autogenerate -m "Initial migration with all models"
```

This creates a migration file in `migrations/versions/` that captures your current model state.

### 4. Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Check migration status
alembic current
```

## Migration Workflow

### Creating Migrations

```bash
# After modifying models in models.py
alembic revision --autogenerate -m "Add new field to User model"
```

This generates a new migration file with:
- Changes to add new fields
- Changes to remove fields
- Changes to modify field types
- Changes to relationships

### Review Before Applying

Always review generated migration file before applying:

```bash
# Check what the migration does
cat migrations/versions/[migration_id].py

# Manually edit if needed
nano migrations/versions/[migration_id].py
```

### Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply to specific revision
alembic upgrade 123abc4def5

# Rollback to previous version
alembic downgrade -1

# Rollback to specific version
alembic downgrade 123abc4def5
```

## Migration File Structure

```python
"""Initial migration with all models"""
from alembic import op
import sqlalchemy as sa

# revision identifiers used by Alembic
revision = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Apply changes forward"""
    # Create tables
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        # ... more columns
    )

def downgrade() -> None:
    """Revert changes"""
    op.drop_table('users')
```

## Useful Commands

```bash
# Show current database revision
alembic current

# Show revision history
alembic history

# Show what migration would do (dry run)
alembic upgrade head --sql

# Create empty migration for manual edits
alembic revision -m "Manual changes"

# Merge conflicting migrations
alembic merge -m "Merge branches"

# Show information about specific revision
alembic show a1b2c3d4e5f6
```

## Best Practices

1. **Always create migrations for schema changes** - Don't use `init_db()` in production
2. **Review migrations** - Check auto-generated migrations before applying
3. **Test migrations** - Test upgrade and downgrade before deploying
4. **One change per migration** - Easier to debug and revert
5. **Descriptive names** - Use clear names: "add_email_field_to_user" not "update_schema"
6. **Keep migrations atomic** - Each migration should be independent
7. **Version control** - Commit all migration files to git
8. **Database backups** - Always backup before running migrations in production

## Example: Adding a New Field

### Step 1: Modify Model

```python
# In models.py
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=True)  # ← NEW FIELD
    # ... rest of model
```

### Step 2: Generate Migration

```bash
alembic revision --autogenerate -m "Add phone field to users"
```

Generated file (`migrations/versions/abc123def456_add_phone_field_to_users.py`):

```python
def upgrade() -> None:
    op.add_column('users', sa.Column('phone', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'phone')
```

### Step 3: Apply Migration

```bash
alembic upgrade head
```

## Development Workflow

```bash
# 1. Develop locally
# Edit models.py

# 2. Generate migration
alembic revision --autogenerate -m "Description"

# 3. Review migration file
nano migrations/versions/[migration_id].py

# 4. Test locally
alembic upgrade head

# 5. Commit to git
git add migrations/versions/[migration_id].py
git commit -m "Add migration: description"

# 6. Deploy to production
alembic upgrade head
```

## Production Deployment

```bash
# On production server:

# 1. Backup database
pg_dump -U user -h localhost -d omnidev > backup.sql

# 2. Apply migrations
alembic upgrade head

# 3. Verify
alembic current

# 4. Monitor application logs
tail -f app.log
```

## Troubleshooting

### Migration Won't Apply

```bash
# Check for syntax errors
alembic upgrade head --sql

# Check current state
alembic current

# Manually mark migration as applied
alembic stamp a1b2c3d4e5f6

# Then apply new migrations
alembic upgrade head
```

### Auto-generation Not Detecting Changes

```bash
# Make sure imports are in env.py
from app.database.models import *

# Alembic compares current schema to migration history
# May need manual edit for complex changes
```

### Rollback

```bash
# Go back one migration
alembic downgrade -1

# Go back to specific version
alembic downgrade a1b2c3d4e5f6

# Remove migration from tracking (caution!)
alembic stamp head
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Database Migrations

on:
  pull_request:
    paths:
      - 'backend/app/database/models.py'

jobs:
  check-migration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r backend/requirements.txt
      - run: alembic upgrade head --sql > /tmp/migration.sql
      - run: wc -l /tmp/migration.sql
```

## Current Migration Status

**Location**: `c:\Users\amank\OneDrive\Desktop\omnidev-ai\backend\migrations\`

**Next Steps**:
1. Run `alembic revision --autogenerate -m "Initial migration"` 
2. Review the generated migration file
3. Apply with `alembic upgrade head`
4. Commit migration files to git

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Migrations](https://docs.sqlalchemy.org/en/20/orm/declarative_config.html)
- [Alembic Best Practices](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)

---

**Status**: ✅ Ready to Setup  
**Alembic Version**: 1.18.3  
**SQLAlchemy Version**: 2.0.46  
**Last Updated**: February 2025
