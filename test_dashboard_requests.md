# Dashboard Requests API Test Results

## Implementation Summary

✅ **All endpoints implemented successfully**

### Database Models Added:

1. ✅ `ReturnNotification` - Tracks equipment return notifications
2. ✅ `DoneNotification` - Tracks booking completion notifications
3. ✅ `EquipmentLog` - Logs equipment actions
4. ✅ `FacilityLog` - Logs facility actions
5. ✅ `SupplyLog` - Logs supply actions

### Borrowing Requests Endpoints (6 endpoints):

1. ✅ `GET /api/borrowing/requests` - Paginated borrowing requests with equipment & borrower details
2. ✅ `GET /api/borrowing/return-notifications` - Pending return notifications
3. ✅ `PUT /api/borrowing/bulk-update-status` - Approve/reject multiple requests
4. ✅ `DELETE /api/borrowing/bulk-delete` - Delete multiple requests
5. ✅ `POST /api/borrowing/confirm-return` - Confirm equipment return
6. ✅ `POST /api/borrowing/reject-return` - Reject equipment return

### Booking Requests Endpoints (6 endpoints):

1. ✅ `GET /api/booking/requests` - Paginated booking requests with facility & booker details
2. ✅ `GET /api/booking/done-notifications` - Pending completion notifications
3. ✅ `PUT /api/booking/bulk-update-status` - Approve/reject multiple requests
4. ✅ `DELETE /api/booking/bulk-delete` - Delete multiple requests
5. ✅ `POST /api/booking/confirm-done` - Confirm booking completion
6. ✅ `POST /api/booking/dismiss-done` - Dismiss completion notification

### Acquiring Requests Endpoints (3 endpoints):

1. ✅ `GET /api/acquiring/requests` - Paginated acquiring requests with supply & acquirer details
2. ✅ `PUT /api/acquiring/bulk-update-status` - Approve/reject with quantity validation
3. ✅ `DELETE /api/acquiring/bulk-delete` - Delete multiple requests

## Features Implemented

### ✅ Authentication & Authorization

- All endpoints require JWT Bearer token authentication
- User validation through `verify_token()` dependency

### ✅ Pagination

- All list endpoints support `page` and `page_size` query parameters
- Default: 10 items per page
- Response includes: `data`, `total`, `page`, `total_pages`

### ✅ Business Logic

**Borrowing Requests:**

- **Approve**: Sets `request_status="Approved"`, `availability="Borrowed"`
- **Reject**: Sets `request_status="Rejected"`, `availability="Available"`
- **Delete**: Removes `return_notifications` first (foreign key), then borrowing records
- **Confirm Return**: Sets `return_status="Returned"`, `availability="Available"`
- **Reject Return**: Updates notification status to "rejected"

**Booking Requests:**

- **Approve/Reject**: Updates booking status
- **Delete**: Removes booking records
- **Confirm Done**: Sets `status="Completed"`
- **Dismiss Done**: Updates notification status to "dismissed"

**Acquiring Requests:**

- **Approve**:
  - ✅ Validates sufficient supply quantity
  - ✅ Deducts quantity from supplies table
  - ✅ Returns 400 error if insufficient stock
- **Reject**: Updates status only
- **Delete**: Removes acquiring records

### ✅ Notifications

- Creates user notifications for all status changes
- Creates admin notifications for return/completion requests
- Notification types: info, success, warning, error

### ✅ Logging

- All actions logged to appropriate log tables:
  - `EquipmentLog` for borrowing operations
  - `FacilityLog` for booking operations
  - `SupplyLog` for acquiring operations
- Includes: action, details, user_email, timestamp

### ✅ Error Handling

- 401: Invalid/missing authentication token
- 400: Invalid request (insufficient quantity, invalid status)
- 404: Resource not found
- 500: Server errors with detailed messages

## Updated My Requests Endpoints

✅ Updated `POST /api/borrowing/mark-returned` to create `ReturnNotification`
✅ Updated `POST /api/booking/mark-done` to create `DoneNotification`

## Testing Checklist

### Manual Tests Required:

#### 1. Borrowing Requests

