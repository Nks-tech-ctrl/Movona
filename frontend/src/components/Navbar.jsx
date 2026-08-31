import { useContext, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { AuthContext } from "../context/AuthContent";
import "./Navbar.css";

function Navbar() {
  const { user, logoutUser } = useContext(AuthContext);
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  function handleLogout() {
    logoutUser();
    setMobileMenuOpen(false);
    navigate("/login");
  }

  function closeMenu() {
    setMobileMenuOpen(false);
  }

  return (
    <header className="navbar-header">
      <div className="navbar-container">
        <Link to="/" className="navbar-logo" onClick={closeMenu}>
          <span className="logo-icon">🚗</span>
          <span className="logo-text">Movona</span>
        </Link>

        <button
          className="mobile-menu-btn"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle navigation menu"
        >
          {mobileMenuOpen ? "✕" : "☰"}
        </button>

        <nav className={`navbar-nav ${mobileMenuOpen ? "nav-open" : ""}`}>
          <div className="nav-links">
            <Link
              to="/"
              className={`nav-link ${location.pathname === "/" ? "active" : ""}`}
              onClick={closeMenu}
            >
              Fleet
            </Link>

            {user && (
              <Link
                to="/my-bookings"
                className={`nav-link ${
                  location.pathname === "/my-bookings" ? "active" : ""
                }`}
                onClick={closeMenu}
              >
                My Reservations
              </Link>
            )}
          </div>

          <div className="nav-auth">
            {user ? (
              <div className="user-menu">
                <span className="user-badge">
                  <span className="user-avatar">👤</span>
                  <span className="user-name">{user.username}</span>
                </span>

                <button onClick={handleLogout} className="btn-logout">
                  Logout
                </button>
              </div>
            ) : (
              <div className="guest-links">
                <Link
                  to="/login"
                  className={`btn-nav-login ${
                    location.pathname === "/login" ? "active" : ""
                  }`}
                  onClick={closeMenu}
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="btn-nav-register"
                  onClick={closeMenu}
                >
                  Register
                </Link>
              </div>
            )}
          </div>
        </nav>
      </div>
    </header>
  );
}

export default Navbar;

