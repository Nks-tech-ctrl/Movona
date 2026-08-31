import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import api from "../api/axios";
import "./BookingPage.css";

const DEFAULT_CAR_IMG =
  "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=800&q=80";

function BookingPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [car, setCar] = useState(null);
  const [loadingCar, setLoadingCar] = useState(true);
  const [carError, setCarError] = useState("");

  const today = new Date().toISOString().split("T")[0];
  const tomorrow = new Date(Date.now() + 86400000).toISOString().split("T")[0];
  const threeDaysLater = new Date(Date.now() + 86400000 * 3)
    .toISOString()
    .split("T")[0];

  const [pickupLocation, setPickupLocation] = useState("");
  const [dropoffLocation, setDropoffLocation] = useState("");
  const [pickupDate, setPickupDate] = useState(tomorrow);
  const [returnDate, setReturnDate] = useState(threeDaysLater);
  const [submitting, setSubmitting] = useState(false);
  const [apiError, setApiError] = useState("");

  useEffect(() => {
    async function fetchCar() {
      try {
        setLoadingCar(true);
        setCarError("");
        const response = await api.get(`/cars/${id}/`);
        setCar(response.data);
      } catch (err) {
        console.error("Error loading car:", err);
        setCarError("Could not load car information.");
      } finally {
        setLoadingCar(false);
      }
    }

    if (id) {
      fetchCar();
    }
  }, [id]);

  // Calculate rental duration in days
  const start = new Date(pickupDate);
  const end = new Date(returnDate);
  const diffTime = end - start;
  const rentalDays = diffTime > 0 ? Math.ceil(diffTime / (1000 * 60 * 60 * 24)) : 0;
  const estimatedTotal =
    car && rentalDays > 0 ? (rentalDays * parseFloat(car.price_per_day)).toFixed(2) : 0;

  async function handleSubmit(e) {
    e.preventDefault();
    setApiError("");

    if (!pickupLocation.trim() || !dropoffLocation.trim()) {
      setApiError("Please enter both pickup and dropoff locations.");
      return;
    }

    if (rentalDays <= 0) {
      setApiError("Return date must be strictly after pickup date.");
      return;
    }

    try {
      setSubmitting(true);
      const payload = {
        car_id: car.id,
        pickup_location: pickupLocation.trim(),
        dropoff_location: dropoffLocation.trim(),
        pickup_date: pickupDate,
        return_date: returnDate,
      };

      await api.post("/bookings/", payload);
      navigate("/my-bookings");
    } catch (err) {
      console.error("Booking error:", err);
      if (err.response && err.response.data) {
        const data = err.response.data;
        if (data.detail) {
          setApiError(data.detail);
        } else if (typeof data === "object") {
          const firstKey = Object.keys(data)[0];
          const msg = Array.isArray(data[firstKey]) ? data[firstKey][0] : data[firstKey];
          setApiError(`${firstKey}: ${msg}`);
        } else {
          setApiError("Failed to complete booking. Please check details.");
        }
      } else {
        setApiError("Unable to connect to server. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (loadingCar) {
    return (
      <div className="booking-container">
        <div className="booking-card loading-state">
          <p>Loading booking details...</p>
        </div>
      </div>
    );
  }

  if (carError || !car) {
    return (
      <div className="booking-container">
        <div className="booking-card error-state">
          <h2>Vehicle Not Found</h2>
          <p>{carError || "The selected car is unavailable."}</p>
          <Link to="/" className="btn-back">
            &larr; Back to Fleet
          </Link>
        </div>
      </div>
    );
  }

  if (!car.is_available) {
    return (
      <div className="booking-container">
        <div className="booking-card error-state">
          <h2>Car Currently Booked</h2>
          <p>
            {car.brand} {car.model} is currently marked unavailable for new bookings.
          </p>
          <Link to="/" className="btn-back">
            &larr; Choose Another Car
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="booking-container">
      <div className="booking-layout">
        {/* Car Summary Sidebar Card */}
        <div className="booking-summary-card">
          <img
            src={car.image_url || DEFAULT_CAR_IMG}
            alt={`${car.brand} ${car.model}`}
            className="summary-car-img"
          />
          <div className="summary-car-body">
            <h3>
              {car.brand} {car.model}
            </h3>
            <p className="summary-car-meta">
              {car.year} &bull; {car.color} &bull; {car.seats} Seats
            </p>
            <div className="summary-rate">
              <span className="summary-rate-label">Daily Rental Rate</span>
              <span className="summary-rate-value">₹{car.price_per_day} / day</span>
            </div>

            {rentalDays > 0 && (
              <div className="rental-calculation">
                <div className="calc-row">
                  <span>Duration</span>
                  <span>
                    {rentalDays} {rentalDays === 1 ? "Day" : "Days"}
                  </span>
                </div>
                <div className="calc-row">
                  <span>Rate</span>
                  <span>₹{car.price_per_day} &times; {rentalDays}</span>
                </div>
                <div className="calc-row total-row">
                  <span>Estimated Total</span>
                  <span className="calc-total">₹{estimatedTotal}</span>
                </div>
                <p className="calc-note">
                  *Final fare calculated and verified securely by backend.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Booking Form */}
        <div className="booking-form-card">
          <h1>Reserve Your Car</h1>
          <p className="form-subtitle">
            Enter your trip details to confirm your reservation.
          </p>

          {apiError && <div className="form-alert-error">{apiError}</div>}

          <form onSubmit={handleSubmit} className="reservation-form">
            <div className="form-group">
              <label htmlFor="pickupLocation">Pickup Location *</label>
              <input
                id="pickupLocation"
                type="text"
                placeholder="e.g. Terminal 3 Airport, Connaught Place"
                value={pickupLocation}
                onChange={(e) => setPickupLocation(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="dropoffLocation">Dropoff Location *</label>
              <input
                id="dropoffLocation"
                type="text"
                placeholder="e.g. Cyber City Gurgaon, Hotel Novotel"
                value={dropoffLocation}
                onChange={(e) => setDropoffLocation(e.target.value)}
                required
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="pickupDate">Pickup Date *</label>
                <input
                  id="pickupDate"
                  type="date"
                  min={today}
                  value={pickupDate}
                  onChange={(e) => setPickupDate(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="returnDate">Return Date *</label>
                <input
                  id="returnDate"
                  type="date"
                  min={pickupDate || today}
                  value={returnDate}
                  onChange={(e) => setReturnDate(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="form-actions">
              <Link to={`/cars/${car.id}`} className="btn-cancel">
                Cancel
              </Link>
              <button
                type="submit"
                className="btn-confirm-booking"
                disabled={submitting}
              >
                {submitting ? "Confirming Reservation..." : "Confirm & Book Now"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default BookingPage;
