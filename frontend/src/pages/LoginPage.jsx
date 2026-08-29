import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../api/axios";
import "./AuthPage.css";

function LoginPage() {
  const navigate = useNavigate();
  const [username, setEmail] = useState("");
  const [password, setPassword] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();

    try {
      const response = await api.post("/auth/token/", {
        username: username,
        password: password,
      });

      console.log("Login successful:", response.data);

      navigate("/");
    } catch (error) {
      console.error("Login failed:", error.response?.data);
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-card">
        <h1>Login to Movona</h1>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>

            <input
              id="username"
              type="text"
              placeholder="Enter your username"
              value={username}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>

            <input
              id="password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </div>

          <button type="submit">Login</button>
        </form>

        <p className="auth-footer">
          Don't have an account? <Link to="/register">Create Account</Link>
        </p>
      </div>
    </main>
  );
}

export default LoginPage;
