import { Link } from "react-router-dom";
import "./Footer.css";

function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="site-footer">
      <div className="footer-container">
        <div className="footer-brand">
          <div className="footer-logo">
            <span className="footer-logo-icon">🚗</span>
            <span className="footer-logo-text">Movona</span>
          </div>
          <p className="footer-tagline">
            Your trusted car rental and ride mobility platform. Reliable,
            convenient, and affordable.
          </p>
        </div>

        <div className="footer-nav">
          <div className="footer-col">
            <h4>Explore</h4>
            <Link to="/">Fleet & Cars</Link>
            <Link to="/my-bookings">My Reservations</Link>
          </div>

          <div className="footer-col">
            <h4>Account</h4>
            <Link to="/login">Login</Link>
            <Link to="/register">Create Account</Link>
          </div>

          <div className="footer-col">
            <h4>About Movona</h4>
            <span>Open Source Project</span>
            <span>Production Ready Architecture</span>
          </div>
        </div>
      </div>

      <div className="footer-bottom">
        <p>&copy; {currentYear} Movona. All rights reserved.</p>
      </div>
    </footer>
  );
}

export default Footer;
