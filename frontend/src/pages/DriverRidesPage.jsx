import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import driverApi from "../api/driverApi";
import "./DriverRidesPage.css";

const STATUS_FILTERS = [
  { label: "All Rides", value: "" },
  { label: "Active", value: "ACTIVE" },
  { label: "Completed", value: "COMPLETED" },
  { label: "Cancelled", value: "CANCELLED" },
];

function DriverRidesPage() {
  const [rides, setRides] = useState([]);
  const [activeTab, setActiveTab] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function fetchRides(filterValue) {
    try {
      setLoading(true);
      setError("");

      let apiStatus = "";
      if (filterValue === "COMPLETED") apiStatus = "COMPLETED";
      if (filterValue === "CANCELLED") apiStatus = "CANCELLED";

      const res = await driverApi.getMyRides(apiStatus);
      let data = res.data || [];

      if (filterValue === "ACTIVE") {
        const activeStatuses = [
          "ACCEPTED",
          "DRIVER_ARRIVING",
          "DRIVER_ARRIVED",
          "STARTED",
        ];
        data = data.filter((r) => activeStatuses.includes(r.status));
      }

      setRides(data);
    } catch (err) {
      console.error("Error fetching driver rides:", err);
      setError("Unable to load rides. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchRides(activeTab);
  }, [activeTab]);

  return (
    <div className="driver-rides-container">
      <div className="driver-rides-header">
        <div>
          <h1>My Assigned Rides</h1>
          <p className="subtitle">
            Track your ongoing trips and review your past completed rides.
          </p>
        </div>
        <Link to="/driver/dashboard" className="btn-back-dashboard">
          &larr; Driver Dashboard
        </Link>
      </div>

      {/* Filter Tabs */}
      <div className="filter-tabs">
        {STATUS_FILTERS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => setActiveTab(tab.value)}
            className={`filter-tab ${activeTab === tab.value ? "active" : ""}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="state-container">
          <div className="spinner"></div>
          <p>Loading your assigned rides...</p>
        </div>
      ) : error ? (
        <div className="state-container error-card">
          <p>{error}</p>
          <button onClick={() => fetchRides(activeTab)} className="btn-retry">
            Try Again
          </button>
        </div>
      ) : rides.length === 0 ? (
        <div className="empty-rides-card">
          <div className="empty-icon">🚖</div>
          <h2>No Rides Found</h2>
          <p>You don't have any rides in this status category.</p>
          <Link to="/driver/dashboard" className="btn-find-rides">
            Find Available Rides
          </Link>
        </div>
      ) : (
        <div className="driver-rides-list">
          {rides.map((ride) => {
            const isCompleted = ride.status === "COMPLETED";
            const isCancelled = ride.status === "CANCELLED";
            const isActive = !isCompleted && !isCancelled;

            return (
              <div key={ride.id} className="driver-ride-item-card">
                <div className="ride-card-header">
                  <div>
                    <span className="ride-id-tag">Trip #{ride.id}</span>
                    <span className="ride-category-badge">
                      {ride.category?.name || "Ride"}
                    </span>
                  </div>
                  <span
                    className={`status-pill status-${ride.status?.toLowerCase()}`}
                  >
                    {ride.status?.replace("_", " ")}
                  </span>
                </div>

                <div className="ride-route-info">
                  <div className="route-stop">
                    <span className="marker green">●</span>
                    <div>
                      <span className="stop-title">Pickup Location</span>
                      <p className="stop-address">{ride.pickup_address}</p>
                    </div>
                  </div>

                  <div className="route-stop">
                    <span className="marker red">●</span>
                    <div>
                      <span className="stop-title">Destination</span>
                      <p className="stop-address">{ride.destination_address}</p>
                    </div>
                  </div>
                </div>

                <div className="ride-meta-footer">
                  <div className="fare-box">
                    <span className="fare-label">
                      {isCompleted ? "Final Fare" : "Estimated Fare"}
                    </span>
                    <span className="fare-amount">
                      ₹{isCompleted ? ride.final_fare : ride.estimated_fare}
                    </span>
                  </div>

                  <div className="ride-trip-metrics">
                    <span>📍 {ride.estimated_distance_km} km</span>
                    <span>⏱ ~{ride.estimated_duration_minutes} mins</span>
                  </div>

                  <div className="ride-actions">
                    <Link
                      to={`/driver/rides/${ride.id}`}
                      className={`btn-action-view ${isActive ? "btn-active-flow" : ""}`}
                    >
                      {isActive ? "Continue Trip &rarr;" : "View Details"}
                    </Link>
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

export default DriverRidesPage;
