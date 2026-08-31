import { useEffect, useState } from "react";
import api from "../api/axios";
import CarCard from "../components/CarCard";
import "./HomePage.css";

function HomePage() {
  const [cars, setCars] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchCars() {
      try {
        const response = await api.get("/cars/");
        setCars(response.data);
      } catch (error) {
        console.error("Failed to fetch cars:", error);
        setError("Failed to load cars.");
      } finally {
        setLoading(false);
      }
    }

    fetchCars();
  }, []);

  if (loading) {
    return (
      <div className="home-container">
        <div className="state-container">
          <div className="spinner"></div>
          <p>Loading available cars...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="home-container">
        <div className="state-container error-card">
          <p>{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="btn-retry"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="home-container">
      <header className="hero-section">
        <h1>Welcome to Movona</h1>
        <p className="hero-subtitle">
          Premium car rentals at your fingertips. Simple, fast, and transparent.
        </p>
      </header>

      <section className="fleet-section">
        <div className="section-header">
          <h2>Featured Fleet</h2>
          <span className="car-count">
            {cars.length} {cars.length === 1 ? "Vehicle" : "Vehicles"} Available
          </span>
        </div>

        {cars.length === 0 ? (
          <div className="state-container empty-card">
            <p>No cars currently in fleet. Please check back later.</p>
          </div>
        ) : (
          <div className="car-grid">
            {cars.map((car) => (
              <CarCard key={car.id} car={car} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default HomePage;
