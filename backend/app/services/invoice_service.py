"""
Invoice Service - Generate, manage, and export invoices with PDF support
Handles invoice creation, PDF generation, payment tracking, and history
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum

Base = declarative_base()


class InvoiceStatus(str, Enum):
    """Invoice status enumeration"""
    DRAFT = "draft"
    ISSUED = "issued"
    SENT = "sent"
    VIEWED = "viewed"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class InvoiceTemplate(str, Enum):
    """Available invoice templates"""
    STANDARD = "standard"
    MINIMAL = "minimal"
    DETAILED = "detailed"
    PROFESSIONAL = "professional"


class InvoiceModel(Base):
    """SQLAlchemy model for invoices"""
    __tablename__ = "invoices"
    
    id = Column(String(36), primary_key=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"))
    agent_id = Column(String(36), ForeignKey("agents.id"))
    invoice_number = Column(String(50), unique=True)
    amount = Column(Float)
    currency = Column(String(3), default="USD")
    status = Column(String(20), default=InvoiceStatus.DRAFT.value)
    due_date = Column(DateTime)
    issued_date = Column(DateTime, default=datetime.utcnow)
    paid_date = Column(DateTime, nullable=True)
    amount_paid = Column(Float, default=0.0)
    payment_method = Column(String(50), nullable=True)
    template = Column(String(20), default=InvoiceTemplate.STANDARD.value)
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InvoiceService:
    """
    Service for managing invoices, PDF generation, and payment tracking.
    Provides comprehensive invoicing capabilities for subscription billing.
    """
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize invoice service"""
        self.db = db
        self.invoices = {}  # In-memory storage for demo
        self.invoice_counter = 1000
        self.templates = {
            InvoiceTemplate.STANDARD: self._template_standard,
            InvoiceTemplate.MINIMAL: self._template_minimal,
            InvoiceTemplate.DETAILED: self._template_detailed,
            InvoiceTemplate.PROFESSIONAL: self._template_professional,
        }
    
    def create_invoice(
        self,
        organization_id: str,
        agent_id: str,
        amount: float,
        currency: str = "USD",
        due_days: int = 30,
        description: str = "",
        custom_line_items: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Create a new invoice.
        
        Args:
            organization_id: Organization creating invoice
            agent_id: Agent being billed
            amount: Invoice amount
            currency: Currency code (USD, EUR, GBP, etc.)
            due_days: Days until invoice is due
            description: Invoice description
            custom_line_items: Custom line items (name, qty, unit_price)
        
        Returns:
            Invoice details dictionary
        """
        self.invoice_counter += 1
        invoice_id = f"inv_{self.invoice_counter}"
        invoice_number = f"INV-{self.invoice_counter}"
        
        due_date = datetime.utcnow() + timedelta(days=due_days)
        
        invoice = {
            "id": invoice_id,
            "invoice_number": invoice_number,
            "organization_id": organization_id,
            "agent_id": agent_id,
            "amount": amount,
            "currency": currency,
            "status": InvoiceStatus.DRAFT.value,
            "issued_date": datetime.utcnow().isoformat(),
            "due_date": due_date.isoformat(),
            "amount_paid": 0.0,
            "payment_method": None,
            "description": description,
            "line_items": custom_line_items or [
                {"name": "Service Fee", "quantity": 1, "unit_price": amount, "total": amount}
            ],
            "notes": "",
            "created_at": datetime.utcnow().isoformat(),
        }
        
        self.invoices[invoice_id] = invoice
        return invoice
    
    def issue_invoice(self, invoice_id: str, notes: str = "") -> Dict:
        """
        Issue an invoice (change status to ISSUED).
        Marks invoice as officially issued and sends to customer.
        
        Args:
            invoice_id: Invoice ID to issue
            notes: Additional notes
        
        Returns:
            Updated invoice
        """
        if invoice_id not in self.invoices:
            raise ValueError(f"Invoice {invoice_id} not found")
        
        invoice = self.invoices[invoice_id]
        invoice["status"] = InvoiceStatus.ISSUED.value
        invoice["issued_date"] = datetime.utcnow().isoformat()
        if notes:
            invoice["notes"] = notes
        invoice["updated_at"] = datetime.utcnow().isoformat()
        
        return invoice
    
    def record_payment(
        self,
        invoice_id: str,
        amount_paid: float,
        payment_method: str = "credit_card",
        transaction_id: str = "",
    ) -> Dict:
        """
        Record a payment for an invoice.
        Updates payment status and marks as paid if full payment received.
        
        Args:
            invoice_id: Invoice ID
            amount_paid: Amount paid
            payment_method: Payment method (credit_card, bank_transfer, etc.)
            transaction_id: Payment processor transaction ID
        
        Returns:
            Updated invoice with payment info
        """
        if invoice_id not in self.invoices:
            raise ValueError(f"Invoice {invoice_id} not found")
        
        invoice = self.invoices[invoice_id]
        total_paid = invoice.get("amount_paid", 0) + amount_paid
        invoice["amount_paid"] = total_paid
        invoice["payment_method"] = payment_method
        invoice["transaction_id"] = transaction_id
        
        # Update status based on payment
        if total_paid >= invoice["amount"]:
            invoice["status"] = InvoiceStatus.PAID.value
            invoice["paid_date"] = datetime.utcnow().isoformat()
        elif total_paid > 0:
            invoice["status"] = InvoiceStatus.PARTIALLY_PAID.value
        
        invoice["updated_at"] = datetime.utcnow().isoformat()
        return invoice
    
    def generate_pdf(
        self,
        invoice_id: str,
        template: InvoiceTemplate = InvoiceTemplate.STANDARD,
        include_payment_stub: bool = True,
    ) -> Dict:
        """
        Generate PDF representation of invoice.
        Creates printable/downloadable invoice with optional payment stub.
        
        Args:
            invoice_id: Invoice ID
            template: Template to use for PDF
            include_payment_stub: Include payment stub section
        
        Returns:
            PDF metadata and binary content reference
        """
        if invoice_id not in self.invoices:
            raise ValueError(f"Invoice {invoice_id} not found")
        
        invoice = self.invoices[invoice_id]
        
        # Select template renderer
        template_fn = self.templates.get(template, self._template_standard)
        
        # Generate PDF content (in practice, use reportlab or similar)
        pdf_content = template_fn(invoice)
        
        return {
            "pdf_id": f"pdf_{invoice_id}",
            "invoice_id": invoice_id,
            "invoice_number": invoice["invoice_number"],
            "template": template.value,
            "file_size": len(pdf_content) * 8,  # Rough estimate in bits
            "generated_at": datetime.utcnow().isoformat(),
            "content_preview": pdf_content[:200],  # First 200 chars preview
            "download_url": f"/invoices/{invoice_id}/download-pdf",
        }
    
    def apply_template(
        self,
        invoice_id: str,
        template: InvoiceTemplate,
        customizations: Optional[Dict] = None,
    ) -> Dict:
        """
        Apply template to invoice with optional customizations.
        Updates invoice appearance and formatting.
        
        Args:
            invoice_id: Invoice ID
            template: Template to apply
            customizations: Custom colors, fonts, logos
        
        Returns:
            Updated invoice with template applied
        """
        if invoice_id not in self.invoices:
            raise ValueError(f"Invoice {invoice_id} not found")
        
        invoice = self.invoices[invoice_id]
        invoice["template"] = template.value
        
        if customizations:
            invoice["customizations"] = customizations
        
        invoice["updated_at"] = datetime.utcnow().isoformat()
        return invoice
    
    def get_invoice(self, invoice_id: str) -> Dict:
        """
        Retrieve invoice details.
        
        Args:
            invoice_id: Invoice ID
        
        Returns:
            Invoice data
        """
        if invoice_id not in self.invoices:
            raise ValueError(f"Invoice {invoice_id} not found")
        return self.invoices[invoice_id]
    
    def get_invoice_history(
        self,
        organization_id: str,
        agent_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """
        Get invoice history for organization or agent.
        Supports filtering by status and date range.
        
        Args:
            organization_id: Organization ID
            agent_id: Optional agent ID filter
            status_filter: Optional status filter
            limit: Maximum results
        
        Returns:
            List of invoices matching criteria
        """
        results = []
        for invoice_id, invoice in self.invoices.items():
            if invoice["organization_id"] != organization_id:
                continue
            if agent_id and invoice["agent_id"] != agent_id:
                continue
            if status_filter and invoice["status"] != status_filter:
                continue
            results.append(invoice)
        
        # Sort by date descending
        results.sort(key=lambda x: x["issued_date"], reverse=True)
        return results[:limit]
    
    def track_payments(
        self,
        organization_id: str,
        date_range_days: int = 30,
    ) -> Dict:
        """
        Track payment metrics for organization.
        Calculates collection rate, average payment time, overdue amounts.
        
        Args:
            organization_id: Organization ID
            date_range_days: Days to analyze
        
        Returns:
            Payment tracking metrics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=date_range_days)
        
        total_invoiced = 0.0
        total_paid = 0.0
        total_overdue = 0.0
        payment_times = []
        invoices_count = 0
        paid_count = 0
        
        for invoice in self.invoices.values():
            if invoice["organization_id"] != organization_id:
                continue
            
            issued = datetime.fromisoformat(invoice["issued_date"])
            if issued < cutoff_date:
                continue
            
            invoices_count += 1
            total_invoiced += invoice["amount"]
            total_paid += invoice.get("amount_paid", 0)
            
            # Track overdue invoices
            if invoice["status"] == InvoiceStatus.OVERDUE.value:
                total_overdue += invoice["amount"] - invoice.get("amount_paid", 0)
            
            # Track payment time
            if invoice.get("paid_date"):
                paid = datetime.fromisoformat(invoice["paid_date"])
                days_to_pay = (paid - issued).days
                payment_times.append(days_to_pay)
                paid_count += 1
        
        avg_payment_time = sum(payment_times) / len(payment_times) if payment_times else 0
        collection_rate = (total_paid / total_invoiced * 100) if total_invoiced > 0 else 0
        
        return {
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "collection_rate": collection_rate,
            "total_overdue": total_overdue,
            "average_payment_days": avg_payment_time,
            "invoices_issued": invoices_count,
            "invoices_paid": paid_count,
            "payment_methods": self._aggregate_payment_methods(organization_id),
        }
    
    def _aggregate_payment_methods(self, organization_id: str) -> Dict[str, int]:
        """Aggregate payment methods used by organization"""
        methods = {}
        for invoice in self.invoices.values():
            if invoice["organization_id"] == organization_id and invoice.get("payment_method"):
                method = invoice["payment_method"]
                methods[method] = methods.get(method, 0) + 1
        return methods
    
    # Template renderers
    def _template_standard(self, invoice: Dict) -> str:
        """Standard invoice template"""
        return f"""
        INVOICE
        Invoice #: {invoice['invoice_number']}
        Date: {invoice['issued_date']}
        Due: {invoice['due_date']}
        
        Amount: {invoice['currency']} {invoice['amount']:.2f}
        Status: {invoice['status']}
        Paid: {invoice.get('amount_paid', 0):.2f}
        """
    
    def _template_minimal(self, invoice: Dict) -> str:
        """Minimal invoice template"""
        return f"{invoice['invoice_number']} | {invoice['currency']} {invoice['amount']:.2f} | {invoice['status']}"
    
    def _template_detailed(self, invoice: Dict) -> str:
        """Detailed invoice template with line items"""
        lines = "\n".join([f"  {item['name']}: {item['quantity']} x {item['unit_price']}" 
                          for item in invoice.get('line_items', [])])
        return f"""
        DETAILED INVOICE
        Invoice: {invoice['invoice_number']}
        Organization: {invoice['organization_id']}
        Agent: {invoice['agent_id']}
        
        LINE ITEMS:
        {lines}
        
        TOTAL: {invoice['currency']} {invoice['amount']:.2f}
        PAID: {invoice['currency']} {invoice.get('amount_paid', 0):.2f}
        BALANCE: {invoice['currency']} {invoice['amount'] - invoice.get('amount_paid', 0):.2f}
        
        Due: {invoice['due_date']}
        Status: {invoice['status']}
        """
    
    def _template_professional(self, invoice: Dict) -> str:
        """Professional invoice template with company branding"""
        return f"""
        ╔════════════════════════════════════════╗
        ║          PROFESSIONAL INVOICE          ║
        ╚════════════════════════════════════════╝
        
        Invoice #: {invoice['invoice_number']}
        Issued: {invoice['issued_date']}
        Due: {invoice['due_date']}
        
        Bill To: {invoice['organization_id']}
        Service: Agent Marketplace Services
        
        ─────────────────────────────────────────
        Description: {invoice.get('description', 'Professional Services')}
        Amount: {invoice['currency']} {invoice['amount']:.2f}
        ─────────────────────────────────────────
        
        Amount Paid: {invoice['currency']} {invoice.get('amount_paid', 0):.2f}
        Balance Due: {invoice['currency']} {invoice['amount'] - invoice.get('amount_paid', 0):.2f}
        
        Status: {invoice['status'].upper()}
        Payment Method: {invoice.get('payment_method', 'Not Received')}
        
        Thank you for your business!
        """
