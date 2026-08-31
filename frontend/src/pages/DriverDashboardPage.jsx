import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import driverApi from "../api/driverApi";
import "./DriverDashboardPage.css";

function DriverDashboardPage() {
  const navigate = useNavigate();

  const [profile, setProfile] = useState(null);
  const [eligibleRides, setEligibleRides] = useState([]);
  const [activeRide, setActiveRide] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionSuccess, setActionSuccess] = useState("");

  const [togglingStatus, setTogglingStatus] = useState(false);
  const [acceptingId, setAcceptingId] = useState(null);

  async function loadDashboardData() {
    try {
      setLoading(true);
      setError("");

      const [profileRes, eligibleRes, ridesRes] = await Promise.all([
        driverApi.getProfile(),
        driverApi.getEligibleRides().catch(() => ({ data: [] })),
        driverApi.getMyRides().catch(() => ({ data: [] })),
      ]);

      setProfile(profileRes.data);
      setEligibleRides(eligibleRes.data || []);

      // Check if driver has an active in-progress ride
      const activeStatuses = [
        "ACCEPTED",
        "DRIVER_ARRIVING",
        "DRIVER_ARRIVED",
        "STARTED",
      ];
      const currentActive = (ridesRes.data || []).find((r) =>
        activeStatuses.includes(r.status),
      );
      setActiveRide(currentActive || null);
    } catch (err) {
      console.error("Failed to load driver dashboard data:", err);
      setError(
        err.response?.data?.detail ||
          "Unable to load driver dashboard. Please check your network connection.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboardData();
  }, []);

  async function handleToggleAvailability() {
    if (!profile) return;
    if (profile.verification_status !== "APPROVED") {
      alert("Only approved drivers can toggle availability.");
      return;
    }
    if (profile.availability_status === "BUSY") {
      alert("Cannot change status while on an active ride.");
      return;
    }

    const nextStatus =
      profile.availability_status === "ONLINE" ? "OFFLINE" : "ONLINE";

    try {
      setTogglingStatus(true);
      setActionSuccess("");
      const res = await driverApi.updateProfile({
        availability_status: nextStatus,
      });
      setProfile(res.data);
      setActionSuccess(
        `Your status is now ${nextStatus === "ONLINE" ? "Online (Receiving Rides)" : "Offline"}.`,
      );

      // Refresh eligible rides
      if (nextStatus === "ONLINE") {
        const eligibleRes = await driverApi.getEligibleRides();
        setEligibleRides(eligibleRes.data || []);
      } else {
        setEligibleRides([]);
      }
    } catch (err) {
      console.error("Availability toggle failed:", err);
      alert(
        err.response?.data?.availability_status?.[0] ||
          err.response?.data?.detail ||
          "Failed to update availability status.",
      );
    } finally {
      setTogglingStatus(false);
    }
  }

  async function handleAcceptRide(rideId) {
    try {
      setAcceptingId(rideId);
      setActionSuccess("");
      await driverApi.acceptRide(rideId);
      navigate(`/driver/rides/${rideId}`);
    } catch (err) {
      console.error("Accept ride failed:", err);
      const msg =
        err.response?.data?.detail ||
        "Could not accept ride. It may have been taken by another driver.";
      alert(msg);
      loadDashboardData();
    } finally {
      setAcceptingId(null);
    }
  }

  if (loading) {
    return (
      <div className="driver-dashboard-container">
        <div className="dashboard-loading">
          <div className="spinner"></div>
          <p>Loading driver portal...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="driver-dashboard-container">
        <div className="dashboard-error-card">
          <h2>Driver Portal Error</h2>
          <p>{error}</p>
          <button onClick={loadDashboardData} className="btn-retry">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  const isOnline = profile?.availability_status === "ONLINE";
  const isBusy = profile?.availability_status === "BUSY";
  const isApproved = profile?.verification_status === "APPROVED";

  return (
    <div className="driver-dashboard-container">
      {/* Header Banner */}
      <div className="driver-header-card">
        <div className="driver-header-info">
          <h1>Welcome, {profile?.username || "Driver"}!</h1>
          <p className="driver-subtitle">
            Manage your rides, track active requests, and configure your
            availability.
          </p>
          <div className="driver-badges">
            <span
              className={`badge-verification badge-verif-${profile?.verification_status?.toLowerCase()}`}
            >
              {profile?.verification_status === "APPROVED"
                ? "✓ Verified Driver"
                : `Verification: ${profile?.verification_status}`}
            </span>
            <span
              className={`badge-status badge-status-${profile?.availability_status?.toLowerCase()}`}
            >
              ● {profile?.availability_status}
            </span>
          </div>
        </div>

        <div className="driver-header-actions">
          {isApproved ? (
            <button
              onClick={handleToggleAvailability}
              className={`btn-availability ${isOnline ? "btn-go-offline" : "btn-go-online"}`}
              disabled={togglingStatus || isBusy}
            >
              {togglingStatus
                ? "Updating..."
                : isBusy
                  ? "On Active Ride"
                  : isOnline
                    ? "Go Offline"
                    : "Go Online"}
            </button>
          ) : (
            <div className="approval-notice">
              ⚠️ Driver profile is pending administrator approval.
            </div>
          )}
        </div>
      </div>

      {actionSuccess && (
        <div className="alert-success-banner">{actionSuccess}</div>
      )}

      {/* Stats Row */}
      <div className="driver-stats-grid">
        <div className="stat-card">
          <span className="stat-icon">🏁</span>
          <div className="stat-details">
            <span className="stat-value">{profile?.completed_rides || 0}</span>
            <span className="stat-label">Completed Rides</span>
          </div>
        </div>

        <div className="stat-card">
          <span className="stat-icon">⭐</span>
          <div className="stat-details">
            <span className="stat-value">
              {Number(profile?.average_rating || 0).toFixed(2)}
            </span>
            <span className="stat-label">Driver Rating</span>
          </div>
        </div>

        <div className="stat-card">
          <span className="stat-icon">⚡</span>
          <div className="stat-details">
            <span className="stat-value">{eligibleRides.length}</span>
            <span className="stat-label">Eligible Nearby Rides</span>
          </div>
        </div>
      </div>

      {/* Active Ride Callout */}
      {activeRide && (
        <div className="active-ride-banner">
          <div className="active-ride-info">
            <span className="active-ride-tag">Active Ride in Progress</span>
            <h3>
              Trip #{activeRide.id} &bull; {activeRide.status.replace("_", " ")}
            </h3>
            <p>
              <strong>Pickup:</strong> {activeRide.pickup_address}
            </p>
            <p>
              <strong>Destination:</strong> {activeRide.destination_address}
            </p>
          </div>
          <div className="active-ride-action">
            <button
              onClick={() => navigate(`/driver/rides/${activeRide.id}`)}
              className="btn-continue-ride"
            >
              Continue Ride &rarr;
            </button>
          </div>
        </div>
      )}

      {/* Eligible Rides Section */}
      <div className="dashboard-section">
        <div className="section-header">
          <div>
            <h2>Available Ride Requests</h2>
            <p className="section-subtitle">
              Instant ride requests matching your approved vehicle categories.
            </p>
          </div>
          <button
            onClick={loadDashboardData}
            className="btn-refresh"
            title="Refresh ride requests"
          >
            ↻ Refresh Feed
          </button>
        </div>

        {!isOnline ? (
          <div className="empty-state-card offline-feed">
            <div className="empty-icon">💤</div>
            <h3>You are Currently Offline</h3>
            <p>Go online above to start receiving live passenger requests.</p>
          </div>
        ) : eligibleRides.length === 0 ? (
          <div className="empty-state-card">
            <div className="empty-icon">🔍</div>
            <h3>No Pending Rides Right Now</h3>
            <p>
              We'll notify you as soon as new ride requests are created nearby.
            </p>
          </div>
        ) : (
          <div className="eligible-rides-grid">
            {eligibleRides.map((ride) => (
              <div key={ride.id} className="ride-card">
                <div className="ride-card-top">
                  <span className="ride-category-pill">
                    {ride.category?.name || "Standard Ride"}
                  </span>
                  <span className="ride-fare">₹{ride.estimated_fare}</span>
                </div>

                <div className="ride-locations">
                  <div className="location-item">
                    <span className="dot dot-green"></span>
                    <div>
                      <span className="loc-label">Pickup</span>
                      <p className="loc-text">{ride.pickup_address}</p>
                    </div>
                  </div>

                  <div className="location-item">
                    <span className="dot dot-red"></span>
                    <div>
                      <span className="loc-label">Destination</span>
                      <p className="loc-text">{ride.destination_address}</p>
                    </div>
                  </div>
                </div>

                <div className="ride-meta-row">
                  <span>📍 {ride.estimated_distance_km} km</span>
                  <span>⏱ ~{ride.estimated_duration_minutes} mins</span>
                </div>

                <div className="ride-card-actions">
                  <button
                    onClick={() => handleAcceptRide(ride.id)}
                    className="btn-accept-ride"
                    disabled={acceptingId === ride.id}
                  >
                    {acceptingId === ride.id ? "Accepting..." : "Accept Ride"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Navigation Cards */}
      <div className="dashboard-quick-links">
        <Link to="/driver/rides" className="quick-link-card">
          <div className="quick-icon">📋</div>
          <div>
            <h3>Ride History</h3>
            <p>View all completed, accepted, and past rides.</p>
          </div>
          <span className="arrow">&rarr;</span>
        </Link>

        <Link to="/driver/vehicles" className="quick-link-card">
          <div className="quick-icon">🚗</div>
          <div>
            <h3>My Vehicles</h3>
            <p>Manage registered vehicles and view approvals.</p>
          </div>
          <span className="arrow">&rarr;</span>
        </Link>

        <Link to="/driver/profile" className="quick-link-card">
          <div className="quick-icon">👤</div>
          <div>
            <h3>Driver Profile</h3>
            <p>View ratings, verification, and personal information.</p>
          </div>
          <span className="arrow">&rarr;</span>
        </Link>
      </div>
    </div>
  );
}

export default DriverDashboardPage;