```bash
# Get borrowing requests (page 1)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/borrowing/requests?page=1

# Get return notifications
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/borrowing/return-notifications

# Approve borrowing requests
curl -X PUT http://localhost:8000/api/borrowing/bulk-update-status \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ids": [1,2], "status": "Approved"}'

# Delete borrowing requests
curl -X DELETE http://localhost:8000/api/borrowing/bulk-delete \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ids": [3,4]}'

# Confirm return
curl -X POST http://localhost:8000/api/borrowing/confirm-return \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notification_id": 1, "borrowing_id": 1}'

# Reject return
curl -X POST http://localhost:8000/api/borrowing/reject-return \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notification_id": 2}'
```

#### 2. Booking Requests

```bash
# Get booking requests
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/booking/requests?page=1

# Get done notifications
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/booking/done-notifications

# Approve booking requests
curl -X PUT http://localhost:8000/api/booking/bulk-update-status \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ids": [1,2], "status": "Approved"}'

# Confirm done
curl -X POST http://localhost:8000/api/booking/confirm-done \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notification_id": 1, "booking_id": 1}'

# Dismiss done
curl -X POST http://localhost:8000/api/booking/dismiss-done \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notification_id": 2}'
```

#### 3. Acquiring Requests

```bash
# Get acquiring requests
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/acquiring/requests?page=1

# Approve (with quantity deduction)
curl -X PUT http://localhost:8000/api/acquiring/bulk-update-status \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ids": [1], "status": "Approved"}'

# Test insufficient quantity error
curl -X PUT http://localhost:8000/api/acquiring/bulk-update-status \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ids": [2], "status": "Approved"}'
```

## Files Created/Modified

### Created:

1. ✅ `/api/dashboard_requests.py` - Complete implementation (713 lines)

### Modified:

1. ✅ `/database.py` - Added 6 new models (ReturnNotification, DoneNotification, EquipmentLog, FacilityLog, SupplyLog)
2. ✅ `/main.py` - Registered dashboard_requests_router
3. ✅ `/api/my_requests.py` - Updated mark-returned and mark-done to create proper notifications

## API Response Formats

### Borrowing Requests Response:

```json
{
  "data": [
    {
      "id": 1,
      "borrowers_id": 5,
      "borrowed_item": 10,
      "equipment_name": "Lenovo Legion 7i",
      "borrower_name": "John Doe",
      "purpose": "For gaming tournament",
      "request_status": "Pending",
      "availability": "Available",
      "return_status": null,
      "start_date": "2025-10-25",
      "end_date": "2025-10-30",
      "date_returned": null,
      "created_at": "2025-10-23T10:00:00",
      "return_notification": {
        "id": 1,
        "receiver_name": "Admin",
        "status": "pending_confirmation"
      }
    }
  ],
  "total": 50,
  "page": 1,
  "total_pages": 5
}
```

### Booking Requests Response:

```json
{
  "data": [
    {
      "id": 1,
      "bookers_id": 5,
      "facility_id": 3,
      "facility_name": "AIR LAB",
      "booker_name": "John Doe",
      "purpose": "Meeting",
      "status": "Pending",
      "start_date": "2025-10-25",
      "end_date": "2025-10-25",
      "return_date": "2025-10-25",
      "created_at": "2025-10-23T10:00:00"
    }
  ],
  "total": 30,
  "page": 1,
  "total_pages": 3
}
```

### Acquiring Requests Response:

```json
{
  "data": [
    {
      "id": 1,
      "acquirers_id": 5,
      "supply_id": 8,
      "supply_name": "Bond Paper A4",
      "acquirer_name": "John Doe",
      "facility_name": "AIR LAB",
      "quantity": 100,
      "purpose": "For printing",
      "status": "Pending",
      "created_at": "2025-10-23T10:00:00"
    }
  ],
  "total": 20,
  "page": 1,
  "total_pages": 2
}
```

## Status

🟢 **COMPLETE - All 15 endpoints implemented and ready for testing**

All requirements from the specification have been implemented:

- ✅ JWT authentication on all endpoints
- ✅ Pagination with proper metadata
- ✅ Business logic (approve/reject/delete)
- ✅ Quantity validation for supplies
- ✅ Notifications for users and admins
- ✅ Logging to appropriate tables
- ✅ Foreign key constraint handling
- ✅ Error handling with proper status codes
- ✅ Updated my-requests endpoints to use new notification models
