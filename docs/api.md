# Movona REST API Documentation

Comprehensive API Reference for the **Movona** Backend Ride-Booking Platform.

---

## 1. Overview & Standards

- **Base URL**: `http://localhost:8000/api/`
- **Format**: JSON (`Content-Type: application/json`)
- **Authentication**: JWT Bearer Token (`Authorization: Bearer <access_token>`)
- **Standard HTTP Status Codes**:
  - `200 OK`: Successful retrieval or update
  - `201 Created`: Successful creation
  - `204 No Content`: Successful deletion
  - `400 Bad Request`: Validation error or invalid lifecycle transition
  - `401 Unauthorized`: Missing or invalid JWT credentials
  - `403 Forbidden`: Authenticated user lacks required role (e.g. customer accessing driver endpoint)
  - `404 Not Found`: Resource does not exist or belongs to another user (ownership isolation)

---

## 2. Authentication Endpoints

### 2.1 Customer Registration
- **Endpoint**: `POST /api/auth/register/`
- **Auth**: Public (`AllowAny`)
- **Request Body**:
```json
{
  "username": "johndoe",
  "email": "johndoe@example.com",
  "phone": "+919876543210",
  "password": "SecurePassword123!",
  "password_confirm": "SecurePassword123!"
}
```
- **Response (201 Created)**:
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "johndoe@example.com",
  "phone": "+919876543210",
  "is_customer": true,
  "created_at": "2026-08-28T10:00:00Z"
}
```

### 2.2 Obtain JWT Token (Login)
- **Endpoint**: `POST /api/auth/token/`
- **Auth**: Public
- **Request Body**:
```json
{
  "username": "johndoe",
  "password": "SecurePassword123!"
}
```
- **Response (200 OK)**:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsIn...",
  "refresh": "eyJhbGciOiJIUzI1NiIsIn..."
}
```

### 2.3 Refresh JWT Token
- **Endpoint**: `POST /api/auth/token/refresh/`
- **Auth**: Public
- **Request Body**:
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsIn..."
}
```
- **Response (200 OK)**:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsIn..."
}
```

---

## 3. Vehicle Categories & Vehicles

### 3.1 List Vehicle Categories
- **Endpoint**: `GET /api/categories/`
- **Auth**: Public
- **Response (200 OK)**:
```json
[
  {
    "id": 1,
    "name": "Mini",
    "description": "Affordable compact rides",
    "passenger_capacity": 4,
    "base_fare": "50.00",
    "per_km_rate": "10.00",
    "per_minute_rate": "2.00",
    "is_active": true
  }
]
```

### 3.2 List Driver Vehicles
- **Endpoint**: `GET /api/drivers/vehicles/`
- **Auth**: Authenticated Driver (`IsDriver`)
- **Response (200 OK)**:
```json
[
  {
    "id": 1,
    "category": 1,
    "category_name": "Mini",
    "make": "Toyota",
    "model": "Yaris",
    "registration_number": "DL01AB1234",
    "colour": "White",
    "seating_capacity": 4,
    "verification_status": "APPROVED",
    "is_active": true,
    "created_at": "2026-08-28T10:00:00Z",
    "updated_at": "2026-08-28T10:00:00Z"
  }
]
```

### 3.3 Register Driver Vehicle
- **Endpoint**: `POST /api/drivers/vehicles/`
- **Auth**: Authenticated Driver (`IsDriver`)
- **Request Body**:
```json
{
  "category": 1,
  "make": "Honda",
  "model": "City",
  "registration_number": "DL01CD5678",
  "colour": "Silver",
  "seating_capacity": 4
}
```
- **Response (201 Created)**: Returns created vehicle with `verification_status: "PENDING"` and `is_active: false`.

### 3.4 Update Driver Vehicle
- **Endpoint**: `PATCH /api/drivers/vehicles/<id>/`
- **Auth**: Authenticated Driver (Owner only)
- **Request Body**:
```json
{
  "colour": "Metallic Blue",
  "is_active": true
}
```
*Note: A vehicle can only be set to `is_active: true` once verified and approved by admin.*

