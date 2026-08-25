Today 2:49 AM

Done. I created the first proper project documentation containing everything we've finalized so far, including the user system, profiles, vehicles, verification, ride lifecycle, OTP, live tracking, payments, refunds, ratings, admin, architecture, stack, and TBD decisions.

Download Movana_requirements_and_system_design.md

Put it in your project

Copy the file into:

Movona/
└── docs/
    └── requirements-and-system-design.md

Then from the project root:

git add docs/requirements-and-system-design.md
git commit -m "docs: add requirements and system design"
git push origin main

This gives us our first formal requirements baseline.

After that, we'll continue with the vehicle category seed data, then move into the Booking/Ride design. 

Movana_requirements_and_system_design.md
Document
that doesn't look good

You're right. The first version was too plain for a GitHub project document. GitHub was rendering the section titles almost like ordinary text, and the document was unnecessarily long.

I rebuilt it with a proper GitHub-friendly structure:

Clear # / ## / ### headings
Table of contents
Tables for requirements
Status markers
Architecture diagrams
Ride lifecycle flow
Technology stack table
Current progress
Open decisions/TBD section
Roadmap
Less repetitive text
Replace the old file

Download the improved version:

Download the improved requirements document

Replace:

docs/requirements-and-system-design.md

with this file.

Then:

git add docs/requirements-and-system-design.md
git commit -m "docs: improve system design documentation"
git push origin main

After refreshing GitHub, it should look much more like a proper software-project specification rather than a long text dump.

Also, I think this format is better for our workflow going forward: shorter documents, clear sections, tables where useful, and explicit TBD decisions. 

requirements-and-system-design.md
Document
write as md formating

Yes. You want the actual Markdown source, so when you open/edit the .md file you'll see the #, ##, | tables |, code blocks, etc.

Here is the Markdown content:

# Movana — Requirements & System Design

> **Version:** 0.1  
> **Status:** In development  
> **Scope:** Single-city launch  
> **Platform:** Car booking & ride-hailing

---

## 📌 Table of Contents

