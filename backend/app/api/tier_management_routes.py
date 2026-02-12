"""
Tier Management API Routes - Subscription tiers, upselling, and usage-based pricing
Provides 32+ endpoints for tier management, upselling, and pricing operations
"""

from flask import Blueprint, request, jsonify
from typing import Dict
from datetime import datetime


def create_tier_management_routes(
    tier_service,
    quota_service,
    upsell_service,
    pricing_service,
):
    """
    Create tier management API routes.
    
    Args:
        tier_service: Subscription tier service instance
        quota_service: Usage quota service instance
        upsell_service: Upsell engine service instance
        pricing_service: Usage-based pricing service instance
    
    Returns:
        Flask blueprint with all routes
    """
    
    tier_bp = Blueprint("tiers", __name__, url_prefix="/api/v1/tiers")
    
    def response(data, status=200, message=None):
        return jsonify({
            "status": "success" if status == 200 else "error",
            "message": message,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }), status
    
    # ============================================================================
    # TIER MANAGEMENT ENDPOINTS (8 endpoints)
    # ============================================================================
    
    @tier_bp.route("/", methods=["GET"])
    def list_tiers():
        """List all available tiers"""
        result = tier_service.list_all_tiers()
        return response(result, 200)
    
    @tier_bp.route("/<tier>", methods=["GET"])
    def get_tier(tier):
        """Get specific tier definition"""
        result = tier_service.get_tier_definition(tier)
        if not result:
            return response(None, 404, "Tier not found")
        return response(result, 200)
    
    @tier_bp.route("/<customer_id>/subscribe", methods=["POST"])
    def subscribe_tier(customer_id):
        """Subscribe customer to tier"""
        data = request.json
        result = tier_service.subscribe_to_tier(
            customer_id=customer_id,
            tier_level=data.get("tier"),
            billing_cycle=data.get("billing_cycle", "monthly"),
            start_date=data.get("start_date"),
        )
        return response(result, 201, "Subscription created")
    
    @tier_bp.route("/<customer_id>/current", methods=["GET"])
    def get_current_tier(customer_id):
        """Get customer's current tier"""
        result = tier_service.get_customer_tier(customer_id)
        return response(result, 200)
    
    @tier_bp.route("/<customer_id>/upgrade", methods=["POST"])
    def upgrade_customer_tier(customer_id):
        """Upgrade customer to higher tier"""
        data = request.json
        result = tier_service.upgrade_tier(
            customer_id=customer_id,
            new_tier_level=data.get("tier"),
            proration=data.get("proration", True),
        )
        return response(result, 200, "Upgrade processed")
    
    @tier_bp.route("/<customer_id>/downgrade", methods=["POST"])
    def downgrade_customer_tier(customer_id):
        """Downgrade customer to lower tier"""
        data = request.json
        result = tier_service.downgrade_tier(
            customer_id=customer_id,
            new_tier_level=data.get("tier"),
            effective_date=data.get("effective_date"),
            reason=data.get("reason"),
        )
        return response(result, 200, "Downgrade processed")
    
    @tier_bp.route("/<customer_id>/limits", methods=["GET"])
    def get_feature_limits(customer_id):
        """Get feature limits for customer's tier"""
        result = tier_service.get_feature_limits(customer_id)
        return response(result, 200)
    
    @tier_bp.route("/<customer_id>/features/<feature>", methods=["GET"])
    def check_feature_access(customer_id, feature):
        """Check if customer has access to feature"""
        has_access = tier_service.has_feature(customer_id, feature)
        return response({"has_access": has_access}, 200)
    
    # ============================================================================
    # USAGE & QUOTA ENDPOINTS (8 endpoints)
    # ============================================================================
    
    @tier_bp.route("/<customer_id>/usage", methods=["GET"])
    def get_usage_status(customer_id):
        """Get comprehensive usage status"""
        result = quota_service.get_usage_status(customer_id)
        return response(result, 200)
    
    @tier_bp.route("/<customer_id>/usage/track", methods=["POST"])
    def track_usage(customer_id):
        """Track usage of a metric"""
        data = request.json
        result = quota_service.track_usage(
            customer_id=customer_id,
            metric=data.get("metric"),
            amount=data.get("amount", 1.0),
        )
        return response(result, 200)
    
    @tier_bp.route("/<customer_id>/usage/batch", methods=["POST"])
    def batch_track_usage(customer_id):
        """Track multiple metrics at once"""
        data = request.json
        result = quota_service.bulk_track_usage(
            customer_id=customer_id,
            metrics=data.get("metrics", {}),
        )
        return response(result, 200)
    
    @tier_bp.route("/<customer_id>/usage/check/<metric>", methods=["GET"])
    def check_quota(customer_id, metric):
        """Check if operation would exceed quota"""
        requested = request.args.get("amount", 1.0, type=float)
        result = quota_service.check_quota_limit(
            customer_id=customer_id,
            metric=metric,
            requested_amount=requested,
        )
        return response(result, 200)
    
    @tier_bp.route("/<customer_id>/quota/reset", methods=["POST"])
    def reset_quota(customer_id):
        """Manually reset quota"""
        result = quota_service.reset_quota(customer_id)
        return response(result, 200, "Quota reset")
    
    @tier_bp.route("/<customer_id>/features/<feature>/enable", methods=["POST"])
    def enable_feature(customer_id, feature):
        """Enable feature flag for customer"""
        data = request.json
        result = quota_service.set_feature_flag(
            customer_id=customer_id,
            feature_name=feature,
            enabled=True,
            reason=data.get("reason"),
            expiration_date=data.get("expiration_date"),
        )
        return response(result, 200, "Feature enabled")
    
    @tier_bp.route("/<customer_id>/features/<feature>/disable", methods=["POST"])
    def disable_feature(customer_id, feature):
        """Disable feature flag for customer"""
        data = request.json
        result = quota_service.set_feature_flag(
            customer_id=customer_id,
            feature_name=feature,
            enabled=False,
            reason=data.get("reason"),
            expiration_date=data.get("expiration_date"),
        )
        return response(result, 200, "Feature disabled")
    
    @tier_bp.route("/<customer_id>/overages", methods=["GET"])
    def get_overage_report(customer_id):
        """Get overage report for billing"""
        result = quota_service.get_overage_report(customer_id)
        return response(result, 200)
    
    # ============================================================================
    # UPSELLING ENDPOINTS (8 endpoints)
    # ============================================================================
    
    @tier_bp.route("/<customer_id>/upsell/opportunities", methods=["POST"])
    def identify_upsell_opportunities(customer_id):
        """Identify upsell opportunities for customer"""
        data = request.json
        results = upsell_service.identify_upsell_opportunities(
            customer_id=customer_id,
            current_tier=data.get("current_tier"),
            usage_metrics=data.get("usage_metrics", {}),
            engagement_data=data.get("engagement_data", {}),
            customer_profile=data.get("customer_profile", {}),
        )
        return response(results, 200)
    
    @tier_bp.route("/<customer_id>/engagement-score", methods=["POST"])
    def calculate_engagement_score(customer_id):
        """Calculate engagement score for customer"""
        data = request.json
        result = upsell_service.calculate_engagement_score(
            customer_id=customer_id,
            engagement_data=data.get("engagement_data", {}),
        )
        return response(result, 200)
    
    @tier_bp.route("/<customer_id>/upsell/campaign", methods=["POST"])
    def create_campaign(customer_id):
        """Create upsell campaign for customer"""
        data = request.json
        result = upsell_service.create_upsell_campaign(
            customer_id=customer_id,
            opportunity_type=data.get("opportunity_type"),
            target_tier=data.get("target_tier"),
            messaging=data.get("messaging", {}),
            trigger_condition=data.get("trigger_condition"),
        )
        return response(result, 201, "Campaign created")
    
    @tier_bp.route("/campaigns/<campaign_id>/track/<event>", methods=["POST"])
    def track_campaign_event(campaign_id, event):
        """Track campaign engagement event"""
        data = request.json
        result = upsell_service.track_campaign_engagement(
            campaign_id=campaign_id,
            customer_id=data.get("customer_id"),
            event_type=event,
        )
        return response(result, 200, "Event tracked")
    
    @tier_bp.route("/<customer_id>/upsell/recommendations", methods=["GET"])
    def get_upsell_recommendations(customer_id):
        """Get current upsell recommendations"""
        results = upsell_service.get_upsell_recommendations(customer_id)
        return response(results, 200)
    
    @tier_bp.route("/<customer_id>/conversion-funnel", methods=["GET"])
    def get_conversion_funnel(customer_id):
        """Get conversion funnel status"""
        result = upsell_service.get_conversion_funnel(customer_id)
        return response(result, 200)
    
    # ============================================================================
    # PRICING ENDPOINTS (8 endpoints)
    # ============================================================================
    
    @tier_bp.route("/pricing/metered", methods=["POST"])
    def create_metered_pricing():
        """Create metered/usage-based pricing"""
        data = request.json
        result = pricing_service.create_metered_pricing(
            customer_id=data.get("customer_id"),
            metric_name=data.get("metric_name"),
            unit_price=data.get("unit_price"),
            billing_cycle=data.get("billing_cycle", "monthly"),
            minimum_charge=data.get("minimum_charge", 0),
            maximum_charge=data.get("maximum_charge"),
        )
        return response(result, 201, "Metered pricing created")
    
    @tier_bp.route("/pricing/tiered", methods=["POST"])
    def create_tiered_pricing():
        """Create tiered pricing structure"""
        data = request.json
        result = pricing_service.create_tiered_pricing(
            customer_id=data.get("customer_id"),
            metric_name=data.get("metric_name"),
            tiers=data.get("tiers", []),
            billing_cycle=data.get("billing_cycle", "monthly"),
        )
        return response(result, 201, "Tiered pricing created")
    
    @tier_bp.route("/pricing/volume-discount", methods=["POST"])
    def create_volume_discount():
        """Create volume discount pricing"""
        data = request.json
        result = pricing_service.create_volume_discount_pricing(
            customer_id=data.get("customer_id"),
            base_unit_price=data.get("base_unit_price"),
            metric_name=data.get("metric_name"),
            discount_brackets=data.get("discount_brackets", []),
            billing_cycle=data.get("billing_cycle", "monthly"),
        )
        return response(result, 201, "Volume discount created")
    
    @tier_bp.route("/pricing/calculate", methods=["POST"])
    def calculate_usage_charge():
        """Calculate charge for given usage"""
        data = request.json
        result = pricing_service.calculate_usage_charge(
            customer_id=data.get("customer_id"),
            model_id=data.get("model_id"),
            usage_amount=data.get("usage_amount"),
        )
        return response(result, 200)
    
    @tier_bp.route("/<customer_id>/discounts", methods=["POST"])
    def add_discount():
        """Add custom discount for customer"""
        data = request.json
        result = pricing_service.add_custom_discount(
            customer_id=data.get("customer_id"),
            discount_percent=data.get("discount_percent"),
            reason=data.get("reason"),
            expiration_date=data.get("expiration_date"),
        )
        return response(result, 201, "Discount added")
    
    @tier_bp.route("/pricing/invoice", methods=["POST"])
    def create_usage_invoice():
        """Create invoice based on usage"""
        data = request.json
        result = pricing_service.create_invoice_from_usage(
            customer_id=data.get("customer_id"),
            billing_period_start=data.get("billing_period_start"),
            billing_period_end=data.get("billing_period_end"),
            usage_by_model=data.get("usage_by_model", {}),
        )
        return response(result, 201, "Invoice created")
    
    # ============================================================================
    # ANALYTICS ENDPOINTS (4 endpoints)
    # ============================================================================
    
    @tier_bp.route("/analytics/tier-distribution", methods=["GET"])
    def get_tier_analytics():
        """Get tier distribution analytics"""
        result = tier_service.get_tier_analytics()
        return response(result, 200)
    
    @tier_bp.route("/analytics/quota-usage", methods=["GET"])
    def get_quota_analytics():
        """Get quota usage analytics"""
        result = quota_service.get_quota_analytics()
        return response(result, 200)
    
    @tier_bp.route("/analytics/pricing", methods=["GET"])
    def get_pricing_analytics():
        """Get pricing model analytics"""
        result = pricing_service.get_pricing_analytics()
        return response(result, 200)
    
    @tier_bp.route("/<customer_id>/tier-history", methods=["GET"])
    def get_transition_history(customer_id):
        """Get tier transition history for customer"""
        limit = request.args.get("limit", 10, type=int)
        result = tier_service.get_transition_history(customer_id, limit)
        return response(result, 200)
    
    return tier_bp
