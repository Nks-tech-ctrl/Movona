import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import driverApi from "../api/driverApi";
import "./DriverRideDetailsPage.css";

function DriverRideDetailsPage() {
  const { id } = useParams();

  const [ride, setRide] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionMessage, setActionMessage] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  // OTP Form state
  const [otp, setOtp] = useState("");
  const [otpError, setOtpError] = useState("");

  // Rating Form state
  const [ratingScore, setRatingScore] = useState(5);
  const [feedback, setFeedback] = useState("");
  const [ratingSubmitted, setRatingSubmitted] = useState(false);
  const [ratingLoading, setRatingLoading] = useState(false);

  async function loadRide() {
    try {
      setLoading(true);
      setError("");
      const res = await driverApi.getRideDetail(id);
      setRide(res.data);
    } catch (err) {
      console.error("Error loading ride details:", err);
      setError(
        err.response?.data?.detail ||
          "Unable to load ride details. Please verify the ride exists and is assigned to you.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (id) {
      loadRide();
    }
  }, [id]);

  async function handleMarkArriving() {
    try {
      setActionLoading(true);
      setActionMessage("");
      const res = await driverApi.markArriving(id);
      setRide(res.data);
      setActionMessage("Status updated: Heading to pickup location.");
    } catch (err) {
      console.error("Error marking arriving:", err);
      alert(err.response?.data?.detail || "Failed to update ride status.");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleMarkArrived() {
    try {
      setActionLoading(true);
      setActionMessage("");
      const res = await driverApi.markArrived(id);
      setRide(res.data);
      setActionMessage(
        "Status updated: You have arrived at pickup. Ask the customer for their OTP.",
      );
    } catch (err) {
      console.error("Error marking arrived:", err);
      alert(err.response?.data?.detail || "Failed to update ride status.");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleVerifyOtp(e) {
    e.preventDefault();
    if (!otp.trim() || otp.trim().length !== 4) {
      setOtpError("Please enter a valid 4-digit OTP.");
      return;
    }

    try {
      setActionLoading(true);
      setOtpError("");
      const res = await driverApi.startRide(id, otp.trim());
      setRide(res.data);
      setOtp("");
      setActionMessage("OTP verified successfully! Ride has started.");
    } catch (err) {
      console.error("Error verifying OTP:", err);
      setOtpError(
        err.response?.data?.detail ||
          "Invalid OTP. Please verify with the customer.",
      );
    } finally {
      setActionLoading(false);
    }
  }

  async function handleCompleteRide() {
    const confirmComplete = window.confirm(
      "Are you sure you want to complete this ride?",
    );
    if (!confirmComplete) return;

    try {
      setActionLoading(true);
      setActionMessage("");
      const res = await driverApi.completeRide(id);
      setRide(res.data);
      setActionMessage("Ride completed successfully!");
    } catch (err) {
      console.error("Error completing ride:", err);
      alert(err.response?.data?.detail || "Failed to complete ride.");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleRatePassenger(e) {
    e.preventDefault();
    try {
      setRatingLoading(true);
      await driverApi.ratePassenger(id, ratingScore, feedback.trim());
      setRatingSubmitted(true);
      setActionMessage("Thank you! Passenger rating submitted.");
    } catch (err) {
      console.error("Error rating passenger:", err);
      alert(
        err.response?.data?.detail ||
          err.response?.data?.rating?.[0] ||
          "Failed to submit rating.",
      );
    } finally {
      setRatingLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="ride-details-container">
        <div className="state-card loading">
          <div className="spinner"></div>
          <p>Loading ride details...</p>
        </div>
      </div>
    );
  }

  if (error || !ride) {
    return (
      <div className="ride-details-container">
        <div className="state-card error">
          <h2>Ride Not Found</h2>
          <p>{error || "Could not find the requested ride."}</p>
          <Link to="/driver/rides" className="btn-back">
            &larr; Back to My Rides
          </Link>
        </div>
      </div>
    );
  }

  const customer = ride.customer?.user || {};
  const status = ride.status;

  return (
    <div className="ride-details-container">
      {/* Top Breadcrumb Header */}
      <div className="details-header">
        <div>
          <Link to="/driver/rides" className="back-link">
            &larr; All Assigned Rides
          </Link>
          <h1>Trip #{ride.id}</h1>
          <p className="details-sub">
            Category: {ride.category?.name || "Standard"} &bull; Requested:{" "}
            {new Date(ride.created_at || ride.requested_at).toLocaleString()}
          </p>
        </div>

        <span className={`status-pill-lg status-${status.toLowerCase()}`}>
          {status.replace("_", " ")}
        </span>
      </div>

      {actionMessage && (
        <div className="alert-action-success">{actionMessage}</div>
      )}

      {/* Main Lifecycle Control Action Card */}
      <div className="lifecycle-action-card">
        <h2>Trip Status & Progression</h2>

        {status === "ACCEPTED" && (
          <div className="stage-action-box">
            <p className="stage-desc">
              You have accepted this ride. When you start driving towards the
              pickup location, click below:
            </p>
            <button
              onClick={handleMarkArriving}
              className="btn-lifecycle-primary"
              disabled={actionLoading}
            >
              {actionLoading ? "Updating..." : "🚗 Start Heading to Pickup"}
            </button>
          </div>
        )}

        {status === "DRIVER_ARRIVING" && (
          <div className="stage-action-box">
            <p className="stage-desc">
              You are en route to the pickup spot. When you arrive at the
              passenger's location, click below:
            </p>
            <button
              onClick={handleMarkArrived}
              className="btn-lifecycle-primary"
              disabled={actionLoading}
            >
              {actionLoading ? "Updating..." : "📍 I Have Arrived at Pickup"}
            </button>
          </div>
        )}

        {status === "DRIVER_ARRIVED" && (
          <div className="stage-action-box otp-stage">
            <div className="otp-instructions">
              <span className="key-icon">🔑</span>
              <div>
                <h3>Verify Passenger OTP</h3>
                <p>
                  Ask the passenger for their 4-digit Start OTP to begin the
                  trip.
                </p>
              </div>
            </div>

            {otpError && <div className="otp-alert-error">{otpError}</div>}

            <form onSubmit={handleVerifyOtp} className="otp-form">
              <input
                type="text"
                maxLength={4}
                placeholder="4-digit OTP"
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
                className="otp-input"
                required
              />
              <button
                type="submit"
                className="btn-verify-otp"
                disabled={actionLoading || otp.length !== 4}
              >
                {actionLoading ? "Verifying..." : "✓ Verify & Start Ride"}
              </button>
            </form>
          </div>
        )}

        {status === "STARTED" && (
          <div className="stage-action-box active-trip-box">
            <div className="trip-in-progress-info">
              <span className="live-pulse">🟢</span>
              <div>
                <h3>Trip in Progress</h3>
                <p>
                  Drive safely to the passenger's destination. When you reach,
                  click below to finalize the ride.
                </p>
              </div>
            </div>
            <button
              onClick={handleCompleteRide}
              className="btn-complete-ride"
              disabled={actionLoading}
            >
              {actionLoading ? "Completing..." : "🏁 Complete Ride"}
            </button>
          </div>
        )}

        {status === "COMPLETED" && (
          <div className="stage-action-box completed-box">
            <div className="completed-header">
              <span className="check-icon">✓</span>
              <div>
                <h3>Ride Successfully Completed!</h3>
                <p>
                  Final Fare:{" "}
                  <strong>₹{ride.final_fare || ride.estimated_fare}</strong>
                </p>
              </div>
            </div>

            {!ratingSubmitted ? (
              <form onSubmit={handleRatePassenger} className="rate-driver-form">
                <h4>Rate Passenger</h4>
                <div className="star-selector">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      className={`star-btn ${ratingScore >= star ? "star-active" : ""}`}
                      onClick={() => setRatingScore(star)}
                    >
                      ★
                    </button>
                  ))}
                  <span className="rating-num-label">{ratingScore} / 5</span>
                </div>

                <textarea
                  placeholder="Optional passenger feedback..."
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                  rows={2}
                  className="feedback-textarea"
                />

                <button
                  type="submit"
                  className="btn-submit-rating"
                  disabled={ratingLoading}
                >
                  {ratingLoading ? "Submitting..." : "Submit Passenger Rating"}
                </button>
              </form>
            ) : (
              <div className="rating-thank-you">
                ⭐ Passenger rated successfully.
              </div>
            )}
          </div>
        )}

        {status === "CANCELLED" && (
          <div className="stage-action-box cancelled-box">
            <h3>Ride Cancelled</h3>
            <p>
              <strong>Cancelled by:</strong> {ride.cancelled_by || "System"}
            </p>
            {ride.cancellation_reason && (
              <p>
                <strong>Reason:</strong> {ride.cancellation_reason}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Grid: Route & Passenger Info */}
      <div className="details-grid">
        {/* Route Details Card */}
        <div className="card-section">
          <h2>Trip Route</h2>

          <div className="route-flow">
            <div className="route-node">
              <span className="node-marker green">●</span>
              <div>
                <span className="node-label">Pickup Location</span>
                <p className="node-text">{ride.pickup_address}</p>
                <span className="coord-text">
                  GPS: ({Number(ride.pickup_latitude).toFixed(4)},{" "}
                  {Number(ride.pickup_longitude).toFixed(4)})
                </span>
              </div>
            </div>

            <div className="route-node">
              <span className="node-marker red">●</span>
              <div>
                <span className="node-label">Destination Location</span>
                <p className="node-text">{ride.destination_address}</p>
                <span className="coord-text">
                  GPS: ({Number(ride.destination_latitude).toFixed(4)},{" "}
                  {Number(ride.destination_longitude).toFixed(4)})
                </span>
              </div>
            </div>
          </div>

          <div className="metrics-box">
            <div className="metric">
              <span className="metric-lbl">Distance</span>
              <span className="metric-val">
                {ride.estimated_distance_km} km
              </span>
            </div>
            <div className="metric">
              <span className="metric-lbl">Est. Duration</span>
              <span className="metric-val">
                {ride.estimated_duration_minutes} mins
              </span>
            </div>
            <div className="metric">
              <span className="metric-lbl">Fare</span>
              <span className="metric-val fare-highlight">
                ₹{ride.final_fare || ride.estimated_fare}
              </span>
            </div>
          </div>
        </div>

        {/* Passenger & Vehicle Card */}
        <div className="card-section">
          <h2>Passenger & Vehicle</h2>

          <div className="info-list">
            <div className="info-row">
              <span className="info-lbl">Passenger</span>
              <span className="info-val">
                {customer.username || "Customer"}
              </span>
            </div>

            {customer.phone && (
              <div className="info-row">
                <span className="info-lbl">Contact Phone</span>
                <span className="info-val">{customer.phone}</span>
              </div>
            )}

            <div className="info-row">
              <span className="info-lbl">Vehicle Category</span>
              <span className="info-val">
                {ride.category?.name || "Standard"}
              </span>
            </div>

            {ride.vehicle && (
              <>
                <div className="info-row">
                  <span className="info-lbl">Assigned Vehicle</span>
                  <span className="info-val">
                    {ride.vehicle.make} {ride.vehicle.model} (
                    {ride.vehicle.registration_number})
                  </span>
                </div>
                <div className="info-row">
                  <span className="info-lbl">Vehicle Color</span>
                  <span className="info-val">{ride.vehicle.colour}</span>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default DriverRideDetailsPage;