1. [Project Overview](#1-project-overview)
2. [Product Vision](#2-product-vision)
3. [Target Users](#3-target-users)
4. [Services](#4-services)
5. [User & Authentication](#5-user--authentication)
6. [Customer](#6-customer)
7. [Driver](#7-driver)
8. [Vehicle System](#8-vehicle-system)
9. [Ride Lifecycle](#9-ride-lifecycle)
10. [Payments & Refunds](#10-payments--refunds)
11. [Communication & Tracking](#11-communication--tracking)
12. [Ratings](#12-ratings)
13. [Admin](#13-admin)
14. [System Architecture](#14-system-architecture)
15. [Technology Stack](#15-technology-stack)
16. [Development Workflow](#16-development-workflow)
17. [Current Progress](#17-current-progress)
18. [Open Decisions](#18-open-decisions)
19. [Roadmap](#19-roadmap)

---

# 1. Project Overview

**Movana** is a transportation platform that connects customers with independent drivers who provide rides using their own vehicles.

The product is being designed as a realistic ride-hailing platform inspired by services such as Ola and Uber, while keeping the first release manageable.

### Initial Scope

- One city initially
- Independent drivers
- Driver-owned vehicles
- Customer and driver accounts
- Real-time ride lifecycle
- Payments and refunds
- Two-way ratings
- Administrative controls

The architecture should allow the platform to expand to additional cities and services later.

---

# 2. Product Vision

## Goal

Build a reliable platform where a customer can:

> **Choose a service → book a ride → get a driver → verify with OTP → track the ride → pay → rate the experience.**

At the same time, a driver should be able to:

> **Register → verify identity/vehicle → go online → accept rides → complete rides → receive earnings.**

## Design Principles

- Keep the booking experience simple.
- Verify drivers and vehicles before they can provide rides.
- Use explicit booking and ride states.
- Keep payment state separate from ride state.
- Record important events for disputes and support.
- Avoid collecting unnecessary personal information.
- Build the core ride flow before adding advanced services.

---

# 3. Target Users

| User | Purpose |
|---|---|
| Customer | Books transportation |
| Driver | Provides transportation using their own vehicle |
| Customer + Driver | One person may use both capabilities |
| Admin | Operates and manages the platform |

## Initial Customer Audience

The platform is intended for general users, including:

- Office commuters
- Students
- People travelling for work
- Travellers
- Local transportation users

There is no unnecessary restriction based on these categories.

---

# 4. Services

The home page will present available services using **card-style UI**.

## Planned Services

| Service | Initial Status |
|---|---|
| 🚗 Ride Now | **Core V1** |
| 🗓️ Scheduled Ride | Planned |
| ✈️ Airport Transfer | Planned |
| 🚘 Car Rental | Planned |
| 🏢 Corporate Travel | Planned |

The first implementation focuses on **Ride Now**.

---

# 5. User & Authentication

## 5.1 Account Model

One account can have multiple capabilities:

```text
                    USER
                      │
             ┌────────┴────────┐
             ↓                 ↓
        CUSTOMER            DRIVER
             │                 │
      CustomerProfile    DriverProfile
                               │
                               ↓
                            Vehicle

A user can therefore be:

Customer only
Driver only
Customer + Driver

Admin access is handled separately through Django permissions.

5.2 Authentication

Initial login requirement:

Email + password OR phone + password

Future
Phone OTP
Email verification
Phone verification
Optional multi-factor authentication
5.3 User Fields
Field	Purpose
Username	Django authentication/admin compatibility
First/Last name	Basic identity
Email	Login/contact
Phone	Login/contact
Password	Secure Django password hash
is_customer	Customer capability
is_driver	Driver capability
account_status	Active/Suspended/Deactivated
is_verified	Account verification
Created/Updated	Audit information
6. Customer
Customer Profile

A customer profile is linked one-to-one with a user.

Field	Rule
User	Required
Profile photo	Optional
Date of birth	Optional
Gender	Optional
Address	Optional
Average rating	System managed
Total rides	System managed

The customer registration process should remain quick and should not collect unnecessary information.

7. Driver
Driver Profile

A driver profile is linked one-to-one with a user.

Field	Rule
User	Required
Profile photo	Required before approval
Date of birth	Required/validated as applicable
Verification status	System managed
Availability	Offline / Online / Busy
Average rating	System managed
Completed rides	System managed
Driver Verification
PENDING
   ↓
APPROVED ─────→ SUSPENDED
   │
   └───────────→ REJECTED

A driver must satisfy platform verification requirements before receiving ride requests.

8. Vehicle System

Drivers bring their own vehicles.

8.1 Vehicle Rules
One driver can register multiple vehicles.
Each vehicle belongs to one driver.
Each vehicle has exactly one category.
Registration number is globally unique.
Only one vehicle per driver can be active for ride bookings.
Vehicle verification is separate from driver verification.
Only an approved + active vehicle can receive ride requests.
8.2 Vehicle Categories
Category	Purpose
Mini	Budget/local rides
Sedan	Standard rides
SUV	Larger groups/luggage
Premium	Premium experience
8.3 Vehicle Data
Field	Purpose
Driver	Vehicle owner/operator
Category	Mini/Sedan/SUV/Premium
Make	Manufacturer
Model	Vehicle model
Registration number	Unique vehicle identity
Colour	Vehicle identification
Seating capacity	Passenger capacity
Verification status	Pending/Approved/Rejected/Suspended
Active	Eligible for bookings
Created/Updated	Audit information
8.4 Vehicle Category Configuration

Each category can eventually contain:

Name
Description
Passenger capacity
Base fare
Per-km rate
Per-minute rate
Active/inactive status

Exact pricing is TBD.

9. Ride Lifecycle

The core V1 flow is:

CUSTOMER
   ↓
Select pickup
   ↓
Select destination
   ↓
Select vehicle/service
   ↓
Fare estimate
   ↓
BOOKING CREATED
   ↓
Driver receives request
   ↓
DRIVER ACCEPTS
   ↓
Driver travels to pickup
   ↓
DRIVER ARRIVED
   ↓
4-DIGIT OTP
   ↓
OTP VERIFIED
   ↓
RIDE STARTED
   ↓
LIVE TRACKING
   ↓
Driver reaches destination
   ↓
RIDE COMPLETED
   ↓
FINAL FARE
   ↓
PAYMENT
   ↓
RECEIPT
   ↓
DRIVER EARNING
   ↓
CUSTOMER ↔ DRIVER RATING
9.1 Driver Acceptance

Movana will use a driver acceptance model.

An eligible driver receives a booking request and explicitly accepts it.

The exact matching algorithm is TBD.

Potential matching factors:

Distance to pickup
Vehicle category
Driver availability
Estimated arrival time
Service area
Current ride status
9.2 OTP Ride Start

When the driver reaches pickup:

Driver selects Arrived.
Customer receives/reveals a 4-digit OTP.
Driver enters the OTP.
System verifies the OTP.
Ride changes to Started.

Important ride timestamps should be recorded.

10. Payments & Refunds
10.1 Payment Flow

Ride completion and payment are separate states.

RIDE COMPLETED
      ↓
FINAL FARE
      ↓
PAYMENT
      ↓
┌──────────────┬───────────────┐
↓              ↓
SUCCESS        FAILED/PENDING
↓              ↓
Receipt        Retry/Support
↓
Driver earning

A payment failure must not incorrectly change a completed ride back to an active ride.

10.2 Platform Charge

Conceptually:

Customer Fare
      ↓
Platform Service Charge
      ↓
Driver Earning

Exact commission/service-charge rules are TBD.

10.3 Cancellation & Refund

Possible cancellation situations:

Customer cancels before driver acceptance.
Customer cancels after driver acceptance.
Customer cancels after driver arrival.
Driver cancels.
Platform cancels.
Technical/system failure.
Refund Principles
Refund may be issued after applicable deductions.
Platform/service charges may be deducted where appropriate.
If the driver/platform is responsible for the failure, the customer should receive an appropriate refund.
Exact percentages and cancellation fees are TBD.
11. Communication & Tracking
11.1 Live Location
Driver Offline
     ↓
No active customer tracking

Booking Assigned
     ↓
Customer sees driver approaching

Ride Started
     ↓
Live ride tracking

Ride Completed
     ↓
Live ride tracking stops

Precise location should not be retained indefinitely without an operational/legal reason.

Maps provider is TBD.

11.2 Customer ↔ Driver Communication

Planned:

Platform call
In-app chat

Personal phone numbers should not be unnecessarily exposed.

Implementation/provider is TBD.

12. Ratings

Movana will use two-way ratings.

Customer ─────→ Driver
Driver   ─────→ Customer
Rating
1–5 stars
Optional comment

Ratings are aggregated into an overall user rating.

The design should reduce the possibility of retaliatory rating behavior.

13. Admin

The admin panel will eventually manage:

Users
View users
Suspend accounts
Deactivate accounts
Review verification
Drivers
Review applications
Approve/reject drivers
Suspend drivers
Vehicles
Approve/reject vehicles
Suspend vehicles
Manage categories
Bookings
View active/completed/cancelled rides
Investigate disputes
Payments
Review payment status
Process/review refunds
Investigate payment issues
Platform
Configure categories
Configure pricing
Manage service availability
14. System Architecture
Current Domain Structure
User
│
├── CustomerProfile
│
└── DriverProfile
       │
       ├── Vehicle
       │      └── VehicleCategory
       │
       └── DriverDocument (planned)
Future Core
CustomerProfile ─────┐
                     ↓
                   Booking
                     ↑
DriverProfile ───────┘
      │
      └── Vehicle

Booking
 ├── Payment
 ├── Refund
 ├── Rating
 ├── Notifications
 ├── Chat
 └── Tracking/Event History
15. Technology Stack
Layer	Technology	Status
Frontend	HTML	Active
Styling	CSS + Bootstrap	Planned/Active
Client-side logic	JavaScript	Planned
Backend	Python + Django	Active
API	Django REST Framework	Planned
Database	SQLite locally	Active
Production DB	PostgreSQL/MySQL	TBD
Real-time	WebSockets	Planned
Background jobs	Celery + Redis	Planned
Maps	Maps provider	TBD
Payments	Payment gateway	TBD
Version control	Git + GitHub	Active

React is not required for V1.

16. Development Workflow

Every feature follows:

DISCUSS
   ↓
DOCUMENT
   ↓
DESIGN
   ↓
IMPLEMENT
   ↓
CHECK
   ↓
MIGRATE
   ↓
TEST
   ↓
GIT COMMIT
   ↓
PUSH
Commit Examples
feat: add custom user authentication model
feat: add customer and driver profiles
feat: add vehicle and category models
docs: add requirements and system design

Small, meaningful commits are preferred.

17. Current Progress
✅ Completed
 Git repository initialized
 Python virtual environment
 Django project
 Django migrations
 Custom User model
 Customer/driver capabilities
 Django Admin
 CustomerProfile
 DriverProfile
 VehicleCategory
 Vehicle
 Vehicle Admin
 Requirements & system design document
🔄 Current Milestone

Vehicle category seed data

Next:

Booking/Ride system design

18. Open Decisions
Decision	Status
Initial city	TBD
Fare formula	TBD
Category pricing	TBD
Platform commission	TBD
Cancellation fees	TBD
Refund rules	Partially defined
Payment gateway	TBD
Maps provider	TBD
Driver matching	TBD
OTP delivery	TBD
Call provider	TBD
Chat implementation	TBD
Legal documents	TBD
Production database	TBD
Deployment	TBD

Keeping these as TBD prevents development assumptions from accidentally becoming final business requirements.

19. Roadmap
Phase 1 — Foundation
 Project setup
 Git workflow
 Django setup
 Authentication
 Customer profile
 Driver profile
 Vehicle system
 Vehicle category seed
Phase 2 — Core Booking
 Booking model
 Pickup/destination
 Vehicle selection
 Fare estimation
 Driver matching
 Driver acceptance
 Booking states
 Driver arrived
 OTP verification
 Ride start
 Ride completion
Phase 3 — Transaction
 Final fare
 Payment
 Receipt
 Driver earnings
 Cancellation
 Refunds
Phase 4 — Experience
 Live location
 Notifications
 Customer ↔ driver chat
 Platform calling
 Ratings
Phase 5 — Operations
 Driver documents
 Vehicle documents
 Verification workflows
 Disputes
 Admin controls
Phase 6 — Expansion
 Scheduled rides
 Airport transfers
 Rentals
 Corporate travel
 Multi-city
 Advanced analytics
Final Principle

Build the core ride lifecycle first. Add complexity only when the business flow requires it.

Movana is being developed as a real-world transportation platform, not just a CRUD demonstration.

Every important business action should eventually have:

Clear states
Validation
Authorization
Database records
Error handling
Tests
Appropriate administrative controls
Auditability where appropriate

Library
/
Car Booking
/
requirements-and-system-design.md
Movana --- Requirements & System Design {#movana--requirements--system-design}

Version: 0.1
Status: In development
Scope: Single-city launch
Platform: Car booking & ride-hailing

📌 Table of Contents {#pushpin-table-of-contents}
Project Overview
Product Vision
Target Users
Services
User & Authentication
Customer
Driver
Vehicle System
Ride Lifecycle
Payments & Refunds
Communication & Tracking
Ratings
Admin
System Architecture
Technology Stack
Development Workflow
Current Progress
Open Decisions
Roadmap
1. Project Overview {#1-project-overview}

Movana is a transportation platform that connects customers with
independent drivers who provide rides using their own vehicles.

The product is being designed as a realistic ride-hailing platform
inspired by services such as Ola and Uber, while keeping the first
release manageable:

One city initially
Independent drivers
Driver-owned vehicles
Customer and driver accounts
Real-time ride lifecycle
Payments and refunds
Two-way ratings
Administrative controls

The architecture should allow the platform to expand to additional
cities and services later.

2. Product Vision {#2-product-vision}
Goal

Build a reliable platform where a customer can:

Choose a service → book a ride → get a driver → verify with OTP →
track the ride → pay → rate the experience.

At the same time, a driver should be able to:

Register → verify identity/vehicle → go online → accept rides →
complete rides → receive earnings.

Design Principles
Keep the booking experience simple.
Verify drivers and vehicles before they can provide rides.
Use explicit booking/ride states.
Keep payment state separate from ride state.
Record important events for disputes and support.
Avoid collecting unnecessary personal information.
Build the core ride flow before adding advanced services.
3. Target Users {#3-target-users}

User Purpose

Customer Books transportation
Driver Provides transportation using their own vehicle
Customer + Driver One person may use both capabilities
Admin Operates and manages the platform

Initial Customer Audience

The platform is intended for general users, including:

Office commuters
Students
People travelling for work
Travellers
Local transportation users

There is no unnecessary restriction based on these categories.

4. Services {#4-services}

The home page will present available services using card-style UI.

Planned Services

Service Initial Status

🚗 Ride Now Core V1
🗓️ Scheduled Ride Planned
✈️ Airport Transfer Planned
🚘 Car Rental Planned
🏢 Corporate Travel Planned

The first implementation focuses on Ride Now.

5. User & Authentication {#5-user--authentication}
5.1 Account Model {#51-account-model}

One account can have multiple capabilities:

                    USER
                      │
             ┌────────┴────────┐
             ↓                 ↓
        CUSTOMER            DRIVER
             │                 │
      CustomerProfile    DriverProfile
                               │
                               ↓
                            Vehicle

A user can therefore be:

Customer only
Driver only
Customer + Driver

Admin access is handled separately through Django permissions.

5.2 Authentication {#52-authentication}

Initial login requirement:

Email + password OR phone + password

Future:

Phone OTP
Email verification
Phone verification
Optional multi-factor authentication
5.3 User Fields {#53-user-fields}

Field Purpose

Username Django authentication/admin compatibility
First/Last name Basic identity
Email Login/contact
Phone Login/contact
Password Secure Django password hash
is_customer Customer capability
is_driver Driver capability
account_status Active/Suspended/Deactivated
is_verified Account verification
Created/Updated Audit information

6. Customer {#6-customer}
Customer Profile

A customer profile is linked one-to-one with a user.

Field Rule

User Required
Profile photo Optional
Date of birth Optional
Gender Optional
Address Optional
Average rating System managed
Total rides System managed

The customer registration process should remain quick and should not
collect unnecessary information.

7. Driver {#7-driver}
Driver Profile

A driver profile is linked one-to-one with a user.

Field Rule

User Required
Profile photo Required before approval
Date of birth Required/validated as applicable
Verification status System managed
Availability Offline / Online / Busy
Average rating System managed
Completed rides System managed

Driver Verification
PENDING
   ↓
APPROVED ─────→ SUSPENDED
   │
   └───────────→ REJECTED

A driver must satisfy platform verification requirements before
receiving ride requests.

8. Vehicle System {#8-vehicle-system}

Drivers bring their own vehicles.

8.1 Vehicle Rules {#81-vehicle-rules}
One driver can register multiple vehicles.
Each vehicle belongs to one driver.
Each vehicle has exactly one category.
Registration number is globally unique.
Only one vehicle per driver can be active for ride bookings.
Vehicle verification is separate from driver verification.
Only an approved + active vehicle can receive ride requests.
8.2 Vehicle Categories {#82-vehicle-categories}

Category Purpose

Mini Budget/local rides
Sedan Standard rides
SUV Larger groups/luggage
Premium Premium experience

8.3 Vehicle Data {#83-vehicle-data}

Field Purpose

Driver Vehicle owner/operator
Category Mini/Sedan/SUV/Premium
Make Manufacturer
Model Vehicle model
Registration number Unique vehicle identity
Colour Vehicle identification
Seating capacity Passenger capacity
Verification status Pending/Approved/Rejected/Suspended
Active Eligible for bookings
Created/Updated Audit information

8.4 Vehicle Category Configuration {#84-vehicle-category-configuration}

Each category can eventually contain:

Name
Description
Passenger capacity
Base fare
Per-km rate
Per-minute rate
Active/inactive status

Exact pricing is TBD.

9. Ride Lifecycle {#9-ride-lifecycle}

The core V1 flow is:

CUSTOMER
   ↓
Select pickup
   ↓
Select destination
   ↓
Select vehicle/service
   ↓
Fare estimate
   ↓
BOOKING CREATED
   ↓
Driver receives request
   ↓
DRIVER ACCEPTS
   ↓
Driver travels to pickup
   ↓
DRIVER ARRIVED
   ↓
4-DIGIT OTP
   ↓
OTP VERIFIED
   ↓
RIDE STARTED
   ↓
LIVE TRACKING
   ↓
Driver reaches destination
   ↓
RIDE COMPLETED
   ↓
FINAL FARE
   ↓
PAYMENT
   ↓
RECEIPT
   ↓
DRIVER EARNING
   ↓
CUSTOMER ↔ DRIVER RATING
9.1 Driver Acceptance {#91-driver-acceptance}

Movana will use a driver acceptance model.

An eligible driver receives a booking request and explicitly accepts it.

The exact matching algorithm is TBD.

Potential matching factors:

Distance to pickup
Vehicle category
Driver availability
Estimated arrival time
Service area
Current ride status
9.2 OTP Ride Start {#92-otp-ride-start}

When the driver reaches pickup:

Driver selects Arrived.
Customer receives/reveals a 4-digit OTP.
Driver enters the OTP.
System verifies the OTP.
Ride changes to Started.

Important ride timestamps should be recorded.

10. Payments & Refunds {#10-payments--refunds}
10.1 Payment Flow {#101-payment-flow}

Ride completion and payment are separate states.

RIDE COMPLETED
      ↓
FINAL FARE
      ↓
PAYMENT
      ↓
┌──────────────┬───────────────┐
↓              ↓
SUCCESS        FAILED/PENDING
↓              ↓
Receipt        Retry/Support
↓
Driver earning

A payment failure must not incorrectly change a completed ride back to
an active ride.

10.2 Platform Charge {#102-platform-charge}

Conceptually:

Customer Fare
      ↓
Platform Service Charge
      ↓
Driver Earning

Exact commission/service-charge rules are TBD.

10.3 Cancellation & Refund {#103-cancellation--refund}

Possible cancellation situations:

Customer cancels before driver acceptance
Customer cancels after driver acceptance
Customer cancels after driver arrival
Driver cancels
Platform cancels
Technical/system failure

Refund principles discussed:

Refund may be issued after applicable deductions.
Platform/service charges may be deducted where appropriate.
If the driver/platform is responsible for the failure, the customer
should receive an appropriate refund.
Exact percentages and cancellation fees are TBD.
11. Communication & Tracking {#11-communication--tracking}
11.1 Live Location {#111-live-location}
Driver Offline
     ↓
No active customer tracking

Booking Assigned
     ↓
Customer sees driver approaching

Ride Started
     ↓
Live ride tracking

Ride Completed
     ↓
Live ride tracking stops

Precise location should not be retained indefinitely without an
operational/legal reason.

Maps provider is TBD.

11.2 Customer ↔ Driver Communication {#112-customer--driver-communication}

Planned:

Platform call
In-app chat

Personal phone numbers should not be unnecessarily exposed.

Implementation/provider is TBD.

12. Ratings {#12-ratings}

Movana will use two-way ratings.

Customer ─────→ Driver
Driver   ─────→ Customer
Rating
1--5 stars
Optional comment

Ratings are aggregated into an overall user rating.

The design should reduce the possibility of retaliatory rating behavior.

13. Admin {#13-admin}

The admin panel will eventually manage:

Users
View users
Suspend accounts
Deactivate accounts
Review verification
Drivers
Review applications
Approve/reject drivers
Suspend drivers
Vehicles
Approve/reject vehicles
Suspend vehicles
Manage categories
Bookings
View active/completed/cancelled rides
Investigate disputes
Payments
Review payment status
Process/review refunds
Investigate payment issues
Platform
Configure categories
Configure pricing
Manage service availability
14. System Architecture {#14-system-architecture}
Current Domain Structure
User
│
├── CustomerProfile
│
└── DriverProfile
       │
       ├── Vehicle
       │      └── VehicleCategory
       │
       └── DriverDocument (planned)
Future Core
CustomerProfile ─────┐
                     ↓
                   Booking
                     ↑
DriverProfile ───────┘
      │
      └── Vehicle

Booking
 ├── Payment
 ├── Refund
 ├── Rating
 ├── Notifications
 ├── Chat
 └── Tracking/Event History
15. Technology Stack {#15-technology-stack}

Layer Technology Status

Frontend HTML Active
Styling CSS + Bootstrap Planned/Active
Client-side logic JavaScript Planned
Backend Python + Django Active
API Django REST Framework Planned
Database SQLite locally Active
Production DB PostgreSQL/MySQL TBD
Real-time WebSockets Planned
Background jobs Celery + Redis Planned
Maps Maps provider TBD
Payments Payment gateway TBD
Version control Git + GitHub Active

React is not required for V1.

16. Development Workflow {#16-development-workflow}

Every feature follows:

DISCUSS
   ↓
DOCUMENT
   ↓
DESIGN
   ↓
IMPLEMENT
   ↓
CHECK
   ↓
MIGRATE
   ↓
TEST
   ↓
GIT COMMIT
   ↓
PUSH
Commit examples
feat: add custom user authentication model
feat: add customer and driver profiles
feat: add vehicle and category models
docs: add requirements and system design

Small, meaningful commits are preferred.

17. Current Progress {#17-current-progress}
✅ Completed {#white_check_mark-completed}

Git repository initialized

Python virtual environment

Django project

Django migrations

Custom User model

Customer/driver capabilities

Django Admin

CustomerProfile

DriverProfile

VehicleCategory

Vehicle

Vehicle Admin

Requirements & system design document

🔄 Current Milestone {#arrows_counterclockwise-current-milestone}

Vehicle category seed data

Then:

Booking/Ride system design

18. Open Decisions {#18-open-decisions}

Decision Status

Initial city TBD
Fare formula TBD
Category pricing TBD
Platform commission TBD
Cancellation fees TBD
Refund rules Partially defined
Payment gateway TBD
Maps provider TBD
Driver matching TBD
OTP delivery TBD
Call provider TBD
Chat implementation TBD
Legal documents TBD
Production database TBD
Deployment TBD

Keeping these as TBD prevents us from accidentally treating
development assumptions as final business requirements.

19. Roadmap {#19-roadmap}
PHASE 1 — FOUNDATION
├── Project setup                 ✅
├── Git workflow                  ✅
├── Django setup                  ✅
├── Authentication                ✅
├── Customer profile              ✅
├── Driver profile                ✅
├── Vehicle system                ✅
└── Vehicle category seed         🔄

PHASE 2 — CORE BOOKING
├── Booking model
├── Pickup/destination
├── Vehicle selection
├── Fare estimation
├── Driver matching
├── Driver acceptance
├── Booking states
├── Driver arrived
├── OTP verification
├── Ride start
└── Ride completion

PHASE 3 — TRANSACTION
├── Final fare
├── Payment
├── Receipt
├── Driver earnings
├── Cancellation
└── Refunds

PHASE 4 — EXPERIENCE
├── Live location
├── Notifications
├── Customer ↔ driver chat
├── Platform calling
└── Ratings

PHASE 5 — OPERATIONS
├── Driver documents
├── Vehicle documents
├── Verification workflows
├── Disputes
└── Admin controls

PHASE 6 — EXPANSION
├── Scheduled rides
├── Airport transfers
├── Rentals
├── Corporate travel
├── Multi-city
└── Advanced analytics
Final Principle

Build the core ride lifecycle first. Add complexity only when the
business flow requires it.

Movana is being developed as a real-world transportation platform, not
just a CRUD demonstration. Every important business action should
eventually have clear states, validation, authorization, database
records, error handling, tests, and appropriate administrative controls.