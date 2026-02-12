"""
Multi-Currency Service - Convert currencies, apply localized pricing, track usage
Handles exchange rates, currency conversion, and multi-currency pricing strategies
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import json

class Currency(str, Enum):
    """Supported currencies"""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    AUD = "AUD"
    CAD = "CAD"
    CHF = "CHF"
    CNY = "CNY"
    INR = "INR"
    MXN = "MXN"


class PricingStrategy(str, Enum):
    """Pricing localization strategies"""
    DIRECT_CONVERSION = "direct_conversion"  # Simple rate conversion
    MARKET_ADJUSTMENT = "market_adjustment"  # Apply local market factors
    PURCHASING_POWER_PARITY = "ppp"  # Adjust for local purchasing power
    FIXED_PRICE = "fixed_price"  # Same price in all currencies


class MultiCurrencyService:
    """
    Service for multi-currency support, exchange rates, and localized pricing.
    Provides currency conversion and intelligent pricing strategies.
    """
    
    def __init__(self):
        """Initialize multi-currency service with exchange rates"""
        self.base_currency = Currency.USD
        
        # Exchange rates relative to USD (as of Feb 7, 2026 - simulated)
        self.exchange_rates = {
            "USD": 1.0,
            "EUR": 0.92,    # €1 = $1.09
            "GBP": 0.79,    # £1 = $1.27
            "JPY": 0.0067,  # ¥1 = $0.0067
            "AUD": 0.66,    # A$1 = $1.52
            "CAD": 0.73,    # C$1 = $1.37
            "CHF": 1.12,    # CHF1 = $0.89
            "CNY": 0.14,    # ¥1 = $0.14
            "INR": 0.012,   # ₹1 = $0.012
            "MXN": 0.058,   # M$1 = $0.058
        }
        
        # Market adjustment factors (pricing multipliers by region)
        self.market_adjustments = {
            "USD": 1.0,
            "EUR": 1.08,    # Europe generally pays more
            "GBP": 1.15,    # UK market premium
            "JPY": 0.95,    # Japan typically more price-sensitive
            "AUD": 0.98,
            "CAD": 1.02,
            "CHF": 1.25,    # Switzerland highest prices
            "CNY": 0.70,    # China price-sensitive
            "INR": 0.50,    # India budget-conscious
            "MXN": 0.80,
        }
        
        # Purchasing power parity adjustments
        self.ppp_adjustments = {
            "USD": 1.0,
            "EUR": 1.05,
            "GBP": 1.10,
            "JPY": 0.85,
            "AUD": 0.92,
            "CAD": 0.95,
            "CHF": 1.40,
            "CNY": 0.40,
            "INR": 0.30,
            "MXN": 0.45,
        }
        
        # Currency formats and symbols
        self.currency_formats = {
            "USD": {"symbol": "$", "position": "before", "decimal_places": 2},
            "EUR": {"symbol": "€", "position": "after", "decimal_places": 2},
            "GBP": {"symbol": "£", "position": "before", "decimal_places": 2},
            "JPY": {"symbol": "¥", "position": "before", "decimal_places": 0},
            "AUD": {"symbol": "A$", "position": "before", "decimal_places": 2},
            "CAD": {"symbol": "C$", "position": "before", "decimal_places": 2},
            "CHF": {"symbol": "CHF", "position": "after", "decimal_places": 2},
            "CNY": {"symbol": "¥", "position": "before", "decimal_places": 2},
            "INR": {"symbol": "₹", "position": "before", "decimal_places": 2},
            "MXN": {"symbol": "M$", "position": "before", "decimal_places": 2},
        }
        
        # Historical rates tracking
        self.rate_history = {}
        self.pricing_usage = {}
        self.conversion_history = {}
        
        # Store current rates with timestamp
        self._update_rate_history()
    
    def convert_currency(
        self,
        amount: float,
        from_currency: str,
        to_currency: str,
        rate_date: Optional[datetime] = None,
    ) -> Dict:
        """
        Convert amount from one currency to another.
        Uses current or historical exchange rates.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            rate_date: Optional date for historical rates
        
        Returns:
            Conversion details with result
        """
        from_curr = from_currency.upper()
        to_curr = to_currency.upper()
        
        if from_curr not in self.exchange_rates:
            raise ValueError(f"Unsupported currency: {from_curr}")
        if to_curr not in self.exchange_rates:
            raise ValueError(f"Unsupported currency: {to_curr}")
        
        # Get conversion rate
        from_rate = self.exchange_rates[from_curr]
        to_rate = self.exchange_rates[to_curr]
        
        # Convert to USD first, then to target
        usd_amount = amount / from_rate if from_rate > 0 else 0
        converted_amount = usd_amount * to_rate
        
        # Calculate conversion fee (0.5% typical)
        conversion_fee = converted_amount * 0.005
        amount_after_fee = converted_amount - conversion_fee
        
        conversion = {
            "transaction_id": f"conv_{len(self.conversion_history) + 1}",
            "original_amount": amount,
            "original_currency": from_curr,
            "converted_amount": round(converted_amount, 2),
            "amount_after_fee": round(amount_after_fee, 2),
            "target_currency": to_curr,
            "exchange_rate": round(to_rate / from_rate, 6),
            "conversion_fee": round(conversion_fee, 2),
            "fee_percentage": 0.5,
            "conversion_date": datetime.utcnow().isoformat(),
        }
        
        # Track conversion
        self.conversion_history[conversion["transaction_id"]] = conversion
        
        return conversion
    
    def get_exchange_rates(
        self,
        base_currency: str = "USD",
        target_currencies: Optional[List[str]] = None,
    ) -> Dict:
        """
        Get current exchange rates for currencies.
        Returns rates relative to specified base currency.
        
        Args:
            base_currency: Base currency for rates
            target_currencies: Optional list of currencies to include
        
        Returns:
            Exchange rates dictionary
        """
        base_curr = base_currency.upper()
        if base_curr not in self.exchange_rates:
            raise ValueError(f"Unsupported base currency: {base_curr}")
        
        base_rate = self.exchange_rates[base_curr]
        
        # Determine which currencies to include
        currencies = target_currencies or list(self.exchange_rates.keys())
        currencies = [c.upper() for c in currencies]
        
        rates = {
            "base_currency": base_curr,
            "timestamp": datetime.utcnow().isoformat(),
            "rates": {}
        }
        
        for currency in currencies:
            if currency not in self.exchange_rates:
                continue
            
            # Convert to base currency
            rate = self.exchange_rates[currency] / base_rate if base_rate > 0 else 0
            rates["rates"][currency] = round(rate, 6)
        
        return rates
    
    def apply_pricing_localization(
        self,
        base_price: float,
        target_currency: str,
        strategy: PricingStrategy = PricingStrategy.MARKET_ADJUSTMENT,
        user_region: Optional[str] = None,
    ) -> Dict:
        """
        Apply localized pricing strategy to base price.
        Adapts pricing based on currency, market, and purchasing power.
        
        Args:
            base_price: Base price in USD
            target_currency: Target currency
            strategy: Pricing strategy to apply
            user_region: Optional region for additional customization
        
        Returns:
            Localized pricing details
        """
        target_curr = target_currency.upper()
        if target_curr not in self.exchange_rates:
            raise ValueError(f"Unsupported currency: {target_curr}")
        
        # Calculate based on strategy
        if strategy == PricingStrategy.DIRECT_CONVERSION:
            localized_price = self._direct_conversion(base_price, target_curr)
        elif strategy == PricingStrategy.MARKET_ADJUSTMENT:
            localized_price = self._market_adjusted(base_price, target_curr)
        elif strategy == PricingStrategy.PURCHASING_POWER_PARITY:
            localized_price = self._purchasing_power_parity(base_price, target_curr)
        else:  # FIXED_PRICE
            localized_price = self.convert_currency(
                base_price, "USD", target_curr
            )["converted_amount"]
        
        # Format currency
        formatted = self._format_currency(localized_price, target_curr)
        
        pricing = {
            "base_price_usd": base_price,
            "target_currency": target_curr,
            "strategy": strategy.value,
            "localized_price": round(localized_price, 2),
            "formatted_price": formatted,
            "exchange_rate": round(self.exchange_rates[target_curr], 6),
            "market_adjustment_factor": self.market_adjustments.get(target_curr, 1.0),
            "price_difference_from_base": round(
                ((localized_price * self.exchange_rates["USD"] / self.exchange_rates[target_curr]) - base_price) / base_price * 100, 2
            ),  # Percentage difference
        }
        
        # Track usage
        self._track_pricing_usage(target_curr, strategy.value)
        
        return pricing
    
    def _direct_conversion(self, base_price: float, target_currency: str) -> float:
        """Simple direct conversion at current rate"""
        conversion = self.convert_currency(base_price, "USD", target_currency)
        return conversion["converted_amount"]
    
    def _market_adjusted(self, base_price: float, target_currency: str) -> float:
        """Apply market adjustment factor"""
        converted = self._direct_conversion(base_price, target_currency)
        adjustment = self.market_adjustments.get(target_currency, 1.0)
        return converted * adjustment
    
    def _purchasing_power_parity(self, base_price: float, target_currency: str) -> float:
        """Apply PPP adjustment for local purchasing power"""
        converted = self._direct_conversion(base_price, target_currency)
        ppp = self.ppp_adjustments.get(target_currency, 1.0)
        return converted * ppp
    
    def _format_currency(self, amount: float, currency: str) -> str:
        """Format amount in currency with proper symbol and decimals"""
        format_info = self.currency_formats.get(currency, {})
        symbol = format_info.get("symbol", currency)
        position = format_info.get("position", "before")
        decimal_places = format_info.get("decimal_places", 2)
        
        formatted_amount = f"{amount:,.{decimal_places}f}"
        
        if position == "before":
            return f"{symbol}{formatted_amount}"
        else:
            return f"{formatted_amount} {symbol}"
    
    def _track_pricing_usage(self, currency: str, strategy: str):
        """Track pricing localization usage"""
        key = f"{currency}_{strategy}"
        self.pricing_usage[key] = self.pricing_usage.get(key, 0) + 1
    
    def _update_rate_history(self):
        """Store current rates in history"""
        timestamp = datetime.utcnow().isoformat()
        self.rate_history[timestamp] = dict(self.exchange_rates)
    
    def get_pricing_by_region(
        self,
        base_price: float,
        regions: Optional[List[str]] = None,
        strategy: PricingStrategy = PricingStrategy.MARKET_ADJUSTMENT,
    ) -> Dict:
        """
        Get localized prices for multiple regions/currencies.
        Useful for pricing tables and global presentations.
        
        Args:
            base_price: Base price in USD
            regions: List of region codes/currencies
            strategy: Pricing strategy to apply
        
        Returns:
            Pricing breakdown by region
        """
        regions = regions or list(self.exchange_rates.keys())
        
        pricing_by_region = {
            "base_price_usd": base_price,
            "strategy": strategy.value,
            "currencies": {}
        }
        
        for currency in regions:
            curr = currency.upper()
            if curr not in self.exchange_rates:
                continue
            
            pricing = self.apply_pricing_localization(
                base_price, curr, strategy
            )
            pricing_by_region["currencies"][curr] = {
                "price": pricing["localized_price"],
                "formatted": pricing["formatted_price"],
                "exchange_rate": pricing["exchange_rate"],
            }
        
        return pricing_by_region
    
    def track_currency_usage(
        self,
        organization_id: str,
        date_range_days: int = 30,
    ) -> Dict:
        """
        Track currency usage metrics for organization.
        Shows which currencies are used and pricing strategies applied.
        
        Args:
            organization_id: Organization ID
            date_range_days: Days to analyze
        
        Returns:
            Currency usage statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=date_range_days)
        
        # Analyze conversion history
        conversions_by_currency = {}
        total_conversions = 0
        total_fees = 0
        
        for conv in self.conversion_history.values():
            conv_date = datetime.fromisoformat(conv["conversion_date"])
            if conv_date < cutoff_date:
                continue
            
            target = conv["target_currency"]
            conversions_by_currency[target] = conversions_by_currency.get(target, 0) + 1
            total_conversions += 1
            total_fees += conv["conversion_fee"]
        
        # Analyze pricing usage
        pricing_by_strategy = {}
        for key, count in self.pricing_usage.items():
            strategy = key.split("_", 1)[1]
            pricing_by_strategy[strategy] = pricing_by_strategy.get(strategy, 0) + count
        
        return {
            "organization_id": organization_id,
            "analysis_period_days": date_range_days,
            "total_conversions": total_conversions,
            "total_conversion_fees": round(total_fees, 2),
            "conversions_by_currency": conversions_by_currency,
            "most_used_currency": max(
                conversions_by_currency, key=conversions_by_currency.get
            ) if conversions_by_currency else None,
            "pricing_strategies_used": pricing_by_strategy,
            "average_conversion_fee": round(
                total_fees / total_conversions, 2
            ) if total_conversions > 0 else 0,
        }
    
    def update_exchange_rate(
        self,
        currency: str,
        new_rate: float,
        source: str = "manual",
    ) -> Dict:
        """
        Update exchange rate for currency.
        Allows manual override or API updates.
        
        Args:
            currency: Currency code
            new_rate: New exchange rate relative to USD
            source: Source of update (manual, api, etc.)
        
        Returns:
            Update confirmation
        """
        curr = currency.upper()
        if curr not in self.exchange_rates:
            raise ValueError(f"Unsupported currency: {curr}")
        
        old_rate = self.exchange_rates[curr]
        self.exchange_rates[curr] = new_rate
        
        # Update history
        self._update_rate_history()
        
        return {
            "currency": curr,
            "old_rate": old_rate,
            "new_rate": new_rate,
            "change_percentage": round(
                ((new_rate - old_rate) / old_rate * 100) if old_rate > 0 else 0, 2
            ),
            "updated_at": datetime.utcnow().isoformat(),
            "source": source,
        }
    
    def get_rate_history(
        self,
        currency: str,
        days: int = 30,
    ) -> List[Dict]:
        """
        Get historical exchange rates for currency.
        Useful for trend analysis and forecasting.
        
        Args:
            currency: Currency code
            days: Number of days of history
        
        Returns:
            List of historical rates
        """
        curr = currency.upper()
        history = []
        
        for timestamp, rates in sorted(self.rate_history.items()):
            if curr in rates:
                history.append({
                    "currency": curr,
                    "rate": rates[curr],
                    "timestamp": timestamp,
                })
        
        # Return last N days
        return history[-days:] if days else history
