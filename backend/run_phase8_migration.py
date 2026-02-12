#!/usr/bin/env python
"""
Phase 8 Database Migration Runner
Executes the Phase 8 migration without alembic CLI
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import os
    from dotenv import load_dotenv
    from sqlalchemy import create_engine, inspect
    from sqlalchemy.orm import sessionmaker
    from app.models.cohort_models import (
        CohortAnalysis, RetentionCurve, LifetimeValue,
        CustomerJourney, ChurnFlow, FeatureAdoption,
        RetentionIntervention, CustomMetric, MetricHistory
    )
    from app.database.config import engine, Base
    
    print("✅ Importing models...")
    
    # Load environment variables
    load_dotenv()
    db_url = os.getenv("DATABASE_URL", "postgresql://user:password@127.0.0.1:5432/omnidev")
    print(f"📊 Database: {db_url.split('@')[1] if '@' in db_url else 'local'}")
    
    print("🔧 Engine ready")
    
    # Create all tables
    print("📝 Creating Phase 8 tables...")
    Base.metadata.create_all(engine)
    print("✅ Tables created")
    
    # Verify tables
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    phase8_tables = [
        'cohort_analysis', 'retention_curve', 'lifetime_value',
        'customer_journey', 'churn_flow', 'feature_adoption',
        'retention_intervention', 'custom_metric', 'metric_history'
    ]
    
    print("\n📋 Verifying Phase 8 tables:")
    for table in phase8_tables:
        if table in tables:
            print(f"  ✅ {table}")
        else:
            print(f"  ❌ {table} NOT FOUND")
    
    print(f"\n🎉 Phase 8 Database Migration Complete!")
    print(f"Total tables in database: {len(tables)}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
