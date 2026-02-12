"""
Payment Monetization API Routes - All endpoints for invoicing, tax, currency, dunning
Provides REST API for invoice management, tax reporting, currency conversion, payment recovery
"""

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from typing import Optional, List, Dict
from datetime import datetime

# These would be injected from main.py
invoice_service = None
tax_service = None
currency_service = None
dunning_service = None

router = APIRouter(prefix="/api/monetization", tags=["Monetization"])


def set_monetization_services(invoices, taxes, currencies, dunning):
    """Inject services from main.py"""
    global invoice_service, tax_service, currency_service, dunning_service
    invoice_service = invoices
    tax_service = taxes
    currency_service = currencies
    dunning_service = dunning


def get_user_id(x_user_id: str = Header(...)) -> str:
    """Extract user ID from header"""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="X-User-ID header required")
    return x_user_id


# ======================== INVOICE ENDPOINTS (6) ========================

@router.post("/invoices/create")
async def create_invoice(
    user_id: str = Depends(get_user_id),
    organization_id: str = Query(...),
    agent_id: str = Query(...),
    amount: float = Query(...),
    currency: str = Query(default="USD"),
    due_days: int = Query(default=30),
    description: str = Query(default=""),
):
    """Create new invoice"""
    invoice = invoice_service.create_invoice(
        organization_id, agent_id, amount, currency, due_days, description
    )
    return {"status": "success", "invoice": invoice}


@router.post("/invoices/{invoice_id}/issue")
async def issue_invoice(
    invoice_id: str,
    user_id: str = Depends(get_user_id),
    notes: str = Query(default=""),
):
    """Issue invoice (change to ISSUED status)"""
    invoice = invoice_service.issue_invoice(invoice_id, notes)
    return {"status": "success", "invoice": invoice}


@router.post("/invoices/{invoice_id}/record-payment")
async def record_payment(
    invoice_id: str,
    user_id: str = Depends(get_user_id),
    amount_paid: float = Query(...),
    payment_method: str = Query(default="credit_card"),
    transaction_id: str = Query(default=""),
):
    """Record payment for invoice"""
    invoice = invoice_service.record_payment(
        invoice_id, amount_paid, payment_method, transaction_id
    )
    return {"status": "success", "invoice": invoice}


@router.get("/invoices/{invoice_id}/pdf")
async def generate_invoice_pdf(
    invoice_id: str,
    user_id: str = Depends(get_user_id),
    template: str = Query(default="standard"),
):
    """Generate PDF for invoice"""
    pdf = invoice_service.generate_pdf(invoice_id, template)
    return {"status": "success", "pdf": pdf}


@router.get("/invoices/history")
async def get_invoice_history(
    user_id: str = Depends(get_user_id),
    organization_id: str = Query(...),
    agent_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50),
):
    """Get invoice history for organization"""
    invoices = invoice_service.get_invoice_history(
        organization_id, agent_id, status, limit
    )
    return {"status": "success", "invoices": invoices, "count": len(invoices)}


@router.get("/invoices/track-payments")
async def track_payments(
    user_id: str = Depends(get_user_id),
    organization_id: str = Query(...),
    days: int = Query(default=30),
):
    """Track payment metrics for organization"""
    metrics = invoice_service.track_payments(organization_id, days)
    return {"status": "success", "metrics": metrics}


# ======================== TAX ENDPOINTS (6) ========================

@router.post("/tax/1099-form")
async def generate_1099(
    user_id: str = Depends(get_user_id),
    vendor_id: str = Query(...),
    tax_year: int = Query(...),
    income_services: float = Query(default=0),
    income_other: float = Query(default=0),
):
    """Generate 1099 tax form"""
    doc = tax_service.generate_1099(
        vendor_id,
        tax_year,
        {"services": income_services, "other_income": income_other},
        {"name": "Vendor", "ssn": "***-**-****"},
    )
    return {"status": "success", "document": doc}


@router.post("/tax/receipt")
async def create_receipt(
    user_id: str = Depends(get_user_id),
    organization_id: str = Query(...),
    amount: float = Query(...),
    category: str = Query(...),
    description: str = Query(...),
):
    """Create tax receipt for deduction"""
    receipt = tax_service.create_tax_receipt(
        organization_id, "expense", amount, category, description
    )
    return {"status": "success", "receipt": receipt}


@router.post("/tax/calculate-taxable-income")
async def calculate_taxable_income(
    user_id: str = Depends(get_user_id),
    vendor_id: str = Query(...),
    tax_year: int = Query(...),
    gross_income: float = Query(...),
):
    """Calculate taxable income with deductions"""
    calculation = tax_service.calculate_taxable_income(
        vendor_id, tax_year, gross_income
    )
    return {"status": "success", "calculation": calculation}


@router.get("/tax/summary")
async def get_tax_summary(
    user_id: str = Depends(get_user_id),
    vendor_id: str = Query(...),
    tax_year: int = Query(...),
):
    """Get comprehensive tax summary"""
    summary = tax_service.get_tax_summary(vendor_id, tax_year)
    return {"status": "success", "summary": summary}


@router.post("/tax/quarterly-estimate")
async def estimate_quarterly_tax(
    user_id: str = Depends(get_user_id),
    vendor_id: str = Query(...),
    ytd_income: float = Query(...),
    ytd_deductions: float = Query(...),
):
    """Estimate quarterly tax payment"""
    estimate = tax_service.estimate_quarterly_tax(
        vendor_id, ytd_income, ytd_deductions
    )
    return {"status": "success", "estimate": estimate}


