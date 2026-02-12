# Phase 12: Quick Start Guide

## Installation

Phase 12 is already integrated into the main application. No additional dependencies needed beyond what's already in `requirements.txt`.

## Starting the Services

### 1. Backend Services
All Phase 12 services are automatically initialized when the FastAPI application starts:

```bash
cd backend
python -m uvicorn app.main:app --reload
```

The application will:
- Initialize the database
- Create the necessary tables
- Load the RBAC system roles and permissions
- Start the enterprise service

### 2. Frontend (React)
Ensure the React development server is running:

```bash
cd frontend
npm install  # if needed
npm start
```

## API Endpoints

### Base URL
```
http://localhost:8000/api/v1/enterprise
```

### Testing with curl

**Create a Tenant:**
```bash
curl -X POST http://localhost:8000/api/v1/enterprise/tenants \
  -H "Content-Type: application/json" \
  -H "x-user-id: user123" \
  -H "x-tenant-id: tenant-abc" \
  -d '{
    "tenant_name": "Acme Corporation",
    "plan": "professional",
    "data_residency": "US"
  }'
```

**Assign Role to User:**
```bash
curl -X POST http://localhost:8000/api/v1/enterprise/rbac/roles/user456 \
  -H "Content-Type: application/json" \
  -H "x-user-id: user123" \
  -H "x-tenant-id: tenant-abc" \
  -d '{"role": "MANAGER"}'
```

**Get Audit Logs:**
```bash
curl http://localhost:8000/api/v1/enterprise/audit/logs \
  -H "x-user-id: user123" \
  -H "x-tenant-id: tenant-abc"
```

**Check System Health:**
```bash
curl http://localhost:8000/api/v1/enterprise/health
```

## Using the React Admin UI

### 1. Tenant Management

Navigate to: `http://localhost:3000/tenants`

**Features:**
- Create new tenants with plan selection
- Edit tenant details
- View member count and status
- Delete tenants
- Manage team members

**Typical Flow:**
1. Click "Create Tenant" button
2. Enter tenant name
3. Select plan (FREE, STARTER, PROFESSIONAL, ENTERPRISE)
4. Choose data residency region
5. Submit

### 2. Access Control Management

Navigate to: `http://localhost:3000/access-control`

**Tabs Available:**

**RBAC Management Tab:**
- View all roles (system + custom)
- See permissions per role
- System roles are read-only

**User Roles Tab:**
- Add users to the system
- Assign roles to users
- Revoke roles with confirmation

**Audit Logs Tab:**
- Query all audit events
- Filter by event type, user, or date
- View event details
- Export logs as CSV or JSON

**Compliance Tab:**
- See audit logging status
- Verify RBAC configuration
- Check data residency enforcement
- View subscription status

## System Roles

```
SUPER_ADMIN (35 permissions)
├─ Full system access
├─ Create/delete tenants
├─ Manage all users and roles
└─ Configure system settings

TENANT_ADMIN (30+ permissions)
├─ Tenant-level administration
├─ Member management
├─ Role assignments within tenant
└─ Subscription upgrades

MANAGER (17 permissions)
├─ Team and workflow management
├─ User invitations
├─ Audit log viewing
└─ Team member oversight

DEVELOPER (13 permissions)
├─ API key management
├─ Workflow execution
├─ Technical integrations
└─ Audit log access

USER (6 permissions)
├─ Create workflows
├─ Execute workflows
└─ API token generation

VIEWER (3 permissions)
├─ Read-only access
├─ View workflows
└─ View audit logs
```

## Subscription Tiers

### FREE
- **Price:** $0
- **Workflows:** 10
- **Executions/month:** 100
- **Team Members:** 1
- **API Calls/month:** 1,000
- **Features:** Basic workflow automation

### STARTER
- **Price:** $29/month
- **Workflows:** 100
- **Executions/month:** 10,000
- **Team Members:** 5
- **API Calls/month:** 50,000
- **Features:** Advanced analytics, 5 API keys

### PROFESSIONAL
- **Price:** $99/month
- **Workflows:** 1,000
- **Executions/month:** 100,000
- **Team Members:** 50
- **API Calls/month:** 500,000
- **Features:** SSO, audit logging, 25 API keys

### ENTERPRISE
- **Price:** Custom
- **Features:** Unlimited everything, dedicated support

