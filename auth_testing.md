# Emergent Google Auth - Testing Playbook

## Step 1: Create Test User & Session
```bash
mongosh --eval "
use('test_database');
var userId = 'test-user-' + Date.now();
var sessionToken = 'test_session_' + Date.now();
db.users.insertOne({
  user_id: userId,
  email: 'test.user.' + Date.now() + '@example.com',
  name: 'Test User',
  picture: 'https://via.placeholder.com/150',
  created_at: new Date()
});
db.user_sessions.insertOne({
  user_id: userId,
  session_token: sessionToken,
  expires_at: new Date(Date.now() + 7*24*60*60*1000),
  created_at: new Date()
});
print('Session token: ' + sessionToken);
print('User ID: ' + userId);
"
```

## Step 2: Test Backend Endpoints
```bash
curl -X GET "$BACKEND_URL/api/auth/me" -H "Authorization: Bearer YOUR_SESSION_TOKEN"
curl -X GET "$BACKEND_URL/api/shipments" -H "Authorization: Bearer YOUR_SESSION_TOKEN"
```

## Step 3: Browser Testing
Set cookie before navigation; ensure shipments are scoped to the authenticated user_id.

## Multi-Tenant Verification
- User A's shipments should NOT be visible to User B
- All queries on /api/shipments, /api/pickups, /api/settings must filter by user_id
- Settings are per-user (each business has their own sender/pickup_location/GST)
- Delhivery API key is shared across all users (single franchise key)
