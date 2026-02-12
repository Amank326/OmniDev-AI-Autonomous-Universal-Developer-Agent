"""
Phase 14: Revenue Management Service
- Author earnings tracking
- Revenue split calculations
- Payout processing
- Commission system
- Financial analytics
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from app.models.marketplace_models import (
    RevenueSplit, WorkflowTemplate, TemplateAuthor, TemplateDownload
)
from app.database.config import SessionLocal
from sqlalchemy import and_, desc, func
import uuid


class RevenueManager:
    """Revenue Tracking & Payout Management"""
    
    # Commission structure
    AUTHOR_SPLIT = 0.50  # 50% to author
    PLATFORM_SPLIT = 0.30  # 30% to platform
    REFERRER_SPLIT = 0.20  # 20% to referrer
    
    def __init__(self):
        self.db = SessionLocal()
    
    # ==================== REVENUE TRACKING ====================
    
    def record_purchase(
        self,
        template_id: str,
        user_id: str,
        amount: float,
        source: str = "marketplace",
        referrer_id: Optional[str] = None
    ) -> Dict:
        """Record template purchase"""
        template = self.db.query(WorkflowTemplate).get(template_id)
        
        if not template or not template.is_paid:
            return {"error": "Invalid template or not paid"}
        
        # Track download with revenue
        download = TemplateDownload(
            id=str(uuid.uuid4()),
            template_id=template_id,
            user_id=user_id,
            source=source,
            referrer_user_id=referrer_id
        )
        
        self.db.add(download)
        
        # Calculate splits
        current_month = datetime.utcnow().strftime("%Y-%m")
        
        split = self._get_or_create_revenue_split(template_id, current_month)
        
        # Calculate amounts
        author_earnings = amount * self.AUTHOR_SPLIT
        platform_earnings = amount * self.PLATFORM_SPLIT
        referrer_earnings = amount * self.REFERRER_SPLIT if referrer_id else platform_earnings + (amount * self.REFERRER_SPLIT)
        
        # If no referrer, platform gets that commission too
        if not referrer_id:
            platform_earnings += amount * self.REFERRER_SPLIT
            referrer_earnings = 0
        
        # Update split
        split.paid_downloads += 1
        split.total_revenue += amount
        split.author_earnings += author_earnings
        split.platform_earnings += platform_earnings
        split.referrer_earnings += referrer_earnings
        
        # Update author total earnings
        template.author.total_earnings += author_earnings
        
        self.db.commit()
        
        return {
            "id": download.id,
            "amount": amount,
            "author_earnings": round(author_earnings, 2),
            "platform_earnings": round(platform_earnings, 2),
            "referrer_earnings": round(referrer_earnings, 2),
            "recorded_at": download.installed_at
        }
    
    def get_monthly_revenue(self, template_id: str, month: str) -> Dict:
        """Get revenue for specific month"""
        split = self.db.query(RevenueSplit).filter(
            RevenueSplit.template_id == template_id,
            RevenueSplit.month == month
        ).first()
        
        if not split:
            return {
                "month": month,
                "total_revenue": 0,
                "paid_downloads": 0,
                "earnings": {
                    "author": 0,
                    "platform": 0,
                    "referrer": 0
                }
            }
        
        return {
            "month": month,
            "total_revenue": round(split.total_revenue, 2),
            "paid_downloads": split.paid_downloads,
            "earnings": {
                "author": round(split.author_earnings, 2),
                "platform": round(split.platform_earnings, 2),
                "referrer": round(split.referrer_earnings, 2)
            },
            "payout": {
                "status": split.payout_status,
                "date": split.payout_date,
                "reference": split.payout_reference
            }
        }
    
    def get_author_earnings(
        self,
        author_id: str,
        months: int = 12
    ) -> Dict:
        """Get author earnings over period"""
        author = self.db.query(TemplateAuthor).get(author_id)
        
        if not author:
            return None
        
        # Get splits for author's templates
        cutoff_month = (datetime.utcnow() - timedelta(days=30*months)).strftime("%Y-%m")
        
        splits = self.db.query(RevenueSplit).join(
            WorkflowTemplate
        ).filter(
            WorkflowTemplate.author_id == author_id,
            RevenueSplit.month >= cutoff_month
        ).all()
        
        monthly_data = {}
        for split in splits:
            monthly_data[split.month] = {
                "revenue": round(split.total_revenue, 2),
                "earnings": round(split.author_earnings, 2),
                "downloads": split.paid_downloads
            }
        
        total_earnings = sum(s.author_earnings for s in splits)
        
        return {
            "author_id": author_id,
            "total_earnings": round(author.total_earnings, 2),
            "period_earnings": round(total_earnings, 2),
            "months": months,
            "monthly_breakdown": monthly_data,
            "pending_payout": self._calculate_pending_payout(author_id),
            "average_monthly": round(total_earnings / months, 2) if months > 0 else 0
        }
    
    def get_template_revenue(self, template_id: str) -> Dict:
        """Get total revenue metrics for a template"""
        template = self.db.query(WorkflowTemplate).get(template_id)
        
        if not template:
            return None
        
        splits = self.db.query(RevenueSplit).filter(
            RevenueSplit.template_id == template_id
        ).all()
        
        total_revenue = sum(s.total_revenue for s in splits)
        total_author_earnings = sum(s.author_earnings for s in splits)
        total_downloads = sum(s.paid_downloads for s in splits)
        
        return {
            "template_id": template_id,
            "total_revenue": round(total_revenue, 2),
            "author_earnings": round(total_author_earnings, 2),
            "platform_earnings": round(sum(s.platform_earnings for s in splits), 2),
            "paid_downloads": total_downloads,
            "average_price": round(total_revenue / total_downloads, 2) if total_downloads > 0 else 0,
            "by_month": {
                s.month: {
                    "revenue": round(s.total_revenue, 2),
                    "earnings": round(s.author_earnings, 2),
                    "downloads": s.paid_downloads
                } for s in sorted(splits, key=lambda x: x.month)
            }
        }
    
    # ==================== PAYOUT PROCESSING ====================
    
    def initiate_payout(
        self,
        author_id: str,
        month: str,
        payout_method: str = "stripe"
    ) -> Dict:
        """Initiate payout for author's monthly earnings"""
        # Get all splits for author in month
        splits = self.db.query(RevenueSplit).join(
            WorkflowTemplate
        ).filter(
            WorkflowTemplate.author_id == author_id,
            RevenueSplit.month == month,
            RevenueSplit.payout_status == "pending"
        ).all()
        
        if not splits:
            return {"error": "No pending payouts"}
        
        total_payout = sum(s.author_earnings for s in splits)
        payout_ref = f"PAYOUT_{month}_{author_id[:6]}_{uuid.uuid4().hex[:6]}"
        
        # Mark as processed
        for split in splits:
            split.payout_status = "processed"
            split.payout_date = datetime.utcnow()
            split.payout_reference = payout_ref
        
        self.db.commit()
        
        return {
            "payout_reference": payout_ref,
            "author_id": author_id,
            "month": month,
            "amount": round(total_payout, 2),
            "templates": len(splits),
            "status": "processing",
            "method": payout_method,
            "initiated_at": datetime.utcnow()
        }
    
    def get_payout_status(self, payout_reference: str) -> Dict:
        """Get payout status"""
        splits = self.db.query(RevenueSplit).filter(
            RevenueSplit.payout_reference == payout_reference
        ).all()
        
        if not splits:
            return None
        
        return {
            "payout_reference": payout_reference,
            "status": splits[0].payout_status,
            "amount": round(sum(s.author_earnings for s in splits), 2),
            "templates": len(splits),
            "payout_date": splits[0].payout_date
        }
    
    # ==================== FINANCIAL ANALYTICS ====================
    
    def get_platform_analytics(self, months: int = 12) -> Dict:
        """Get overall platform financial metrics"""
        cutoff_month = (datetime.utcnow() - timedelta(days=30*months)).strftime("%Y-%m")
        
        splits = self.db.query(RevenueSplit).filter(
            RevenueSplit.month >= cutoff_month
        ).all()
        
        total_revenue = sum(s.total_revenue for s in splits)
        total_author_earnings = sum(s.author_earnings for s in splits)
        total_platform_earnings = sum(s.platform_earnings for s in splits)
        total_downloads = sum(s.paid_downloads for s in splits)
        
        # By month
        monthly_revenue = {}
        for split in splits:
            if split.month not in monthly_revenue:
                monthly_revenue[split.month] = {
                    "revenue": 0,
                    "author_earnings": 0,
                    "platform_earnings": 0,
                    "downloads": 0
                }
            monthly_revenue[split.month]["revenue"] += split.total_revenue
            monthly_revenue[split.month]["author_earnings"] += split.author_earnings
            monthly_revenue[split.month]["platform_earnings"] += split.platform_earnings
            monthly_revenue[split.month]["downloads"] += split.paid_downloads
        
        return {
            "period_months": months,
            "total_revenue": round(total_revenue, 2),
            "total_author_payouts": round(total_author_earnings, 2),
            "total_platform_revenue": round(total_platform_earnings, 2),
            "total_paid_downloads": total_downloads,
            "average_monthly_revenue": round(total_revenue / months, 2) if months > 0 else 0,
            "monthly_breakdown": {
                k: {
                    "revenue": round(v["revenue"], 2),
                    "author_payouts": round(v["author_earnings"], 2),
                    "platform_revenue": round(v["platform_earnings"], 2),
                    "downloads": v["downloads"]
                } for k, v in sorted(monthly_revenue.items())
            }
        }
    
    def get_top_earning_templates(self, limit: int = 10) -> List[Dict]:
        """Get highest-earning templates"""
        splits = self.db.query(
            RevenueSplit.template_id,
            func.sum(RevenueSplit.total_revenue).label('total_revenue'),
            func.sum(RevenueSplit.paid_downloads).label('total_downloads')
        ).group_by(
            RevenueSplit.template_id
        ).order_by(
            desc(func.sum(RevenueSplit.total_revenue))
        ).limit(limit).all()
        
        result = []
        for template_id, revenue, downloads in splits:
            template = self.db.query(WorkflowTemplate).get(template_id)
            if template:
                result.append({
                    "template_id": template_id,
                    "name": template.name,
                    "total_revenue": round(revenue, 2),
                    "paid_downloads": downloads,
                    "average_price": round(revenue / downloads, 2) if downloads > 0 else 0
                })
        
        return result
    
    def get_top_earning_authors(self, limit: int = 10) -> List[Dict]:
        """Get highest-earning authors"""
        authors = self.db.query(TemplateAuthor).filter(
            TemplateAuthor.total_earnings > 0
        ).order_by(
            desc(TemplateAuthor.total_earnings)
        ).limit(limit).all()
        
        return [
            {
                "author_id": a.id,
                "username": a.username,
                "total_earnings": round(a.total_earnings, 2),
                "total_templates": a.total_templates,
                "total_downloads": a.total_downloads,
                "average_earnings_per_template": round(a.total_earnings / a.total_templates, 2) if a.total_templates > 0 else 0
            } for a in authors
        ]
    
    # ==================== HELPER METHODS ====================
    
    def _get_or_create_revenue_split(self, template_id: str, month: str) -> RevenueSplit:
        """Get or create monthly split record"""
        split = self.db.query(RevenueSplit).filter(
            RevenueSplit.template_id == template_id,
            RevenueSplit.month == month
        ).first()
        
        if not split:
            template = self.db.query(WorkflowTemplate).get(template_id)
            split = RevenueSplit(
                id=str(uuid.uuid4()),
                template_id=template_id,
                author_id=template.author_id,
                month=month,
                author_percent=self.AUTHOR_SPLIT * 100,
                platform_percent=self.PLATFORM_SPLIT * 100,
                referrer_percent=self.REFERRER_SPLIT * 100
            )
            self.db.add(split)
        
        return split
    
    def _calculate_pending_payout(self, author_id: str) -> float:
        """Calculate pending payout for author"""
        pending = self.db.query(RevenueSplit).join(
            WorkflowTemplate
        ).filter(
            WorkflowTemplate.author_id == author_id,
            RevenueSplit.payout_status == "pending"
        ).all()
        
        return round(sum(s.author_earnings for s in pending), 2)
