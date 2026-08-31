import { Link } from "react-router-dom";
import "./CarCard.css";

function CarCard({ car }) {
  return (
    <div className="car-card">
      <div className="car-card-header">
        <h3>
          {car.brand} {car.model}
        </h3>
        <span
          className={`availability-badge ${
            car.is_available ? "available" : "unavailable"
          }`}
        >
          {car.is_available ? "Available" : "Booked"}
        </span>
      </div>

      <p>Year: {car.year}</p>
      <p>Color: {car.color}</p>
      <p>Seats: {car.seats}</p>
      <p className="price-tag">Price per day: ₹{car.price_per_day}</p>

      <div className="car-card-actions">
        <Link to={`/cars/${car.id}`} className="btn-view-details">
          View Details
        </Link>
      </div>
    </div>
  );
}

export default CarCard;