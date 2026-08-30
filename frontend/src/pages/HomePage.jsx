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
    return <p>Loading cars...</p>;
  }

  if (error) {
    return <p>{error}</p>;
  }

  return (
    <div>
      <h1>Welcome to Movona</h1>
      <p>Your ride, your way.</p>

      <h2>Available Cars</h2>

      {cars.length === 0 ? (
        <p>No cars available.</p>
      ) : (
       <div className="car-grid">
        {cars.map((car)=>(
          <CarCard key={car.id} car={car}/>
        ))} 
       </div>
      )}
    </div>
  );
}

export default HomePage;
