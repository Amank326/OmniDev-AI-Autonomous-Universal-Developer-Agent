"""
Phase 49: Enterprise Analytics & Business Intelligence Verification Script

Comprehensive verification for all Phase 49 services and endpoints.
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

def verify_phase49():
    """Verify Phase 49 deployment"""
    
    print("\n" + "="*80)
    print("Phase 49: Enterprise Analytics & Business Intelligence - Verification")
    print("="*80 + "\n")
    
    checks_passed = 0
    checks_total = 0
    
    # Check 1: Service files exist
    print("📁 Checking service files...")
    checks_total += 1
    try:
        service_file = Path("backend/app/services/enterprise_analytics_service.py")
        if service_file.exists():
            size = service_file.stat().st_size
            print(f"   ✅ enterprise_analytics_service.py ({size:,} bytes)")
            checks_passed += 1
        else:
            print(f"   ❌ enterprise_analytics_service.py NOT FOUND")
    except Exception as e:
        print(f"   ❌ Error checking service file: {e}")
    
    # Check 2: API routes file exists
    print("\n📁 Checking API routes file...")
    checks_total += 1
    try:
        routes_file = Path("backend/app/api/analytics_routes_phase49.py")
        if routes_file.exists():
            size = routes_file.stat().st_size
            print(f"   ✅ analytics_routes_phase49.py ({size:,} bytes)")
            checks_passed += 1
        else:
            print(f"   ❌ analytics_routes_phase49.py NOT FOUND")
    except Exception as e:
        print(f"   ❌ Error checking routes file: {e}")
    
    # Check 3: Import services
    print("\n📦 Importing Phase 49 services...")
    checks_total += 1
    try:
        from app.services.enterprise_analytics_service import (
            get_phase49_service,
            BusinessMetricsService,
            BusinessDashboardService,
            ROIAnalysisService,
            PredictiveAnalyticsService,
            BusinessIntelligenceService,
            MetricType,
            KPIDefinition
        )
        print("   ✅ All services imported successfully")
        checks_passed += 1
        service = get_phase49_service()
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        service = None
    
    # Check 4: Service instantiation
    print("\n⚙️  Checking service instantiation...")
    if service:
        checks_total += 1
        try:
            print(f"   ✅ BusinessMetricsService: {type(service.business_metrics).__name__}")
            print(f"   ✅ BusinessDashboardService: {type(service.dashboard).__name__}")
            print(f"   ✅ ROIAnalysisService: {type(service.roi_analysis).__name__}")
            print(f"   ✅ PredictiveAnalyticsService: {type(service.predictive_analytics).__name__}")
            print(f"   ✅ BusinessIntelligenceService: {type(service.business_intelligence).__name__}")
            checks_passed += 1
        except Exception as e:
            print(f"   ❌ Instantiation error: {e}")
    
    # Check 5: Service status
    print("\n📊 Checking service status...")
    if service:
        checks_total += 1
        try:
            status = service.get_status()
            print(f"   Phase: {status['phase']}")
            print(f"   Status: {status['status']}")
            print(f"   Services: {len(status['services'])} operational")
            checks_passed += 1
        except Exception as e:
            print(f"   ❌ Status check error: {e}")
    
    # Check 6: Import API routes
    print("\n🔌 Importing API routes...")
    checks_total += 1
    try:
        from app.api.analytics_routes_phase49 import router
        print(f"   ✅ Analytics routes router imported successfully")
        print(f"   ✅ Router prefix: /api/v1/analytics")
        checks_passed += 1
    except Exception as e:
        print(f"   ❌ Routes import error: {e}")
    
    # Check 7: Business Metrics Service tests
    print("\n🧪 Testing BusinessMetricsService...")
    if service:
        checks_total += 1
        try:
            # Define KPI
            kpi = KPIDefinition(
                name="test_revenue",
                metric_type=MetricType.REVENUE,
                formula="test_formula",
                target=1000,
                threshold_warning=900,
                threshold_critical=800,
                refresh_interval=60,
                owner="Test Owner"
            )
            service.business_metrics.define_kpi(kpi)
            
            # Record value
            service.business_metrics.record_kpi_value("test_revenue", 950)
            
            # Get status
            status = service.business_metrics.get_kpi_status("test_revenue")
            
            if status and status.current_value == 950:
                print(f"   ✅ KPI Definition: SUCCESS")
                print(f"   ✅ Value Recording: SUCCESS")
                print(f"   ✅ Status Retrieval: SUCCESS")
                print(f"      Current Value: {status.current_value}")
                print(f"      Status: {status.status}")
                print(f"      Trend: {status.trend}")
                checks_passed += 1
            else:
                print(f"   ❌ Status retrieval failed")
        except Exception as e:
            print(f"   ❌ Test error: {e}")
    
    # Check 8: Dashboard Service tests
    print("\n🧪 Testing BusinessDashboardService...")
    if service:
        checks_total += 1
        try:
            service.dashboard.create_dashboard("Test Dashboard", "Test Description")
            dashboard = service.dashboard.get_dashboard("Test Dashboard")
            
            if dashboard:
                print(f"   ✅ Dashboard Creation: SUCCESS")
                print(f"   ✅ Dashboard Retrieval: SUCCESS")
                print(f"      Dashboard Name: {dashboard['name']}")
                checks_passed += 1
            else:
                print(f"   ❌ Dashboard retrieval failed")
        except Exception as e:
            print(f"   ❌ Test error: {e}")
    
    # Check 9: ROI Analysis Service tests
    print("\n🧪 Testing ROIAnalysisService...")
    if service:
        checks_total += 1
        try:
            service.roi_analysis.record_cost("test_category", 1000, "Test Cost")
            roi = service.roi_analysis.calculate_roi(10000, 15000, 90)
            
            if roi and roi.get("roi_percent") == 50:
                print(f"   ✅ Cost Recording: SUCCESS")
                print(f"   ✅ ROI Calculation: SUCCESS")
                print(f"      ROI %: {roi['roi_percent']}")
                print(f"      Annualized ROI: {roi['annualized_roi']:.1f}%")
                checks_passed += 1
            else:
                print(f"   ❌ ROI calculation failed")
        except Exception as e:
            print(f"   ❌ Test error: {e}")
    
    # Check 10: Predictive Analytics tests
    print("\n🧪 Testing PredictiveAnalyticsService...")
    if service:
        checks_total += 1
        try:
            service.predictive_analytics.add_data_point("test_metric", 100)
            service.predictive_analytics.add_data_point("test_metric", 105)
            service.predictive_analytics.add_data_point("test_metric", 110)
            
            forecast = service.predictive_analytics.forecast_simple("test_metric", 3)
            trend = service.predictive_analytics.detect_trend("test_metric", 3)
            
            if forecast and trend:
                print(f"   ✅ Data Point Recording: SUCCESS")
                print(f"   ✅ Forecasting: SUCCESS ({len(forecast)} periods)")
                print(f"   ✅ Trend Detection: SUCCESS (Trend: {trend})")
                checks_passed += 1
            else:
                print(f"   ❌ Forecast or trend detection failed")
        except Exception as e:
            print(f"   ❌ Test error: {e}")
    
    # Check 11: Business Intelligence tests
    print("\n🧪 Testing BusinessIntelligenceService...")
    if service:
        checks_total += 1
        try:
            service.business_intelligence.generate_insight(
                "Test Insight",
                "This is a test insight",
                "high",
                "Test recommendation",
                "test_metric"
            )
            
            insights = service.business_intelligence.get_high_impact_insights(10)
            summary = service.business_intelligence.generate_executive_summary()
            
            if insights and summary:
                print(f"   ✅ Insight Generation: SUCCESS")
                print(f"   ✅ Insight Retrieval: SUCCESS ({len(insights)} high-impact)")
                print(f"   ✅ Executive Summary: SUCCESS")
                print(f"      Total Insights: {summary.get('total_insights', 0)}")
                checks_passed += 1
            else:
                print(f"   ❌ Insight operations failed")
        except Exception as e:
            print(f"   ❌ Test error: {e}")
    
    # Summary
    print("\n" + "="*80)
    print("PHASE 49 VERIFICATION SUMMARY")
    print("="*80)
    print(f"\n✅ Checks Passed: {checks_passed}/{checks_total}")
    print(f"📊 Success Rate: {(checks_passed/checks_total*100):.1f}%")
    
    if checks_passed == checks_total:
        print("\n🎉 PHASE 49: COMPLETE & OPERATIONAL ✅")
    else:
        print(f"\n⚠️  Phase 49: {checks_total - checks_passed} issue(s) detected")
    
    print("\n" + "="*80 + "\n")
    
    return checks_passed == checks_total


if __name__ == "__main__":
    success = verify_phase49()
    sys.exit(0 if success else 1)
