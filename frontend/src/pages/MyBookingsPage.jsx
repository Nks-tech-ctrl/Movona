import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/axios";
import "./MyBookingsPage.css";

const DEFAULT_CAR_IMG =
  "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=600&q=80";

function MyBookingsPage() {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [cancellingId, setCancellingId] = useState(null);
  const [actionMessage, setActionMessage] = useState("");

  async function fetchBookings() {
    try {
      setLoading(true);
      setError("");
      const response = await api.get("/bookings/");
      setBookings(response.data);
    } catch (err) {
      console.error("Error fetching bookings:", err);
      setError("Unable to load your bookings. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchBookings();
  }, []);

  async function handleCancel(bookingId) {
    const confirmCancel = window.confirm(
      "Are you sure you want to cancel this reservation?"
    );
    if (!confirmCancel) return;

    try {
      setCancellingId(bookingId);
      setActionMessage("");
      const response = await api.post(`/bookings/${bookingId}/cancel/`);

      // Update booking in local state
      setBookings((prev) =>
        prev.map((b) => (b.id === bookingId ? response.data : b))
      );
      setActionMessage("Reservation cancelled successfully.");
    } catch (err) {
      console.error("Cancellation error:", err);
      alert(
        err.response?.data?.detail || "Failed to cancel booking. Please try again."
      );
    } finally {
      setCancellingId(null);
    }
  }

  if (loading) {
    return (
      <div className="bookings-container">
        <div className="state-container">
          <div className="spinner"></div>
          <p>Loading your reservations...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bookings-container">
        <div className="state-container error-card">
          <p>{error}</p>
          <button onClick={fetchBookings} className="btn-retry">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bookings-container">
      <div className="bookings-header">
        <div>
          <h1>My Reservations</h1>
          <p className="subtitle">
            View, track, and manage all your car bookings.
          </p>
        </div>
        <Link to="/" className="btn-browse-cars">
          + Book Another Car
        </Link>
      </div>

      {actionMessage && (
        <div className="alert-success-banner">{actionMessage}</div>
      )}

      {bookings.length === 0 ? (
        <div className="empty-bookings-card">
          <div className="empty-icon">🚗</div>
          <h2>No Reservations Found</h2>
          <p>You haven't booked any cars yet. Explore our fleet today!</p>
          <Link to="/" className="btn-primary">
            Explore Available Cars
          </Link>
        </div>
      ) : (
        <div className="bookings-list">
          {bookings.map((booking) => {
            const car = booking.car || {};
            const isCancellable =
              booking.booking_status === "CONFIRMED" ||
              booking.booking_status === "PENDING";

            return (
              <div key={booking.id} className="booking-item-card">
                <div className="booking-card-main">
                  <div className="booking-image-wrapper">
                    <img
                      src={car.image_url || DEFAULT_CAR_IMG}
                      alt={`${car.brand || "Car"} ${car.model || ""}`}
                      className="booking-car-img"
                    />
                  </div>

                  <div className="booking-details-content">
                    <div className="booking-top-row">
                      <div>
                        <span className="booking-id-tag">
                          Booking #{booking.id}
                        </span>
                        <h3 className="booking-car-title">
                          {car.brand} {car.model}
                        </h3>
                        <p className="booking-car-sub">
                          {car.year} &bull; {car.color} &bull; {car.license_plate}
                        </p>
                      </div>

                      <span
                        className={`booking-status-badge status-${booking.booking_status?.toLowerCase()}`}
                      >
                        {booking.booking_status}
                      </span>
                    </div>

                    <div className="booking-info-grid">
                      <div className="info-cell">
                        <span className="cell-label">📍 Pickup</span>
                        <span className="cell-value">
                          {booking.pickup_location}
                        </span>
                        <span className="cell-date">
                          📅 {booking.pickup_date}
                        </span>
                      </div>

                      <div className="info-cell">
                        <span className="cell-label">🏁 Dropoff</span>
                        <span className="cell-value">
                          {booking.dropoff_location}
                        </span>
                        <span className="cell-date">
                          📅 {booking.return_date}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="booking-card-footer">
                  <div className="booking-fare">
                    <span className="fare-label">Total Amount Paid</span>
                    <span className="fare-value">₹{booking.total_price}</span>
                  </div>

                  <div className="booking-actions">
                    <Link
                      to={`/cars/${car.id}`}
                      className="btn-view-car"
                    >
                      View Car
                    </Link>
                    {isCancellable && (
                      <button
                        onClick={() => handleCancel(booking.id)}
                        className="btn-cancel-booking"
                        disabled={cancellingId === booking.id}
                      >
                        {cancellingId === booking.id
                          ? "Cancelling..."
                          : "Cancel Booking"}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default MyBookingsPage;
