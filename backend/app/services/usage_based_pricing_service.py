"""
Usage-Based Pricing Service - Metered billing and flexible pricing models
Handles usage-based pricing, volume discounts, and custom pricing rules
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum


class PricingModel(str, Enum):
    """Types of pricing models"""
    FLAT_RATE = "flat_rate"
    PER_UNIT = "per_unit"
    TIERED = "tiered"
    VOLUME_DISCOUNT = "volume_discount"
    SEAT_BASED = "seat_based"
    HYBRID = "hybrid"


class UsageBasedPricingService:
    """
    Service for flexible pricing models including usage-based billing,
    volume discounts, and custom pricing rules.
    """
    
    def __init__(self):
        """Initialize usage-based pricing service"""
        self.pricing_models = {}
        self.usage_charges = {}
        self.discount_rules = {}
        self.billing_periods = {}
        self.custom_pricing = {}
    
    def create_metered_pricing(
        self,
        customer_id: str,
        metric_name: str,
        unit_price: float,
        billing_cycle: str = "monthly",
        minimum_charge: float = 0,
        maximum_charge: Optional[float] = None,
    ) -> Dict:
        """
        Create metered/usage-based pricing for a metric.
        
        Args:
            customer_id: Customer ID
            metric_name: Metric being charged (e.g., "api_calls", "executions")
            unit_price: Price per unit
            billing_cycle: How often billed
            minimum_charge: Minimum monthly charge
            maximum_charge: Optional cap on charges
        
        Returns:
            Metered pricing configuration
        """
        model_id = f"pricing_{datetime.utcnow().timestamp()}"
        
        pricing = {
            "model_id": model_id,
            "customer_id": customer_id,
            "pricing_model": PricingModel.PER_UNIT.value,
            "metric_name": metric_name,
            "unit_price": unit_price,
            "billing_cycle": billing_cycle,
            "minimum_charge": minimum_charge,
            "maximum_charge": maximum_charge,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active",
        }
        
        self.pricing_models[model_id] = pricing
        
        return pricing
    
    def create_tiered_pricing(
        self,
        customer_id: str,
        metric_name: str,
        tiers: List[Dict],
        billing_cycle: str = "monthly",
    ) -> Dict:
        """
        Create tiered pricing with volume breakpoints.
        
        Args:
            customer_id: Customer ID
            metric_name: Metric being charged
            tiers: List of tier definitions
                  [{
                    "unit_min": 0,
                    "unit_max": 1000,
                    "unit_price": 0.50
                  }, ...]
            billing_cycle: How often billed
        
        Returns:
            Tiered pricing configuration
        """
        # Validate tiers
        for i, tier in enumerate(tiers):
            if i > 0:
                if tier["unit_min"] != tiers[i-1]["unit_max"]:
                    return {"status": "error", "message": "Tiers must be contiguous"}
        
        model_id = f"pricing_{datetime.utcnow().timestamp()}"
        
        pricing = {
            "model_id": model_id,
            "customer_id": customer_id,
            "pricing_model": PricingModel.TIERED.value,
            "metric_name": metric_name,
            "tiers": tiers,
            "billing_cycle": billing_cycle,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active",
        }
        
        self.pricing_models[model_id] = pricing
        
        return pricing
    
    def create_volume_discount_pricing(
        self,
        customer_id: str,
        base_unit_price: float,
        metric_name: str,
        discount_brackets: List[Dict],
        billing_cycle: str = "monthly",
    ) -> Dict:
        """
        Create volume discount pricing structure.
        
        Args:
            customer_id: Customer ID
            base_unit_price: Base price per unit
            metric_name: Metric being charged
            discount_brackets: List of discount levels
                              [{
                                "unit_min": 0,
                                "unit_max": 10000,
                                "discount_percent": 0
                              }, ...]
            billing_cycle: How often billed
        
        Returns:
            Volume discount pricing configuration
        """
        model_id = f"pricing_{datetime.utcnow().timestamp()}"
        
        pricing = {
            "model_id": model_id,
            "customer_id": customer_id,
            "pricing_model": PricingModel.VOLUME_DISCOUNT.value,
            "metric_name": metric_name,
            "base_unit_price": base_unit_price,
            "discount_brackets": discount_brackets,
            "billing_cycle": billing_cycle,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active",
        }
        
        self.pricing_models[model_id] = pricing
        
        return pricing
    
    def create_seat_based_pricing(
        self,
        customer_id: str,
        price_per_seat: float,
        minimum_seats: int = 1,
        billing_cycle: str = "monthly",
    ) -> Dict:
        """
        Create seat-based pricing (per user/agent/team).
        
        Args:
            customer_id: Customer ID
            price_per_seat: Cost per seat
            minimum_seats: Minimum commitment
            billing_cycle: How often billed
        
        Returns:
            Seat-based pricing configuration
        """
        model_id = f"pricing_{datetime.utcnow().timestamp()}"
        
        pricing = {
            "model_id": model_id,
            "customer_id": customer_id,
            "pricing_model": PricingModel.SEAT_BASED.value,
            "price_per_seat": price_per_seat,
            "minimum_seats": minimum_seats,
            "current_seats": minimum_seats,
            "billing_cycle": billing_cycle,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active",
        }
        
        self.pricing_models[model_id] = pricing
        
        return pricing
    
    def calculate_usage_charge(
        self,
        customer_id: str,
        model_id: str,
        usage_amount: float,
    ) -> Dict:
        """
        Calculate charge for given usage amount.
        
        Args:
            customer_id: Customer ID
            model_id: Pricing model ID
            usage_amount: Amount of metric used
        
        Returns:
            Calculated charge
        """
        model = self.pricing_models.get(model_id)
        if not model:
            return {"status": "error", "message": "Model not found"}
        
        pricing_type = model["pricing_model"]
        
        if pricing_type == PricingModel.PER_UNIT.value:
            charge = self._calculate_per_unit_charge(model, usage_amount)
        
        elif pricing_type == PricingModel.TIERED.value:
            charge = self._calculate_tiered_charge(model, usage_amount)
        
        elif pricing_type == PricingModel.VOLUME_DISCOUNT.value:
            charge = self._calculate_volume_discount_charge(model, usage_amount)
        
        elif pricing_type == PricingModel.SEAT_BASED.value:
            charge = self._calculate_seat_based_charge(model)
        
        else:
            charge = {"status": "error", "message": "Unknown pricing model"}
        
        return charge
    
    def _calculate_per_unit_charge(self, model: Dict, usage: float) -> Dict:
        """Calculate per-unit pricing charge"""
        unit_price = model["unit_price"]
        charge = usage * unit_price
        
        # Apply minimum
        if charge < model.get("minimum_charge", 0):
            charge = model["minimum_charge"]
        
        # Apply maximum
        if model.get("maximum_charge") and charge > model["maximum_charge"]:
            charge = model["maximum_charge"]
        
        return {
            "model_type": PricingModel.PER_UNIT.value,
            "usage_amount": usage,
            "unit_price": unit_price,
            "subtotal": round(usage * unit_price, 2),
            "minimum_charge": model.get("minimum_charge", 0),
            "maximum_charge": model.get("maximum_charge"),
            "total_charge": round(charge, 2),
            "calculated_at": datetime.utcnow().isoformat(),
        }
    
    def _calculate_tiered_charge(self, model: Dict, usage: float) -> Dict:
        """Calculate tiered pricing charge"""
        tiers = model["tiers"]
        total_charge = 0
        tier_breakdown = []
        
        remaining_usage = usage
        
        for tier in tiers:
            if remaining_usage <= 0:
                break
            
            tier_min = tier["unit_min"]
            tier_max = tier["unit_max"]
            tier_price = tier["unit_price"]
            
            # How much of this tier is used
            units_in_tier = min(remaining_usage, tier_max - tier_min)
            tier_charge = units_in_tier * tier_price
            
            total_charge += tier_charge
            
            tier_breakdown.append({
                "tier_min": tier_min,
                "tier_max": tier_max,
                "units_used": units_in_tier,
                "unit_price": tier_price,
                "tier_charge": round(tier_charge, 2),
            })
            
            remaining_usage -= units_in_tier
        
        return {
            "model_type": PricingModel.TIERED.value,
            "usage_amount": usage,
            "tier_breakdown": tier_breakdown,
            "total_charge": round(total_charge, 2),
            "calculated_at": datetime.utcnow().isoformat(),
        }
    
    def _calculate_volume_discount_charge(self, model: Dict, usage: float) -> Dict:
        """Calculate volume discount pricing charge"""
        base_price = model["base_unit_price"]
        brackets = model["discount_brackets"]
        
        # Find applicable discount
        applicable_discount = 0
        for bracket in brackets:
            if bracket["unit_min"] <= usage <= bracket["unit_max"]:
                applicable_discount = bracket["discount_percent"]
                break
        
        # Calculate charge
        base_charge = usage * base_price
        discount_amount = base_charge * (applicable_discount / 100)
        final_charge = base_charge - discount_amount
        
        return {
            "model_type": PricingModel.VOLUME_DISCOUNT.value,
            "usage_amount": usage,
            "base_unit_price": base_price,
            "base_charge": round(base_charge, 2),
            "discount_percent": applicable_discount,
            "discount_amount": round(discount_amount, 2),
            "final_charge": round(final_charge, 2),
            "calculated_at": datetime.utcnow().isoformat(),
        }
    
    def _calculate_seat_based_charge(self, model: Dict) -> Dict:
        """Calculate seat-based pricing charge"""
        seats = model["current_seats"]
        price_per_seat = model["price_per_seat"]
        
        total_charge = seats * price_per_seat
        
        return {
            "model_type": PricingModel.SEAT_BASED.value,
            "seats": seats,
            "price_per_seat": price_per_seat,
            "total_charge": round(total_charge, 2),
            "calculated_at": datetime.utcnow().isoformat(),
        }
    
    def add_custom_discount(
        self,
        customer_id: str,
        discount_percent: float,
        reason: str,
        expiration_date: Optional[str] = None,
    ) -> Dict:
        """
        Add custom discount for customer.
        
        Args:
            customer_id: Customer ID
            discount_percent: Discount percentage (0-100)
            reason: Reason for discount
            expiration_date: When discount expires
        
        Returns:
            Discount configuration
        """
        if customer_id not in self.discount_rules:
            self.discount_rules[customer_id] = []
        
        discount = {
            "discount_id": f"discount_{datetime.utcnow().timestamp()}",
            "customer_id": customer_id,
            "discount_percent": discount_percent,
            "reason": reason,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expiration_date,
            "status": "active",
        }
        
        self.discount_rules[customer_id].append(discount)
        
        return discount
    
    def get_effective_discount(self, customer_id: str) -> float:
        """Get total effective discount for customer"""
        discounts = self.discount_rules.get(customer_id, [])
        
        total_discount = 0
        
        for discount in discounts:
            if discount["status"] == "active":
                # Check expiration
                if discount.get("expires_at"):
                    expiration = datetime.fromisoformat(discount["expires_at"])
                    if datetime.utcnow() > expiration:
                        discount["status"] = "expired"
                        continue
                
                total_discount += discount["discount_percent"]
        
        return min(100, total_discount)  # Cap at 100%
    
    def apply_discount_to_charge(
        self,
        customer_id: str,
        base_charge: float,
    ) -> Dict:
        """
        Apply customer discounts to a charge.
        
        Args:
            customer_id: Customer ID
            base_charge: Base charge amount
        
        Returns:
            Charge with discount applied
        """
        discount_percent = self.get_effective_discount(customer_id)
        discount_amount = base_charge * (discount_percent / 100)
        final_charge = base_charge - discount_amount
        
        return {
            "customer_id": customer_id,
            "base_charge": round(base_charge, 2),
            "discount_percent": discount_percent,
            "discount_amount": round(discount_amount, 2),
            "final_charge": round(final_charge, 2),
        }
    
    def adjust_seat_count(
        self,
        model_id: str,
        new_seat_count: int,
        effective_date: Optional[str] = None,
    ) -> Dict:
        """
        Adjust seat count for seat-based pricing.
        
        Args:
            model_id: Pricing model ID
            new_seat_count: New number of seats
            effective_date: When adjustment takes effect
        
        Returns:
            Seat adjustment confirmation
        """
        model = self.pricing_models.get(model_id)
        if not model or model["pricing_model"] != PricingModel.SEAT_BASED.value:
            return {"status": "error"}
        
        old_seats = model["current_seats"]
        model["current_seats"] = new_seat_count
        
        # Calculate proration if mid-month
        old_charge = old_seats * model["price_per_seat"]
        new_charge = new_seat_count * model["price_per_seat"]
        
        return {
            "model_id": model_id,
            "old_seats": old_seats,
            "new_seats": new_seat_count,
            "seat_change": new_seat_count - old_seats,
            "old_monthly_charge": round(old_charge, 2),
            "new_monthly_charge": round(new_charge, 2),
            "monthly_change": round(new_charge - old_charge, 2),
            "effective_date": effective_date or datetime.utcnow().isoformat(),
        }
    
    def create_invoice_from_usage(
        self,
        customer_id: str,
        billing_period_start: str,
        billing_period_end: str,
        usage_by_model: Dict[str, float],
    ) -> Dict:
        """
        Create invoice based on usage in billing period.
        
        Args:
            customer_id: Customer ID
            billing_period_start: Start date
            billing_period_end: End date
            usage_by_model: Dict of model_id -> usage_amount
        
        Returns:
            Invoice with itemized charges
        """
        invoice_id = f"invoice_{datetime.utcnow().timestamp()}"
        line_items = []
        total_charge = 0
        
        for model_id, usage in usage_by_model.items():
            charge = self.calculate_usage_charge(customer_id, model_id, usage)
            
            if "total_charge" in charge:
                line_items.append({
                    "model_id": model_id,
                    "usage": usage,
                    "charge": charge,
                })
                total_charge += charge["total_charge"]
        
        # Apply customer discounts
        discount_info = self.apply_discount_to_charge(customer_id, total_charge)
        
        invoice = {
            "invoice_id": invoice_id,
            "customer_id": customer_id,
            "billing_period": {
                "start": billing_period_start,
                "end": billing_period_end,
            },
            "line_items": line_items,
            "subtotal": round(total_charge, 2),
            "discount_percent": discount_info["discount_percent"],
            "discount_amount": discount_info["discount_amount"],
            "total": discount_info["final_charge"],
            "created_at": datetime.utcnow().isoformat(),
        }
        
        return invoice
    
    def get_pricing_analytics(self, customer_id: Optional[str] = None) -> Dict:
        """
        Get analytics on pricing models and usage.
        
        Args:
            customer_id: Optional specific customer
        
        Returns:
            Pricing analytics
        """
        if customer_id:
            models = [m for m in self.pricing_models.values() if m["customer_id"] == customer_id]
        else:
            models = list(self.pricing_models.values())
        
        model_distribution = {}
        for model in models:
            model_type = model["pricing_model"]
            model_distribution[model_type] = model_distribution.get(model_type, 0) + 1
        
        return {
            "total_pricing_models": len(models),
            "model_distribution": model_distribution,
            "total_customers_with_usage_pricing": len(set(m["customer_id"] for m in models)),
            "active_models": len([m for m in models if m["status"] == "active"]),
            "average_discount": self._calculate_average_discount(),
        }
    
    def _calculate_average_discount(self) -> float:
        """Calculate average discount across all customers"""
        if not self.discount_rules:
            return 0
        
        total_discount = 0
        count = 0
        
        for discounts in self.discount_rules.values():
            active_discounts = [d for d in discounts if d["status"] == "active"]
            if active_discounts:
                total_discount += sum(d["discount_percent"] for d in active_discounts)
                count += len(active_discounts)
        
        return (total_discount / count) if count > 0 else 0
