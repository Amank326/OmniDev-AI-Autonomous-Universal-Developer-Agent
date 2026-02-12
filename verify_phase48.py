#!/usr/bin/env python3
"""
Phase 48 Verification Script
Verify all Phase 48 services are properly deployed
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, 'backend')

def verify_phase48():
    """Verify Phase 48 deployment"""
    print("\n" + "="*70)
    print("PHASE 48 - ADVANCED MONITORING & ANALYTICS VERIFICATION".center(70))
    print("="*70 + "\n")
    
    # Check files
    print("📁 CHECKING FILES:\n")
    files_to_check = {
        'app/services/advanced_monitoring_service.py': 'Advanced Monitoring Service',
        'app/api/monitoring_routes_phase48.py': 'Monitoring API Routes',
    }
    
    all_good = True
    for filepath, description in files_to_check.items():
        full_path = f"backend/{filepath}"
        if os.path.exists(full_path):
            file_size = os.path.getsize(full_path)
            print(f"  ✅ {description:35} | {file_size:6} bytes")
        else:
            print(f"  ❌ {description:35} | FILE NOT FOUND")
            all_good = False
    
    # Import services
    print("\n📦 IMPORTING SERVICES:\n")
    try:
        from app.services.advanced_monitoring_service import (
            advanced_monitoring, performance_analytics, real_time_dashboard,
            alert_management, analytics_reporting
        )
        print("  ✅ All services imported successfully\n")
        
        # Show statistics
        print("📊 SERVICE STATISTICS:\n")
        services = [
            ("Advanced Monitoring", advanced_monitoring),
            ("Performance Analytics", performance_analytics),
            ("Real-Time Dashboard", real_time_dashboard),
            ("Alert Management", alert_management),
            ("Analytics & Reporting", analytics_reporting),
        ]
        
        for name, service in services:
            stats = service.get_statistics()
            status = stats.get("status", "unknown")
            print(f"  ✅ {name:25} | Status: {status:12} | {stats}")
        
    except Exception as e:
        print(f"  ❌ Import error: {e}")
        all_good = False
    
    # Summary
    print("\n" + "="*70)
    if all_good:
        print("✅ PHASE 48 VERIFICATION: COMPLETE & OPERATIONAL".center(70))
    else:
        print("⚠️  PHASE 48 VERIFICATION: SOME CHECKS FAILED".center(70))
    print("="*70 + "\n")
    
    return 0 if all_good else 1

if __name__ == '__main__':
    sys.exit(verify_phase48())
