import { Routes, Route } from "react-router-dom";
import ProtectedRoute from "./ProtectedRoute";

import BookingPage from "../pages/BookingPage";
import CarDetailsPage from "../pages/CarDetailsPage";
import HomePage from "../pages/HomePage";
import LoginPage from "../pages/LoginPage";
import NotFoundPage from "../pages/NotFoundPage";
import RegisterPage from "../pages/RegisterPage";

function AppRoutes() {
  return (
    <Routes>
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
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}


export default AppRoutes;
