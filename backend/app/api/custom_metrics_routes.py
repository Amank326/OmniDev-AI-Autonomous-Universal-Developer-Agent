"""Phase 8: Custom Metrics Builder Service

Provides ability for users to create, manage, and calculate custom metrics
similar to Metabase, with formula evaluation, threshold management, and trending.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from pydantic import BaseModel
import json
import re

from app.auth.dependencies import get_current_user
from app.database.config import get_db
from app.models.cohort_models import CustomMetric, MetricHistory, MetricType

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class MetricDefinition(BaseModel):
    """Define custom metric"""
    name: str
    description: Optional[str]
    metric_type: str  # count, sum, avg, percentage, ratio, custom_formula
    formula: Optional[str]  # SQL-like formula for custom calculations
    source_table: Optional[str]  # e.g., "user_activity", "engagement_metrics"
    source_fields: Optional[List[str]]  # e.g., ["api_calls", "errors"]
    time_period: str = "daily"  # daily, weekly, monthly
    aggregation: str = "sum"  # sum, avg, count, max, min
    threshold_warning: Optional[float]
    threshold_critical: Optional[float]
    is_public: bool = False


class MetricCalculation(BaseModel):
    """Result of metric calculation"""
    metric_id: int
    name: str
    current_value: float
    previous_value: Optional[float]
    change: float
    change_percentage: float
    trend_direction: str  # up, down, flat
    status: str  # healthy, warning, critical
    calculated_at: datetime


class MetricCreateRequest(BaseModel):
    """Create metric request"""
    name: str
    metric_type: str
    description: Optional[str] = None
    formula: Optional[str] = None
    source_table: Optional[str] = None
    source_fields: Optional[List[str]] = None
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None


# Create router
router = APIRouter(
    prefix="/api/metrics",
    tags=["custom-metrics"]
)


# ============================================================================
# FORMULA PARSER & VALIDATOR
# ============================================================================

class FormulaValidator:
    """
    Validates and evaluates metric formulas
    
    Supports:
    - Basic operators: +, -, *, /, %
    - Functions: COUNT, SUM, AVG, MAX, MIN
    - Field references: {field_name}
    - Parentheses for grouping: (a + b) * c
    """

    ALLOWED_FUNCTIONS = {'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'IF'}
    ALLOWED_OPERATORS = {'+', '-', '*', '/', '%', '(', ')'}

    @staticmethod
    def validate(formula: str) -> Dict[str, Any]:
        """Validate formula syntax and structure"""
        if not formula or not isinstance(formula, str):
            return {"valid": False, "error": "Formula must be non-empty string"}

        # Check for invalid characters
        cleaned = re.sub(r'[\w\s\{\}\(\)\+\-\*/%,.]', '', formula)
        if cleaned:
            return {"valid": False, "error": f"Invalid characters: {cleaned}"}

        # Check for balanced parentheses
        if formula.count('(') != formula.count(')'):
            return {"valid": False, "error": "Unbalanced parentheses"}

        # Extract field references
        fields = re.findall(r'\{(\w+)\}', formula)

        return {
            "valid": True,
            "formula": formula,
            "fields": list(set(fields)),  # unique fields
            "message": "Formula is valid"
        }

    @staticmethod
    def evaluate(formula: str, values: Dict[str, float]) -> float:
        """
        Safely evaluate formula with provided values
        
        Example:
            formula = "(api_calls + webhooks) / total_requests"
            values = {"api_calls": 100, "webhooks": 50, "total_requests": 200}
            result = 0.75
        """
        # Validate first
        validation = FormulaValidator.validate(formula)
        if not validation["valid"]:
            raise ValueError(validation["error"])

        # Replace field references with values
        eval_formula = formula
        for field in validation["fields"]:
            if field not in values:
                raise ValueError(f"Missing value for field: {field}")
            eval_formula = eval_formula.replace(f"{{{field}}}", str(values[field]))

        # Safe evaluation (only math operations)
        try:
            result = eval(eval_formula, {"__builtins__": {}}, {})
            return float(result)
        except Exception as e:
            raise ValueError(f"Formula evaluation failed: {str(e)}")


# ============================================================================
# CUSTOM METRICS SERVICE
# ============================================================================

class CustomMetricsService:
    """Service for custom metric management and calculation"""

    @staticmethod
    def create_metric(
        db: Session,
        customer_id: int,
        name: str,
        metric_type: str,
        formula: Optional[str] = None,
        source_table: Optional[str] = None,
        source_fields: Optional[List[str]] = None,
        threshold_warning: Optional[float] = None,
        threshold_critical: Optional[float] = None,
        created_by: str = None
    ) -> CustomMetric:
        """Create new custom metric definition"""
        
        # Validate metric type
        try:
            MetricType(metric_type)
        except ValueError:
            raise ValueError(f"Invalid metric type: {metric_type}")

        # Validate formula if custom_formula type
        if metric_type == "custom_formula" and formula:
            validation = FormulaValidator.validate(formula)
            if not validation["valid"]:
                raise ValueError(validation["error"])

        # Check for duplicate metric name
        existing = db.query(CustomMetric).filter_by(
            customer_id=customer_id,
            name=name
        ).first()
        if existing:
            raise ValueError(f"Metric '{name}' already exists")

        # Create metric
        metric = CustomMetric(
            customer_id=customer_id,
            name=name,
            metric_type=MetricType(metric_type),
            formula=formula,
            source_table=source_table,
            source_fields=json.dumps(source_fields or []),
            threshold_warning=threshold_warning,
            threshold_critical=threshold_critical,
            created_by=created_by,
            is_public=False,
            last_calculated=datetime.utcnow(),
            current_value=0.0
        )

        db.add(metric)
        db.commit()
        db.refresh(metric)

        return metric

    @staticmethod
    def calculate_metric(
        db: Session,
        metric_id: int,
        data_values: Optional[Dict[str, float]] = None
    ) -> MetricCalculation:
        """
        Calculate current value for a metric
        
        For custom_formula metrics, uses provided data_values
        For other types, queries source table
        """
        metric = db.query(CustomMetric).filter_by(id=metric_id).first()
        if not metric:
            raise ValueError("Metric not found")

        previous_value = metric.current_value
        change_percentage = 0.0

        # Calculate based on metric type
        if metric.metric_type == MetricType.CUSTOM_FORMULA:
            if not data_values:
                raise ValueError("data_values required for custom_formula metrics")
            
            current_value = FormulaValidator.evaluate(metric.formula, data_values)

        elif metric.metric_type == MetricType.COUNT:
            # COUNT(*) from source_table
            if not metric.source_table:
                raise ValueError("source_table required for count metrics")
            
            query = f"SELECT COUNT(*) as count FROM {metric.source_table}"
            result = db.execute(text(query)).fetchone()
            current_value = float(result[0]) if result else 0.0

        elif metric.metric_type == MetricType.SUM:
            # SUM(field) from source_table
            if not metric.source_table or not metric.source_fields:
                raise ValueError("source_table and source_fields required")
            
            field = json.loads(metric.source_fields)[0] if metric.source_fields else None
            if not field:
                raise ValueError("No field specified for SUM")
            
            query = f"SELECT SUM({field}) as total FROM {metric.source_table}"
            result = db.execute(text(query)).fetchone()
            current_value = float(result[0]) if result and result[0] else 0.0

        elif metric.metric_type == MetricType.AVERAGE:
            # AVG(field) from source_table
            if not metric.source_table or not metric.source_fields:
                raise ValueError("source_table and source_fields required")
            
            field = json.loads(metric.source_fields)[0] if metric.source_fields else None
            query = f"SELECT AVG({field}) as average FROM {metric.source_table}"
            result = db.execute(text(query)).fetchone()
            current_value = float(result[0]) if result and result[0] else 0.0

        else:
            current_value = 0.0

        # Calculate change
        if previous_value and previous_value != 0:
            change = current_value - previous_value
            change_percentage = (change / abs(previous_value)) * 100
        else:
            change = current_value
            change_percentage = 0.0

        # Determine trend direction
        if change > 0:
            trend_direction = "up"
        elif change < 0:
            trend_direction = "down"
        else:
            trend_direction = "flat"

        # Determine status based on thresholds
        if metric.threshold_critical and current_value >= metric.threshold_critical:
            status = "critical"
        elif metric.threshold_warning and current_value >= metric.threshold_warning:
            status = "warning"
        else:
            status = "healthy"

        # Update metric in database
        metric.current_value = current_value
        metric.previous_value = previous_value
        metric.change_percentage = change_percentage
        metric.trend_direction = trend_direction
        metric.last_calculated = datetime.utcnow()
        db.commit()

        # Record in history
        history = MetricHistory(
            metric_id=metric_id,
            customer_id=metric.customer_id,
            value=current_value,
            change_from_previous=change,
            percent_change=change_percentage,
            recorded_at=datetime.utcnow()
        )
        db.add(history)
        db.commit()

        return MetricCalculation(
            metric_id=metric_id,
            name=metric.name,
            current_value=current_value,
            previous_value=previous_value,
            change=change,
            change_percentage=change_percentage,
            trend_direction=trend_direction,
            status=status,
            calculated_at=datetime.utcnow()
        )

    @staticmethod
    def update_metric(
        db: Session,
        metric_id: int,
        **kwargs
    ) -> CustomMetric:
        """Update metric definition"""
        metric = db.query(CustomMetric).filter_by(id=metric_id).first()
        if not metric:
            raise ValueError("Metric not found")

        # Validate formula if updating
        if "formula" in kwargs and kwargs["formula"]:
            validation = FormulaValidator.validate(kwargs["formula"])
            if not validation["valid"]:
                raise ValueError(validation["error"])

        # Update fields
        for key, value in kwargs.items():
            if hasattr(metric, key):
                setattr(metric, key, value)

        db.commit()
        db.refresh(metric)

        return metric

    @staticmethod
    def delete_metric(db: Session, metric_id: int) -> bool:
        """Delete metric and its history"""
        metric = db.query(CustomMetric).filter_by(id=metric_id).first()
        if not metric:
            raise ValueError("Metric not found")

        # Delete history first
        db.query(MetricHistory).filter_by(metric_id=metric_id).delete()

        # Delete metric
        db.delete(metric)
        db.commit()

        return True

    @staticmethod
    def get_metrics_for_customer(
        db: Session,
        customer_id: int,
        include_public: bool = True
    ) -> List[CustomMetric]:
        """Get all metrics for a customer"""
        query = db.query(CustomMetric).filter_by(customer_id=customer_id)

        if include_public:
            # Include own metrics and public metrics from others
            query = db.query(CustomMetric).filter(
                (CustomMetric.customer_id == customer_id) |
                (CustomMetric.is_public == True)
            )

        return query.all()


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("")
async def create_metric(
    request: MetricCreateRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create custom metric definition
    
    **Metric Types:**
    - count: COUNT(*) from table
    - sum: SUM of values
    - average: AVG of values
    - percentage: % calculation
    - ratio: Ratio of two metrics
    - custom_formula: Custom evaluated formula
    
    **Example (Custom Formula):**
    ```json
    {
      "name": "API Success Rate",
      "metric_type": "custom_formula",
      "formula": "successful_calls / total_calls * 100"
    }
    ```
    
    **Example (Table Count):**
    ```json
    {
      "name": "Active Users",
      "metric_type": "count",
      "source_table": "user_activity"
    }
    ```
    """
    try:
        metric = CustomMetricsService.create_metric(
            db=db,
            customer_id=current_user.id,
            name=request.name,
            metric_type=request.metric_type,
            formula=request.formula,
            source_table=request.source_table,
            source_fields=request.source_fields,
            threshold_warning=request.threshold_warning,
            threshold_critical=request.threshold_critical,
            created_by=current_user.email
        )
        return metric
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{metric_id}")
async def get_metric(
    metric_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get metric definition"""
    metric = db.query(CustomMetric).filter_by(id=metric_id).first()
    
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    
    if metric.customer_id != current_user.id and not metric.is_public:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return metric


@router.post("/{metric_id}/calculate")
async def calculate_metric(
    metric_id: int,
    data_values: Optional[Dict[str, float]] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Calculate current value for metric
    
    For custom_formula metrics, pass calculated values:
    ```json
    {
      "successful_calls": 950,
      "total_calls": 1000
    }
    ```
    """
    try:
        metric = db.query(CustomMetric).filter_by(id=metric_id).first()
        
        if not metric:
            raise HTTPException(status_code=404, detail="Metric not found")
        
        if metric.customer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        result = CustomMetricsService.calculate_metric(db, metric_id, data_values)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{metric_id}/history")
async def get_metric_history(
    metric_id: int,
    days: int = Query(30, description="Days of history"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get metric value history for trending"""
    metric = db.query(CustomMetric).filter_by(id=metric_id).first()
    
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")
    
    if metric.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    history = db.query(MetricHistory)\
        .filter_by(metric_id=metric_id)\
        .filter(MetricHistory.recorded_at >= datetime.utcnow() - timedelta(days=days))\
        .order_by(MetricHistory.recorded_at)\
        .all()

    return {
        "metric_id": metric_id,
        "name": metric.name,
        "days": days,
        "points": [
            {
                "date": h.recorded_at,
                "value": h.value,
                "change": h.change_from_previous,
                "percent_change": h.percent_change
            }
            for h in history
        ]
    }


@router.patch("/{metric_id}")
async def update_metric(
    metric_id: int,
    threshold_warning: Optional[float] = None,
    threshold_critical: Optional[float] = None,
    is_public: Optional[bool] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update metric settings"""
    try:
        metric = db.query(CustomMetric).filter_by(id=metric_id).first()
        
        if not metric:
            raise HTTPException(status_code=404, detail="Metric not found")
        
        if metric.customer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        updates = {}
        if threshold_warning is not None:
            updates["threshold_warning"] = threshold_warning
        if threshold_critical is not None:
            updates["threshold_critical"] = threshold_critical
        if is_public is not None:
            updates["is_public"] = is_public

        result = CustomMetricsService.update_metric(db, metric_id, **updates)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{metric_id}")
async def delete_metric(
    metric_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete metric and its history"""
    try:
        metric = db.query(CustomMetric).filter_by(id=metric_id).first()
        
        if not metric:
            raise HTTPException(status_code=404, detail="Metric not found")
        
        if metric.customer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        CustomMetricsService.delete_metric(db, metric_id)
        return {"success": True, "message": "Metric deleted"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
async def list_metrics(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    include_public: bool = Query(True)
):
    """List all metrics accessible to user"""
    metrics = CustomMetricsService.get_metrics_for_customer(
        db, current_user.id, include_public=include_public
    )
    
    return {
        "count": len(metrics),
        "metrics": metrics
    }


@router.post("/formula/validate")
async def validate_formula(
    formula: str = Query(...),
    current_user = Depends(get_current_user)
):
    """
    Validate formula syntax
    
    **Example:**
    ```
    POST /api/metrics/formula/validate?formula=(api_calls%2Bwebhooks)%2Ftotal_requests
    ```
    """
    result = FormulaValidator.validate(formula)
    return result