@router.get("/tax/deductions")
async def get_deductions_total(
    user_id: str = Depends(get_user_id),
    vendor_id: str = Query(...),
    category: Optional[str] = Query(default=None),
):
    """Get total deductions"""
    total = tax_service.get_deduction_total(vendor_id, category)
    return {"status": "success", "total_deductions": total}


# ======================== CURRENCY ENDPOINTS (5) ========================

@router.post("/currency/convert")
async def convert_currency(
    user_id: str = Depends(get_user_id),
    amount: float = Query(...),
    from_currency: str = Query(...),
    to_currency: str = Query(...),
):
    """Convert amount between currencies"""
    conversion = currency_service.convert_currency(
        amount, from_currency, to_currency
    )
    return {"status": "success", "conversion": conversion}


@router.get("/currency/rates")
async def get_exchange_rates(
    user_id: str = Depends(get_user_id),
    base_currency: str = Query(default="USD"),
    currencies: Optional[List[str]] = Query(default=None),
):
    """Get exchange rates"""
    rates = currency_service.get_exchange_rates(base_currency, currencies)
    return {"status": "success", "rates": rates}


@router.post("/currency/localize-pricing")
async def localize_pricing(
    user_id: str = Depends(get_user_id),
    base_price: float = Query(...),
    target_currency: str = Query(...),
    strategy: str = Query(default="market_adjustment"),
):
    """Get localized price for currency"""
    pricing = currency_service.apply_pricing_localization(
        base_price, target_currency, strategy
    )
    return {"status": "success", "pricing": pricing}


@router.get("/currency/pricing-by-region")
async def get_pricing_by_region(
    user_id: str = Depends(get_user_id),
    base_price: float = Query(...),
    strategy: str = Query(default="market_adjustment"),
):
    """Get prices for all regions"""
    pricing = currency_service.get_pricing_by_region(
        base_price, strategy=strategy
    )
    return {"status": "success", "pricing": pricing}


@router.get("/currency/usage")
async def track_currency_usage(
    user_id: str = Depends(get_user_id),
    organization_id: str = Query(...),
    days: int = Query(default=30),
):
    """Track currency usage metrics"""
    usage = currency_service.track_currency_usage(organization_id, days)
    return {"status": "success", "usage": usage}


# ======================== DUNNING ENDPOINTS (6) ========================

@router.post("/dunning/process-failed-payment")
async def process_failed_payment(
    user_id: str = Depends(get_user_id),
    subscription_id: str = Query(...),
    customer_id: str = Query(...),
    amount: float = Query(...),
    error_code: str = Query(...),
    error_message: str = Query(...),
    customer_email: str = Query(...),
    strategy: str = Query(default="moderate"),
):
    """Process failed payment and initiate recovery"""
    result = dunning_service.process_failed_payment(
        subscription_id, customer_id, amount, "USD", 
        "credit_card", error_code, error_message, customer_email, strategy
    )
    return {"status": "success", "result": result}


@router.get("/dunning/retry-schedule")
async def get_retry_schedule(
    user_id: str = Depends(get_user_id),
    failure_id: str = Query(...),
):
    """Get retry schedule for failed payment"""
    schedule = dunning_service.retry_schedules.get(failure_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Retry schedule not found")
    return {"status": "success", "schedule": schedule}


@router.post("/dunning/send-notifications")
async def send_dunning_notifications(
    user_id: str = Depends(get_user_id),
    failure_ids: List[str] = Query(...),
):
    """Send notifications for failed payments"""
    notifications = dunning_service.send_notifications(failure_ids)
    return {"status": "success", "notifications_sent": len(notifications)}


@router.post("/dunning/mark-recovered")
async def mark_recovered(
    user_id: str = Depends(get_user_id),
    failure_id: str = Query(...),
    transaction_id: str = Query(...),
):
    """Mark failed payment as recovered"""
    result = dunning_service.mark_payment_recovered(failure_id, transaction_id)
    return {"status": "success", "result": result}


@router.post("/dunning/record-retry-attempt")
async def record_retry_attempt(
    user_id: str = Depends(get_user_id),
    failure_id: str = Query(...),
    attempt_number: int = Query(...),
    result: str = Query(...),
    error_code: Optional[str] = Query(default=None),
):
    """Record retry attempt result"""
    attempt = dunning_service.record_retry_attempt(
        failure_id, attempt_number, result, error_code
    )
    return {"status": "success", "attempt": attempt}


@router.get("/dunning/metrics")
async def get_dunning_metrics(
    user_id: str = Depends(get_user_id),
    organization_id: str = Query(...),
    days: int = Query(default=30),
):
    """Get dunning/recovery metrics"""
    metrics = dunning_service.track_dunning_metrics(organization_id, days)
    return {"status": "success", "metrics": metrics}


# ======================== HEALTH ENDPOINT ========================

@router.get("/health")
async def health_check():
    """Check payment monetization module health"""
    services_ready = all([
        invoice_service is not None,
        tax_service is not None,
        currency_service is not None,
        dunning_service is not None,
    ])
    
    return {
        "status": "healthy" if services_ready else "degraded",
        "services": {
            "invoices": invoice_service is not None,
            "tax": tax_service is not None,
            "currency": currency_service is not None,
            "dunning": dunning_service is not None,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
