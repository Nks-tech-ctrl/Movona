import { useState } from "react";
import { Link } from "react-router-dom";
import "./CarCard.css";

const DEFAULT_CAR_IMG = "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=600&q=80";

function CarCard({ car }) {
  const [imgError, setImgError] = useState(false);

  const displayImage = !imgError && car.image_url ? car.image_url : DEFAULT_CAR_IMG;

  return (
    <div className="car-card">
      <div className="car-card-image-wrapper">
        <img
          src={displayImage}
          alt={`${car.brand} ${car.model}`}
          className="car-card-img"
          onError={() => setImgError(true)}
          loading="lazy"
        />
        <span
          className={`availability-badge-overlay ${
            car.is_available ? "available" : "unavailable"
          }`}
        >
          {car.is_available ? "Available" : "Booked"}
        </span>
      </div>

      <div className="car-card-body">
        <div className="car-card-header">
          <h3>
            {car.brand} {car.model}
          </h3>
          <span className="car-year-badge">{car.year}</span>
        </div>

        <div className="car-meta-list">
          <span>🎨 {car.color}</span>
          <span>👥 {car.seats} Seats</span>
        </div>

        <div className="car-card-footer">
          <div>
            <span className="rate-label">Daily Rate</span>
            <p className="price-tag">₹{car.price_per_day}</p>
          </div>
          <Link to={`/cars/${car.id}`} className="btn-view-details">
            View Details
          </Link>
        </div>
      </div>
    </div>
  );
}

export default CarCard;
