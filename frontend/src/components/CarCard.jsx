import "./CarCard.css";
function CarCard({ car }) {
  return (
    <div className="car-card">
      <h3>
        {car.brand} {car.model}
      </h3>

      <p>Year: {car.year}</p>
      <p>Color: {car.color}</p>
      <p>Seats: {car.seats}</p>
      <p>Price per day: ₹{car.price_per_day}</p>
    </div>
  );
}

export default CarCard;