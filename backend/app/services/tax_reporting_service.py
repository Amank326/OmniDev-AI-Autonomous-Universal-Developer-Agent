"""
Tax Reporting Service - Generate tax forms (1099s, receipts), calculate taxes
Handles tax document generation, deduction tracking, and tax summary reporting
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TaxDocumentType(str, Enum):
    """Tax document types"""
    FORM_1099_NEC = "1099-nec"  # Non-employee compensation
    FORM_1099_MISC = "1099-misc"  # Miscellaneous income
    FORM_1098_T = "1098-t"  # Education credit
    TAX_RECEIPT = "tax_receipt"  # General receipt
    INVOICE_RECEIPT = "invoice_receipt"


class DeductionCategory(str, Enum):
    """Tax deduction categories"""
    SOFTWARE = "software"
    EQUIPMENT = "equipment"
    SUPPLIES = "supplies"
    UTILITIES = "utilities"
    PROFESSIONAL_FEES = "professional_fees"
    MARKETING = "marketing"
    TRAVEL = "travel"
    MEALS = "meals"
    OTHER = "other"


class TaxModel(Base):
    """SQLAlchemy model for tax records"""
    __tablename__ = "tax_records"
    
    id = Column(String(36), primary_key=True)
    vendor_id = Column(String(36), ForeignKey("vendors.id"))
    tax_year = Column(Integer)
    total_income = Column(Float, default=0.0)
    total_deductions = Column(Float, default=0.0)
    taxable_income = Column(Float, default=0.0)
    tax_rate = Column(Float, default=0.0)
    estimated_tax = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class TaxReportingService:
    """
    Service for tax reporting, form generation, and deduction tracking.
    Provides comprehensive tax compliance and reporting capabilities.
    """
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize tax reporting service"""
        self.db = db
        self.tax_records = {}
        self.documents = {}
        self.receipts = {}
        self.current_year = datetime.now().year
        
        # Standard deduction and tax rates (2024)
        self.standard_deduction = 13850.0  # Single filer
        self.tax_brackets = [
            (11000, 0.10),
            (44725, 0.12),
            (95375, 0.22),
            (182100, 0.24),
            (231250, 0.32),
            (578125, 0.35),
            (float('inf'), 0.37),
        ]
    
    def generate_1099(
        self,
        vendor_id: str,
        tax_year: int,
        income_by_type: Dict[str, float],
        vendor_info: Dict,
    ) -> Dict:
        """
        Generate 1099 tax form for independent contractor.
        Creates 1099-NEC for contract payments or 1099-MISC for other income.
        
        Args:
            vendor_id: Vendor/contractor ID
            tax_year: Tax year for 1099
            income_by_type: Income breakdown by category
            vendor_info: Vendor name, address, SSN, etc.
        
        Returns:
            1099 document details
        """
        doc_id = f"1099_{vendor_id}_{tax_year}"
        
        # Calculate total income
        total_1099_income = sum(income_by_type.values())
        
        # Determine 1099 type (NEC for contract, MISC for other)
        doc_type = (
            TaxDocumentType.FORM_1099_NEC 
            if total_1099_income > 600 
            else TaxDocumentType.TAX_RECEIPT
        )
        
        document = {
            "doc_id": doc_id,
            "type": doc_type.value,
            "vendor_id": vendor_id,
            "tax_year": tax_year,
            "vendor_name": vendor_info.get("name", ""),
            "vendor_ssn": vendor_info.get("ssn", "***-**-****"),
            "vendor_address": vendor_info.get("address", ""),
            "box_1": income_by_type.get("services", 0),  # Non-employee compensation
            "box_2": income_by_type.get("other_income", 0),  # Other income
            "total_payments": total_1099_income,
            "federal_withheld": income_by_type.get("federal_withheld", 0),
            "generated_date": datetime.utcnow().isoformat(),
            "issue_deadline": f"{tax_year + 1}-01-31",  # January 31 of following year
            "filing_deadline": f"{tax_year + 1}-02-28",  # February 28 for IRS
        }
        
        self.documents[doc_id] = document
        return document
    
    def create_tax_receipt(
        self,
        organization_id: str,
        receipt_type: str,
        amount: float,
        category: DeductionCategory,
        description: str,
        date: Optional[datetime] = None,
    ) -> Dict:
        """
        Create tax receipt for deductible expense or income.
        Tracks receipts for tax deduction and audit purposes.
        
        Args:
            organization_id: Organization creating receipt
            receipt_type: Type of receipt (payment, expense, donation)
            amount: Receipt amount
            category: Deduction category
            description: Detailed description
            date: Receipt date
        
        Returns:
            Tax receipt details
        """
        receipt_id = f"receipt_{len(self.receipts) + 1}"
        date = date or datetime.utcnow()
        
        receipt = {
            "receipt_id": receipt_id,
            "organization_id": organization_id,
            "receipt_type": receipt_type,
            "amount": amount,
            "category": category.value,
            "description": description,
            "date": date.isoformat(),
            "tax_year": date.year,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        self.receipts[receipt_id] = receipt
        return receipt
    
    def calculate_taxable_income(
        self,
        vendor_id: str,
        tax_year: int,
        gross_income: float,
        deductions: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Calculate taxable income after deductions.
        Applies standard or itemized deductions, calculates tax liability.
        
        Args:
            vendor_id: Vendor ID
            tax_year: Tax year
            gross_income: Total gross income
            deductions: List of deduction dicts (category, amount)
        
        Returns:
            Tax calculation breakdown
        """
        # Calculate total deductions
        total_deductions = sum(
            d.get("amount", 0) for d in (deductions or [])
        )
        
        # Apply standard deduction if greater
        itemized_deductions = total_deductions
        standard_deduction = self.standard_deduction
        
        # Use greater of itemized or standard deduction
        deduction_to_use = max(itemized_deductions, standard_deduction)
        
        # Calculate taxable income
        taxable_income = max(0, gross_income - deduction_to_use)
        
        # Calculate tax based on brackets
        tax_amount = self._calculate_tax_from_brackets(taxable_income)
        
        calculation = {
            "vendor_id": vendor_id,
            "tax_year": tax_year,
            "gross_income": gross_income,
            "itemized_deductions": itemized_deductions,
            "standard_deduction": standard_deduction,
            "deduction_used": "itemized" if itemized_deductions > standard_deduction else "standard",
            "total_deductions": deduction_to_use,
            "taxable_income": taxable_income,
            "estimated_tax": tax_amount,
            "deduction_breakdown": self._breakdown_deductions(deductions),
        }
        
        # Store calculation
        record_id = f"tax_{vendor_id}_{tax_year}"
        self.tax_records[record_id] = calculation
        
        return calculation
    
    def _calculate_tax_from_brackets(self, taxable_income: float) -> float:
        """Calculate tax using progressive tax brackets"""
        tax = 0.0
        previous_limit = 0.0
        
        for bracket_limit, rate in self.tax_brackets:
            if taxable_income <= previous_limit:
                break
            
            income_in_bracket = min(taxable_income, bracket_limit) - previous_limit
            tax += income_in_bracket * rate
            previous_limit = bracket_limit
        
        return tax
    
    def _breakdown_deductions(self, deductions: Optional[List[Dict]]) -> Dict[str, float]:
        """Break down deductions by category"""
        breakdown = {}
        for deduction in (deductions or []):
            category = deduction.get("category", "other")
            amount = deduction.get("amount", 0)
            breakdown[category] = breakdown.get(category, 0) + amount
        return breakdown
    
    def get_tax_summary(
        self,
        vendor_id: str,
        tax_year: int,
    ) -> Dict:
        """
        Get comprehensive tax summary for vendor in tax year.
        Includes income, deductions, tax liability, forms generated.
        
        Args:
            vendor_id: Vendor ID
            tax_year: Tax year to summarize
        
        Returns:
            Complete tax summary
        """
        record_key = f"tax_{vendor_id}_{tax_year}"
        calculation = self.tax_records.get(record_key, {})
        
        # Collect receipts for the year
        year_receipts = [
            r for r in self.receipts.values()
            if r["organization_id"] == vendor_id and r["tax_year"] == tax_year
        ]
        
        # Collect 1099 forms
        tax_forms = [
            d for d in self.documents.values()
            if d["vendor_id"] == vendor_id and d["tax_year"] == tax_year
        ]
        
        # Aggregate by deduction category
        deductions_by_category = {}
        for receipt in year_receipts:
            if receipt["receipt_type"] == "expense":
                category = receipt["category"]
                amount = receipt["amount"]
                deductions_by_category[category] = (
                    deductions_by_category.get(category, 0) + amount
                )
        
        summary = {
            "vendor_id": vendor_id,
            "tax_year": tax_year,
            "gross_income": calculation.get("gross_income", 0),
            "total_deductions": calculation.get("total_deductions", 0),
            "taxable_income": calculation.get("taxable_income", 0),
            "estimated_tax_liability": calculation.get("estimated_tax", 0),
            "deductions_by_category": deductions_by_category,
            "receipts_count": len(year_receipts),
            "tax_forms_generated": [f.get("type") for f in tax_forms],
            "tax_filing_deadline": f"{tax_year + 1}-04-15",  # April 15
            "recommended_quarterly_payments": self._calculate_quarterly_payments(
                calculation.get("estimated_tax", 0)
            ),
        }
        
        return summary
    
    def _calculate_quarterly_payments(self, annual_tax: float) -> Dict[str, float]:
        """Calculate recommended quarterly estimated tax payments"""
        q_payment = annual_tax / 4
        return {
            "Q1": q_payment,  # Due April 15
            "Q2": q_payment,  # Due June 15
            "Q3": q_payment,  # Due September 15
            "Q4": q_payment,  # Due January 15 next year
        }
    
    def track_deductions(
        self,
        vendor_id: str,
        category: DeductionCategory,
        amount: float,
        description: str,
        date: Optional[datetime] = None,
    ) -> Dict:
        """
        Track deductible expense with receipt.
        Records business expense for tax deduction tracking.
        
        Args:
            vendor_id: Vendor ID
            category: Deduction category
            amount: Expense amount
            description: Expense description
            date: Expense date
        
        Returns:
            Deduction record
        """
        receipt = self.create_tax_receipt(
            vendor_id,
            "expense",
            amount,
            category,
            description,
            date,
        )
        return receipt
    
    def get_deduction_total(
        self,
        vendor_id: str,
        category: Optional[DeductionCategory] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> float:
        """
        Get total deductions for vendor in period.
        Useful for estimated tax and planning.
        
        Args:
            vendor_id: Vendor ID
            category: Optional category filter
            start_date: Start of period
            end_date: End of period
        
        Returns:
            Total deduction amount
        """
        total = 0.0
        for receipt in self.receipts.values():
            if receipt["organization_id"] != vendor_id:
                continue
            if receipt["receipt_type"] != "expense":
                continue
            if category and receipt["category"] != category.value:
                continue
            
            # Check date range if specified
            if start_date or end_date:
                receipt_date = datetime.fromisoformat(receipt["date"])
                if start_date and receipt_date < start_date:
                    continue
                if end_date and receipt_date > end_date:
                    continue
            
            total += receipt["amount"]
        
        return total
    
    def estimate_quarterly_tax(
        self,
        vendor_id: str,
        ytd_income: float,
        ytd_deductions: float,
    ) -> Dict:
        """
        Estimate quarterly tax payment needed.
        Helps with tax planning and avoiding underpayment penalties.
        
        Args:
            vendor_id: Vendor ID
            ytd_income: Year-to-date income
            ytd_deductions: Year-to-date deductions
        
        Returns:
            Quarterly tax estimate
        """
        # Project to year-end
        current_month = datetime.now().month
        months_remaining = 12 - current_month
        months_elapsed = current_month
        
        # Annualize income/deductions
        annualized_income = (ytd_income / months_elapsed) * 12
        annualized_deductions = (ytd_deductions / months_elapsed) * 12
        
        # Apply standard deduction
        taxable_income = max(0, annualized_income - max(
            annualized_deductions,
            self.standard_deduction
        ))
        
        # Calculate estimated tax
        estimated_total_tax = self._calculate_tax_from_brackets(taxable_income)
        
        # Quarterly payment
        quarterly_payment = estimated_total_tax / 4
        remaining_quarters = (12 - current_month + 3) // 3  # Remaining quarter payments
        amount_due = quarterly_payment * remaining_quarters
        
        return {
            "vendor_id": vendor_id,
            "ytd_income": ytd_income,
            "annualized_income": annualized_income,
            "annualized_deductions": annualized_deductions,
            "estimated_taxable_income": taxable_income,
            "estimated_annual_tax": estimated_total_tax,
            "quarterly_payment": quarterly_payment,
            "next_payment_due": self._next_quarterly_due_date(),
            "remaining_payments": remaining_quarters,
            "amount_due_this_quarter": amount_due / remaining_quarters if remaining_quarters else 0,
        }
    
    def _next_quarterly_due_date(self) -> str:
        """Calculate next quarterly tax payment due date"""
        month = datetime.now().month
        if month < 4:
            return f"{datetime.now().year}-04-15"
        elif month < 6:
            return f"{datetime.now().year}-06-15"
        elif month < 9:
            return f"{datetime.now().year}-09-15"
        else:
            return f"{datetime.now().year + 1}-01-15"