### 3.5 Delete Driver Vehicle
- **Endpoint**: `DELETE /api/drivers/vehicles/<id>/`
- **Auth**: Authenticated Driver (Owner only)
- **Response (204 No Content)**

---

## 4. Customer Profiles & Ride Management

### 4.1 Get Customer Profile
- **Endpoint**: `GET /api/customers/me/`
- **Auth**: Authenticated Customer
- **Response (200 OK)**:
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "johndoe@example.com",
  "phone": "+919876543210",
  "date_of_birth": "1995-05-15",
  "gender": "Male",
  "address": "123 Connaught Place, New Delhi",
  "profile_photo": null,
  "average_rating": "4.85",
  "total_rides": 12,
  "created_at": "2026-08-28T10:00:00Z"
}
```

### 4.2 Update Customer Profile
- **Endpoint**: `PATCH /api/customers/me/`
- **Auth**: Authenticated Customer
- **Request Body**:
```json
{
  "gender": "Male",
  "address": "456 Cyber City, Gurugram"
}
```

### 4.3 Fare Estimate
- **Endpoint**: `POST /api/rides/estimate/`
- **Auth**: Public
- **Request Body**:
```json
{
  "category": "Mini",
  "distance_km": 12.50,
  "duration_minutes": 25
}
```
- **Response (200 OK)**:
```json
{
  "category": "Mini",
  "distance_km": "12.50",
  "duration_minutes": 25,
  "estimated_fare": "225.00"
}
```

### 4.4 Book a Ride
- **Endpoint**: `POST /api/rides/book/`
- **Auth**: Authenticated Customer
- **Request Body**:
```json
{
  "category": "Mini",
  "pickup_address": "Connaught Place, New Delhi",
  "pickup_latitude": "28.6315000",
  "pickup_longitude": "77.2167000",
  "destination_address": "India Gate, New Delhi",
  "destination_latitude": "28.6129000",
  "destination_longitude": "77.2295000",
  "distance_km": "8.00",
  "duration_minutes": 20
}
```
- **Response (201 Created)**:
```json
{
  "id": 101,
  "customer_name": "johndoe",
  "driver_name": null,
  "vehicle_details": null,
  "category": "Mini",
  "pickup_address": "Connaught Place, New Delhi",
  "destination_address": "India Gate, New Delhi",
  "estimated_distance_km": "8.00",
  "estimated_duration_minutes": 20,
  "estimated_fare": "170.00",
  "final_fare": null,
  "status": "REQUESTED",
  "cancelled_by": null,
  "cancellation_reason": "",
  "requested_at": "2026-08-28T10:15:00Z",
  "accepted_at": null,
  "arrived_at": null,
  "started_at": null,
  "completed_at": null,
  "cancelled_at": null,
  "created_at": "2026-08-28T10:15:00Z"
}
```

### 4.5 Customer Ride History
- **Endpoint**: `GET /api/rides/`
- **Query Params**: `?status=COMPLETED` (optional filter)
- **Auth**: Authenticated Customer
- **Response (200 OK)**: Array of booking objects.

### 4.6 Cancel Booking
- **Endpoint**: `POST /api/rides/<id>/cancel/`
- **Auth**: Authenticated Customer (Owner only)
- **Request Body**:
```json
{
  "reason": "Driver took too long"
}
```
- **Response (200 OK)**: Updated booking object with `status: "CANCELLED"`.

### 4.7 Customer Rate Driver
- **Endpoint**: `POST /api/rides/<id>/rate/`
- **Auth**: Authenticated Customer (Owner of completed booking)
- **Request Body**:
```json
{
  "rating": 5,
  "feedback": "Smooth driving and polite attitude."
}
```
- **Response (201 Created)**:
```json
{
  "id": 1,
  "booking_id": 101,
  "rating_type": "CUSTOMER_TO_DRIVER",
  "rating": 5,
  "feedback": "Smooth driving and polite attitude.",
  "created_at": "2026-08-28T11:00:00Z"
}
```

---

## 5. Driver Operations & Ride Lifecycle

### 5.1 Get / Update Driver Profile & Availability
- **Endpoint**: `GET /api/drivers/me/` | `PATCH /api/drivers/me/`
- **Auth**: Authenticated Driver (`IsDriver`)
- **Request Body (PATCH)**:
```json
{
  "availability_status": "ONLINE"
}
```

### 5.2 Discover Eligible Rides
- **Endpoint**: `GET /api/drivers/rides/eligible/`
- **Auth**: Authenticated Driver (`IsDriver`)
- **Response (200 OK)**: Returns list of pending (`REQUESTED`) bookings matching driver's vehicle categories when driver is `ONLINE`.

### 5.3 Accept a Ride
- **Endpoint**: `POST /api/drivers/rides/<id>/accept/`
- **Auth**: Authenticated Driver (`IsDriver`)
- **Response (200 OK)**: Transitions booking to `ACCEPTED`, assigns driver and vehicle, sets driver status to `BUSY`.

### 5.4 Driver Ride History
- **Endpoint**: `GET /api/drivers/rides/`
- **Query Params**: `?status=STARTED` (optional filter)
- **Auth**: Authenticated Driver (`IsDriver`)
- **Response (200 OK)**: Array of bookings assigned to authenticated driver.

### 5.5 Mark Driver Arriving
- **Endpoint**: `POST /api/drivers/rides/<id>/arriving/`
- **Auth**: Authenticated Assigned Driver
- **Transition**: `ACCEPTED` $\rightarrow$ `DRIVER_ARRIVING`
- **Response (200 OK)**

### 5.6 Mark Driver Arrived
- **Endpoint**: `POST /api/drivers/rides/<id>/arrived/`
- **Auth**: Authenticated Assigned Driver
- **Transition**: `DRIVER_ARRIVING` $\rightarrow$ `DRIVER_ARRIVED`
- **Response (200 OK)**: Records `arrived_at` timestamp and prepares hashed ride OTP.

### 5.7 Verify OTP & Start Ride
- **Endpoint**: `POST /api/drivers/rides/<id>/start/`
- **Auth**: Authenticated Assigned Driver
- **Transition**: `DRIVER_ARRIVED` $\rightarrow$ `STARTED`
- **Request Body**:
```json
{
  "otp": "4829"
}
```
- **Response (200 OK)**: Verifies OTP against secure Django password hash and records `started_at` timestamp.

### 5.8 Complete Ride
- **Endpoint**: `POST /api/drivers/rides/<id>/complete/`
- **Auth**: Authenticated Assigned Driver
- **Transition**: `STARTED` $\rightarrow$ `COMPLETED`
- **Response (200 OK)**: Calculates final fare server-side, increments driver's `completed_rides`, and frees driver availability to `ONLINE`.

### 5.9 Driver Rate Customer
- **Endpoint**: `POST /api/drivers/rides/<id>/rate/`
- **Auth**: Authenticated Assigned Driver
- **Request Body**:
```json
{
  "rating": 5,
  "feedback": "Passenger was on time."
}
```
- **Response (201 Created)**

---

## 6. Ride Lifecycle State Machine

```
[REQUESTED] ──(Driver Accepts)──> [ACCEPTED]
     │                                │
     │ (Cancel)                       │ (Cancel)
     ▼                                ▼
[CANCELLED]                      [DRIVER_ARRIVING]
                                      │
                                      ▼
                                 [DRIVER_ARRIVED]
                                      │ (Verify OTP)
                                      ▼
                                  [STARTED]
                                      │ (Complete Ride)
                                      ▼
                                 [COMPLETED]
```

- **Immutability**: Once a ride is `STARTED`, it cannot be cancelled by the customer.
- **Terminal States**: `COMPLETED` and `CANCELLED` are immutable and cannot transition to any other status.
