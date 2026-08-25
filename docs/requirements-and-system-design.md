1. Project Overview

Movana is a ride-hailing and transportation platform inspired by
real-world services such as Ola and Uber.

The platform connects customers who need transportation with independent
drivers who provide rides using their own vehicles.

The initial implementation will target a single city. The architecture
should remain flexible enough to expand to additional cities and
services later.

2. Product Goals

The initial goals are:

Provide a simple way for customers to book transportation.

Allow independent drivers to use their own vehicles.

Provide driver and vehicle verification.

Support an end-to-end ride lifecycle.

Provide transparent fare and payment handling.

Provide customer and driver ratings.

Give administrators control over users, drivers, vehicles, bookings,
payments, and disputes.

Build the system using a maintainable full-stack architecture.

3. Target Users

3.1 Common Customers

The platform is intended for people such as:

Office commuters

Students

People travelling for work

General travellers

People requiring local transportation

The initial product should not unnecessarily restrict users based on
these categories.

3.2 Drivers

Drivers are independent service providers who bring and operate their
own vehicles.

3.3 Administrators

Administrators manage the platform, verification, disputes, users,
vehicles, pricing configuration, and operational issues.

4. Initial Geographic Scope

The first release will operate in one city.

The city itself is TBD.

The system should be designed so additional cities can be added later
without redesigning the entire application.

5. Services

The home page should present available transportation services using
card-style UI.

Initial service concepts include:

Ride Now

Scheduled Ride

Airport Transfer

Car Rental

Corporate Travel

The first development milestone will focus on the core Ride Now
flow.

Other services will be added after the core ride system is stable.

6. User Account Architecture

A single user account can support multiple capabilities.

A person may be:

Customer

Driver

Customer + Driver

Administrator access will use Django's built-in staff/superuser and
permission system.

Initial User Information

Username

First name

Last name

Email

Phone

Password

Customer capability

Driver capability

Account status

Verification status

Created timestamp

Updated timestamp

Account Status

Active

Suspended

Deactivated

Email and phone numbers are intended to be unique.

Passwords must be handled using Django's secure authentication/password
hashing system.

7. Authentication

Initial authentication requirement:

Email + password OR phone + password

Future enhancement:

Phone OTP authentication

Phone verification

Email verification

Multi-factor authentication if required

8. Customer Profile

A customer profile is linked one-to-one with the user account.

Initial information:

User

Profile photo --- optional

Date of birth --- optional

Gender --- optional

Address --- optional

Average rating --- system managed

Total rides --- system managed

The platform should avoid collecting unnecessary personal information.

9. Driver Profile

A driver profile is linked one-to-one with the user account.

Initial information:

User

Profile photo --- required before driver approval

Date of birth

Driver verification status

Availability status

Average rating --- system managed

Completed rides --- system managed

Driver Verification Status

Pending

Approved

Rejected

Driver Availability

Offline

Online

Busy

A driver should not receive ride requests unless the driver and active
vehicle satisfy the platform's verification requirements.

10. Vehicle System

Drivers may register multiple vehicles.

Each vehicle:

Belongs to one driver

Has exactly one vehicle category

Has a unique registration number

Has its own verification status

Can be active or inactive

Only one vehicle belonging to a driver should be active for ride
bookings at a time.

Initial Vehicle Categories

Mini

Sedan

SUV

Premium

Pricing values are currently TBD.

Vehicle Information

Driver

Category

Make

Model

Registration number

Colour

Seating capacity

Verification status

Active status

Created timestamp

Updated timestamp

Vehicle Verification

Pending

Approved

Rejected

Suspended

Only an approved and active vehicle should be eligible for ride
matching.

11. Vehicle Category

A vehicle category represents the service category selected by a
customer.

Each category can contain:

Name

Description

Passenger capacity

Base fare

Per-kilometre rate

Per-minute rate

Active/inactive status

Initial pricing is intentionally not finalized.

12. Driver & Vehicle Documents

Documents should eventually be represented separately from the basic
driver and vehicle models.

Potential driver documents:

Driving licence

Identity document

Other legally required documents

Potential vehicle documents:

Registration

Insurance

Other required vehicle documents

Each document may eventually contain:

Document type

File/reference

Verification status

Issue date

Expiry date

Verification timestamp

Exact document requirements are TBD based on the target city's
regulations and business requirements.

13. Core Ride Lifecycle

The core Ride Now flow is:

Customer
    ↓
Select pickup and destination
    ↓
Select service/category
    ↓
Fare estimate
    ↓
Book ride
    ↓
Driver receives request
    ↓
Driver accepts
    ↓
Driver travels to pickup
    ↓
Driver marks Arrived
    ↓
Customer receives/reveals OTP
    ↓
OTP verification
    ↓
Ride Started
    ↓
Live tracking
    ↓
Driver reaches destination
    ↓
Driver ends ride
    ↓
Final fare calculated
    ↓
Payment
    ↓
Receipt
    ↓
Driver earning recorded
    ↓
Customer ↔ Driver rating

14. Driver Acceptance

The platform will use a driver acceptance model.

A booking request is sent to an eligible driver.

The driver must explicitly accept the request.

The exact driver matching/dispatch algorithm is TBD.

Potential future matching factors:

Distance from pickup

Vehicle category

Driver availability

Driver status

Current workload

Service area

Estimated arrival time

15. Driver Arrival and OTP

When the driver reaches the pickup location:

Driver marks the booking as Arrived.

Customer receives/reveals a 4-digit ride OTP.

Driver enters the OTP.

System validates the OTP.

Ride becomes Started.

The OTP helps confirm that the correct customer and driver are connected
before starting the ride.

Ride timestamps should be recorded for important lifecycle events.