## Common Tasks

### Create a Multi-Tenant Setup

1. **Create Tenant:**
   ```
   POST /api/v1/enterprise/tenants
   Body: {tenant_name, plan, data_residency}
   ```

2. **Add Team Members:**
   ```
   POST /api/v1/enterprise/tenants/{tenant_id}/members
   Body: {user_id, email, role}
   ```

3. **Verify Permissions:**
   ```
   GET /api/v1/enterprise/rbac/users/{user_id}/permissions?tenant_id={id}
   ```

### Set Up RBAC for Large Team

1. **List Available Roles:**
   ```
   GET /api/v1/enterprise/rbac/roles
   ```

2. **Assign Roles:**
   ```
   POST /api/v1/enterprise/rbac/roles/{user_id}
   Body: {role: "MANAGER"}
   ```

3. **Check Permissions:**
   ```
   POST /api/v1/enterprise/rbac/permissions/check
   Body: {user_id, permission: "workflow:create"}
   ```

### Export Audit Trail for Compliance

1. **Navigate to Access Control UI**
2. **Go to Audit Logs tab**
3. **Click Export button**
4. **Select format (JSON or CSV)**
5. **Download is automatic**

Or via API:
```bash
POST /api/v1/enterprise/audit/export
Body: {format: "csv"}
```

### Upgrade Subscription

1. **Get Current Subscription:**
   ```
   GET /api/v1/enterprise/subscriptions/{tenant_id}
   ```

2. **Upgrade Plan:**
   ```
   POST /api/v1/enterprise/subscriptions/{tenant_id}/upgrade
   Body: {new_tier: "professional"}
   ```

3. **Check Quota Impact:**
   ```
   GET /api/v1/enterprise/status/{tenant_id}
   ```

## Development

### Adding Custom Permissions

Edit `app/services/tenant_manager.py`:

```python
class CustomPermission(Permission):
    def __init__(self):
        super().__init__(
            id="custom:action",
            name="Custom Action",
            resource="custom",
            action="action",
            description="Custom permission description"
        )
```

### Creating Custom Roles

Via API:
```bash
POST /api/v1/enterprise/rbac/roles
Body: {
  "name": "Custom Role",
  "description": "Role description",
  "permissions": ["workflow:create", "workflow:execute"]
}
```

### Extending Audit Logging

In your code, call:
```python
from app.services.enterprise_service import enterprise_service

enterprise_service.log_user_action(
    event_type="custom.event",
    user_id="user123",
    tenant_id="tenant_id",
    description="Something happened",
    details={"custom_field": "value"}
)
```

## Troubleshooting

### "Tenant not found"
- Verify tenant exists: `GET /api/v1/enterprise/tenants/{tenant_id}`
- Check x-tenant-id header in request
- Ensure user is member of tenant

### "Missing required permission"
- Check user's role: `GET /api/v1/enterprise/rbac/users/{user_id}/roles`
- Get user's permissions: `GET /api/v1/enterprise/rbac/users/{user_id}/permissions`
- Verify role has permission: View in Access Control UI

### "Quota exceeded"
- Check usage: `GET /api/v1/enterprise/status/{tenant_id}`
- Upgrade plan or clean up old items
- Contact support for temporary overage

### Audit logs not appearing
- Verify audit logging is enabled
- Check that requests include proper headers
- View system health: `GET /api/v1/enterprise/health`

## Performance Tips

1. **Use Permission Caching**
   - Permissions are cached per user
   - Cache clears on role changes

2. **Batch Operations**
   - Use bulk_assign_role for multiple users
   - Reduces API calls

3. **Pagination**
   - Audit logs support pagination
   - Default limit: 100 records

4. **Filtering**
   - Filter logs by event_type before export
   - Reduces data transfer

## Next Steps

After Phase 12, consider:
1. **Phase 13:** Advanced monitoring and observability
2. **Phase 14:** API marketplace for workflow sharing
3. **Phase 15:** Custom integrations and webhooks
4. **Phase 16:** Machine learning for resource optimization

## Support

For issues or questions:
1. Check PHASE12_BUILD_COMPLETE.md for architecture details
2. Review PHASE12_SUMMARY.md for features
3. Consult integration documentation
4. Check logs for error details

---

**Phase 12: Enterprise Features Ready! 🚀**
