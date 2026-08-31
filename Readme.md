# Movona — Urban Mobility & Car Rental Platform

Movona is a modern, modular, full-stack mobility platform built with **Django REST Framework** on the backend and **React (Vite)** on the frontend. It provides both on-demand ride dispatching (with driver matching, OTP ride verification, fare calculation, and ratings) and a full-featured vehicle rental booking system.

---

## 🚀 Key Features

### 🚗 Vehicle Fleet & Car Rental

- **Fleet Showcase**: Browse available vehicles with images, model year, seating capacity, color, and daily rates.
- **Detailed Specifications**: Detailed vehicle profile with real-time availability badges and pricing.
- **Secure Reservation Engine**:
  - Validates date ranges and restricts reservations on unavailable or overlapping dates.
  - Server-side authoritative price calculation (`rental_days * price_per_day`).
  - Ownership isolation for all user bookings.
- **Booking Management (`/my-bookings`)**:
  - Live status tracking (`CONFIRMED`, `PENDING`, `COMPLETED`, `CANCELLED`).
  - Self-service booking cancellation with instant status updates.

### 🚕 On-Demand Ride Dispatch & Driver Lifecycle

- **Custom User Architecture**: Multi-role system supporting Customers, Drivers, and Administrators.
- **JWT Authentication**: Secure token-based auth with automatic token refresh interceptors.
- **Ride Request & Estimation**: Haversine distance-based dynamic fare calculations.
- **Driver Match & Discovery**: Radius-based search for pending rides.
- **Full Ride Lifecycle**:
  1. Customer requests ride $\rightarrow$ `REQUESTED`
  2. Driver accepts ride $\rightarrow$ `ACCEPTED`
  3. Driver is en-route $\rightarrow$ `ARRIVING`
  4. Driver arrives at pickup $\rightarrow$ `ARRIVED`
  5. OTP Verification $\rightarrow$ `IN_PROGRESS`
  6. Ride Completion $\rightarrow$ `COMPLETED`
  7. Post-ride rating & reviews $\rightarrow$ 1-5 stars

---

## 🛠️ Technology Stack

| Layer               | Technologies                                                    |
| :------------------ | :-------------------------------------------------------------- |
| **Backend**         | Python 3.12+, Django 6.0, Django REST Framework 3.16            |
| **Auth & Security** | `djangorestframework-simplejwt`, Django PBKDF2 Password Hasher  |
| **Database**        | SQLite (Production-ready relational schema)                     |
| **Frontend**        | React 19, Vite, React Router DOM 7, Axios                       |
| **Styling**         | Modern CSS with Responsive Flexbox/Grid, Mobile-Friendly UI     |
| **Testing**         | Django `APITestCase`, Fast test hasher suite (165 tests in <5s) |

---

## 📂 Project Architecture

```
Movona/
├── backend/
│   ├── accounts/             # User auth, CustomerProfile, DriverProfile
│   ├── cars/                 # Car model, CarBooking model, serializers, views, tests
│   ├── config/               # Django settings, test settings, root URLs
│   ├── rides/                # VehicleCategory, Booking (rides), Ratings, services
│   └── manage.py
├── frontend/
│   ├── src/
│   │   ├── api/              # Axios instance with JWT interceptors
│   │   ├── components/       # Navbar, Footer, CarCard
│   │   ├── context/          # AuthContext & AuthProvider
│   │   ├── pages/            # HomePage, CarDetailsPage, BookingPage, MyBookingsPage, Login, Register
│   │   └── routes/           # AppRoutes, ProtectedRoute
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## ⚡ Quick Start & Installation

### Prerequisites

- Python 3.10+
- Node.js 18+ and npm

---

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create & activate virtual environment (if not already active)
python -m venv ../venv
# Windows:
..\venv\Scripts\activate
# Linux/macOS:
source ../venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# (Optional) Run automated test suite (165 tests)
python manage.py test --settings=config.settings_test

# Start backend development server
python manage.py runserver
```

Backend will be live at `http://127.0.0.1:8000/`.

---

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Start frontend development server
npm run dev
```

Frontend will be live at `http://localhost:5173/`.

---

## 📡 REST API Reference

### Authentication & Profiles

| Method | Endpoint                   | Description                        | Auth Required |
| :----- | :------------------------- | :--------------------------------- | :------------ |
| `POST` | `/api/auth/register/`      | Register customer account          | No            |
| `POST` | `/api/auth/token/`         | Obtain JWT access and refresh pair | No            |
| `POST` | `/api/auth/token/refresh/` | Refresh expired access token       | No            |
| `GET`  | `/api/customers/me/`       | Get current customer profile       | Yes           |
| `GET`  | `/api/drivers/me/`         | Get current driver profile         | Yes (Driver)  |

### Car Rental & Fleet

| Method | Endpoint                     | Description                            | Auth Required |
| :----- | :--------------------------- | :------------------------------------- | :------------ |
| `GET`  | `/api/cars/`                 | List all vehicles in fleet             | No            |
| `GET`  | `/api/cars/<id>/`            | Retrieve vehicle details               | No            |
| `GET`  | `/api/bookings/`             | List authenticated user's reservations | Yes           |
| `POST` | `/api/bookings/`             | Create a new car reservation           | Yes           |
| `GET`  | `/api/bookings/<id>/`        | Retrieve specific reservation          | Yes           |
| `POST` | `/api/bookings/<id>/cancel/` | Cancel reservation                     | Yes           |

### On-Demand Rides & Dispatch

| Method | Endpoint                           | Description                          | Auth Required |
| :----- | :--------------------------------- | :----------------------------------- | :------------ |
| `POST` | `/api/rides/fare-estimate/`        | Calculate distance and fare estimate | No            |
| `POST` | `/api/rides/book/`                 | Book on-demand ride                  | Yes           |
| `GET`  | `/api/rides/`                      | List customer ride history           | Yes           |
| `GET`  | `/api/rides/<id>/`                 | Get ride details                     | Yes           |
| `POST` | `/api/rides/<id>/cancel/`          | Cancel on-demand ride                | Yes           |
| `GET`  | `/api/rides/driver/available/`     | Driver discovery for nearby rides    | Yes (Driver)  |
| `POST` | `/api/rides/driver/<id>/accept/`   | Accept ride                          | Yes (Driver)  |
| `POST` | `/api/rides/driver/<id>/arriving/` | Mark driver en-route                 | Yes (Driver)  |
| `POST` | `/api/rides/driver/<id>/arrived/`  | Mark driver arrived                  | Yes (Driver)  |
| `POST` | `/api/rides/driver/<id>/start/`    | Verify customer OTP & start ride     | Yes (Driver)  |
| `POST` | `/api/rides/driver/<id>/complete/` | Complete ride                        | Yes (Driver)  |
| `POST` | `/api/rides/<id>/rate/`            | Submit customer rating and review    | Yes           |

---

## 🧪 Testing

Movona includes a comprehensive automated test suite covering authentication, permissions, edge cases, date validation, and ownership isolation.

To run the complete test suite:

```bash
cd backend
..\venv\Scripts\python.exe manage.py test --settings=config.settings_test
```

**Results**: `165 passed in ~4.5s`.

---

## 📄 License & Open-Source Compliance

This project is built 100% using free and open-source libraries and public assets without requiring any paid third-party APIs or subscription services.