16. Live Location

Live location should be available during an active booking.

General states:

No active booking
    ↓
No customer ride tracking

Assigned
    ↓
Customer can see driver approaching

Ride started
    ↓
Customer receives live ride tracking

Ride completed
    ↓
Live ride tracking stops

Precise location data should not be retained indefinitely without a
valid operational or legal reason.

The maps/location provider is TBD.

17. Payment

The physical ride should be marked as completed when the ride ends.

Payment is a separate state.

Example:

Ride Completed
      ↓
Final Fare
      ↓
Payment
      ↓
Payment Successful
      ↓
Receipt + Driver Earning

If payment fails:

Ride Completed
      ↓
Payment Failed/Pending
      ↓
Retry / Alternate Payment / Support

This prevents a payment failure from incorrectly making a completed
physical ride appear incomplete.

Payment gateway is TBD.

18. Platform Charges and Driver Earnings

The platform may deduct a service/platform charge from the ride amount
before calculating driver earnings.

Exact commission/service-charge rules are TBD.

Conceptually:

Customer Fare
      ↓
Platform Service Charge
      ↓
Driver Earning

Exact tax handling, commissions, and settlement rules require business
and legal decisions before production use.

19. Cancellation and Refund Principles

The platform should support cancellation at different stages.

Potential cancellation states include:

Customer cancelled before driver acceptance

Customer cancelled after driver acceptance

Customer cancelled after driver arrival

Driver cancelled

Platform cancelled

Ride cancelled due to technical/system issue

Refund principles discussed:

Customer may receive a refund after applicable deductions.

Service/platform charges may be deducted where applicable.

If cancellation or failure is clearly caused by the driver/platform,
the customer should receive an appropriate refund.

Exact refund percentages and cancellation fees are TBD.

These rules should eventually be implemented as explicit business rules
rather than hard-coded scattered conditions.

20. Customer and Driver Communication

For an active booking, the customer and driver should be able to
communicate through the platform.

Planned features:

Platform call

In-app chat

Exact provider/implementation is TBD.

Personal contact details should not be unnecessarily exposed to either
party.

21. Ratings

The platform will support two-way ratings.

Customer → Driver
Driver   → Customer

Rating:

1--5 stars

Optional comment

Ratings should be aggregated to produce an overall user rating.

The system should minimize rating retaliation by handling individual
ratings appropriately.

22. Refund and Dispute Handling

The platform should maintain records needed to investigate disputes.

Potential dispute information:

Booking

Customer

Driver

Ride timestamps

Payment status

Cancellation reason

Relevant communication/event records

Refund decision

Admin decision

Administrators should be able to review and resolve disputes.

23. Admin Responsibilities

The admin system should eventually support:

Users

View users

Suspend accounts

Deactivate accounts

Review verification status

Drivers

Review driver applications

Approve/reject verification

Suspend drivers

Vehicles

Review vehicles

Approve/reject vehicles

Suspend vehicles

Manage categories

Bookings

View active/completed/cancelled rides

Investigate ride issues

Payments

View payment status

Review refunds

Handle payment disputes

Platform Configuration

Manage vehicle categories

Manage pricing

Manage service availability

24. Initial Database Architecture

Current foundation:

User
 │
 ├── CustomerProfile
 │
 └── DriverProfile
        │
        └── Vehicle
               │
               └── VehicleCategory

Future core booking architecture:

User
 │
 ├── CustomerProfile
 └── DriverProfile
        │
        └── Vehicle

CustomerProfile
        │
        ↓
      Booking
        ↑
        │
DriverProfile
        │
        ↓
      Vehicle

Future related models are expected to include:

Booking

BookingStatus/Event history

Payment

Refund

Rating

DriverDocument

VehicleDocument

Notification

ChatMessage

Location/Tracking records where required

25. Technology Stack

Frontend

HTML

CSS

JavaScript

Bootstrap

React is not required for the initial version.

Backend

Python

Django

Django REST Framework --- planned when API architecture is
introduced

Database

A production relational database will be selected between PostgreSQL and
MySQL.

Local development currently uses SQLite.

Future Infrastructure

Potential future components:

Redis

Celery

WebSockets

Docker

Cloud/VPS deployment

These will be introduced only when the project requires them.

26. Development Workflow

The project follows:

Discuss
   ↓
Document
   ↓
Design
   ↓
Implement
   ↓
Check
   ↓
Migrate
   ↓
Test
   ↓
Git Commit
   ↓
Push

Git should use small, meaningful commits.

Examples:

feat: add custom user authentication model
feat: add customer and driver profiles
feat: add vehicle and category models

27. Current Project Status

Completed:

Project repository initialized

Python virtual environment created

Django installed

Django project created

Initial migrations applied

Custom User model created

Customer/driver capability model created

Django Admin configured

CustomerProfile created

DriverProfile created

VehicleCategory created

Vehicle created

Vehicle Admin configured

Git checkpoints created

Current next milestone:

Seed default vehicle categories, then design and implement the
Booking/Ride system.

28. Items Still To Be Decided

Initial city

Exact vehicle pricing

Fare calculation formula

Platform service charge/commission

Cancellation fee rules

Refund percentages

Payment gateway

Maps provider

Driver matching algorithm

OTP delivery method

Call provider

Chat implementation

Notification system

Legal/document requirements

Data retention policy

Production database

Deployment infrastructure

These should be decided before the corresponding production feature is
implemented.

29. Guiding Principle

Movana should be built as a real-world transportation platform rather
than a simple CRUD demonstration.

Each important business action should have:

Clear state transitions

Validation

Authorization

Database records

Error handling

Auditability where appropriate

Tests

Appropriate admin controls