import { Routes, Route } from "react-router-dom";
import ProtectedRoute from "./ProtectedRoute";
import DriverRoute from "./DriverRoute";

import BookingPage from "../pages/BookingPage";
import CarDetailsPage from "../pages/CarDetailsPage";
import DriverDashboardPage from "../pages/DriverDashboardPage";
import DriverProfilePage from "../pages/DriverProfilePage";
import DriverRideDetailsPage from "../pages/DriverRideDetailsPage";
import DriverRidesPage from "../pages/DriverRidesPage";
import DriverVehiclesPage from "../pages/DriverVehiclesPage";
import HomePage from "../pages/HomePage";
import LoginPage from "../pages/LoginPage";
import MyBookingsPage from "../pages/MyBookingsPage";
import NotFoundPage from "../pages/NotFoundPage";
import RegisterPage from "../pages/RegisterPage";

function AppRoutes() {
  return (
    <Routes>
      {/* Customer & Rental Fleet Routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <HomePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/cars/:id"
        element={
          <ProtectedRoute>
            <CarDetailsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/cars/:id/book"
        element={
          <ProtectedRoute>
            <BookingPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/my-bookings"
        element={
          <ProtectedRoute>
            <MyBookingsPage />
          </ProtectedRoute>
        }
      />

      {/* Driver Portal Protected Routes */}
      <Route
        path="/driver/dashboard"
        element={
          <DriverRoute>
            <DriverDashboardPage />
          </DriverRoute>
        }
      />
      <Route
        path="/driver/rides"
        element={
          <DriverRoute>
            <DriverRidesPage />
          </DriverRoute>
        }
      />
      <Route
        path="/driver/rides/:id"
        element={
          <DriverRoute>
            <DriverRideDetailsPage />
          </DriverRoute>
        }
      />
      <Route
        path="/driver/vehicles"
        element={
          <DriverRoute>
            <DriverVehiclesPage />
          </DriverRoute>
        }
      />
      <Route
        path="/driver/profile"
        element={
          <DriverRoute>
            <DriverProfilePage />
          </DriverRoute>
        }
      />

      {/* Auth & Public Routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

export default AppRoutes;
