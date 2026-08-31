import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import api from "../api/axios";
import "./CarDetailsPage.css";

const DEFAULT_CAR_IMG = "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=1200&q=80";

function CarDetailsPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [car, setCar] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [imgError, setImgError] = useState(false);

  useEffect(() => {
    async function fetchCarDetails() {
      try {
        setLoading(true);
        setError("");
        const response = await api.get(`/cars/${id}/`);
        setCar(response.data);
      } catch (err) {
        console.error("Failed to load car details:", err);
        if (err.response && err.response.status === 404) {
          setError(
            "Car not found. It may have been removed or does not exist.",
          );
        } else {
          setError("Unable to load car details. Please try again later.");
        }
      } finally {
        setLoading(false);
      }
    }

    if (id) {
      fetchCarDetails();
    }
  }, [id]);

  if (loading) {
    return (
      <div className="car-details-container">
        <div className="car-details-card loading-state">
          <p>Loading car details...</p>
        </div>
      </div>
    );
  }

  if (error || !car) {
    return (
      <div className="car-details-container">
        <div className="car-details-card error-state">
          <h2>Oops!</h2>
          <p>{error || "Car not found."}</p>
          <Link to="/" className="btn-back">
            &larr; Back to Cars
          </Link>
        </div>
      </div>
    );
  }

  const displayImage = !imgError && car.image_url ? car.image_url : DEFAULT_CAR_IMG;

  return (
    <div className="car-details-container">
      <div className="car-details-card">
        <div className="car-details-hero">
          <img
            src={displayImage}
            alt={`${car.brand} ${car.model}`}
            className="car-details-img"
            onError={() => setImgError(true)}
          />
          <span
            className={`status-pill-overlay ${
              car.is_available ? "status-available" : "status-booked"
            }`}
          >
            {car.is_available ? "Available for Rent" : "Currently Booked"}
          </span>
        </div>

        <div className="car-details-header">
          <div>
            <h1 className="car-title">
              {car.brand} {car.model}
            </h1>
            <p className="car-subtitle">Model Year: {car.year}</p>
          </div>
        </div>

        <div className="car-info-grid">
          <div className="info-item">
            <span className="info-label">Brand</span>
            <span className="info-value">{car.brand}</span>
          </div>

          <div className="info-item">
            <span className="info-label">Model</span>
            <span className="info-value">{car.model}</span>
          </div>

          <div className="info-item">
            <span className="info-label">Year</span>
            <span className="info-value">{car.year}</span>
          </div>

          <div className="info-item">
            <span className="info-label">Color</span>
            <span className="info-value">{car.color}</span>
          </div>

          <div className="info-item">
            <span className="info-label">Seating Capacity</span>
            <span className="info-value">{car.seats} Seats</span>
          </div>

          <div className="info-item">
            <span className="info-label">Registration</span>
            <span className="info-value">{car.license_plate}</span>
          </div>
        </div>

        <div className="pricing-section">
          <div>
            <span className="pricing-label">Daily Rental Rate</span>
            <div className="pricing-amount">
              ₹{car.price_per_day} <span>/ day</span>
            </div>
          </div>

          <div className="car-actions">
            <Link to="/" className="btn-secondary">
              &larr; Back to Cars
            </Link>
            {car.is_available ? (
              <button
                onClick={() => navigate(`/cars/${car.id}/book`)}
                className="btn-primary"
              >
                Book Now
              </button>
            ) : (
              <button disabled className="btn-disabled">
                Unavailable
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default CarDetailsPage;
