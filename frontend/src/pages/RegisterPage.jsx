import { useState } from "react";
import { Link } from "react-router-dom";
import "./AuthPage.css";

function RegisterPage() {
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    phone: "",
    password: "",
    password_confirm: "",
  });
  const [error, setError] = useState("");

  function handleChange(event) {
    const { name, value } = event.target;

    setFormData({
      ...formData,
      [name]: value,
    });
    setError("");
  }

  function handleSubmit(event) {
    event.preventDefault();

    if (formData.password !== formData.password_confirm) {
      setError("Passwords do not match.");
      return;
    }

    setError("");

    console.log("Registration form submitted");
  }

  return (
    <main className="auth-page">
      <div className="auth-card">
        <h1>Create your Movona account</h1>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>

            <input
              id="username"
              name="username"
              type="text"
              placeholder="Choose a username"
              value={formData.username}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email</label>

            <input
              id="email"
              name="email"
              type="email"
              placeholder="Enter your email"
              value={formData.email}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="phone">Phone</label>

            <input
              id="phone"
              name="phone"
              type="tel"
              placeholder="+919876543210"
              value={formData.phone}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>

            <input
              id="password"
              name="password"
              type="password"
              placeholder="Create a password"
              value={formData.password}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password_confirm">Confirm Password</label>

            <input
              id="password_confirm"
              name="password_confirm"
              type="password"
              placeholder="Confirm your password"
              value={formData.password_confirm}
              onChange={handleChange}
              required
            />
          </div>
          {error && <p className="form-error">{error}</p>}
          <button type="submit">Create Account</button>
        </form>

        <p className="auth-footer">
          Already have an account? <Link to="/login">Login</Link>
        </p>
      </div>
    </main>
  );
}

export default RegisterPage;
