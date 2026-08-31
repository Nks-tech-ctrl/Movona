import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import driverApi from "../api/driverApi";
import "./DriverProfilePage.css";

function DriverProfilePage() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  // Edit fields
  const [dob, setDob] = useState("");
  const [saving, setSaving] = useState(false);

  async function loadProfile() {
    try {
      setLoading(true);
      setError("");
      const res = await driverApi.getProfile();
      setProfile(res.data);
      setDob(res.data.date_of_birth || "");
    } catch (err) {
      console.error("Error loading driver profile:", err);
      setError("Unable to load driver profile. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadProfile();
  }, []);

  async function handleSave(e) {
    e.preventDefault();
    try {
      setSaving(true);
      setSuccessMessage("");
      const res = await driverApi.updateProfile({
        date_of_birth: dob || null,
      });
      setProfile(res.data);
      setSuccessMessage("Driver profile updated successfully.");
    } catch (err) {
      console.error("Error updating profile:", err);
      alert(
        err.response?.data?.date_of_birth?.[0] ||
          err.response?.data?.detail ||
          "Failed to update profile.",
      );
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="driver-profile-container">
        <div className="state-card loading">
          <div className="spinner"></div>
          <p>Loading driver profile...</p>
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="driver-profile-container">
        <div className="state-card error">
          <p>{error || "Profile not found."}</p>
          <button onClick={loadProfile} className="btn-retry">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="driver-profile-container">
      <div className="profile-header">
        <div>
          <h1>Driver Profile</h1>
          <p className="subtitle">
            View your driver credentials, performance metrics, and settings.
          </p>
        </div>
        <Link to="/driver/dashboard" className="btn-back-dashboard">
          &larr; Driver Dashboard
        </Link>
      </div>

      {successMessage && (
        <div className="alert-success-banner">{successMessage}</div>
      )}

      <div className="profile-layout">
        {/* Left Side: Summary / Status Card */}
        <div className="profile-card summary-card">
          <div className="driver-avatar-circle">🚕</div>
          <h2>{profile.username}</h2>
          <p className="profile-email">{profile.email}</p>
          <p className="profile-phone">{profile.phone}</p>

          <div className="profile-badge-row">
            <span
              className={`badge-verif verif-${profile.verification_status?.toLowerCase()}`}
            >
              {profile.verification_status === "APPROVED"
                ? "✓ Verified Driver"
                : `Status: ${profile.verification_status}`}
            </span>
            <span
              className={`badge-avail avail-${profile.availability_status?.toLowerCase()}`}
            >
              ● {profile.availability_status}
            </span>
          </div>

          <div className="driver-metrics-list">
            <div className="driver-metric-item">
              <span className="metric-val">{profile.completed_rides}</span>
              <span className="metric-lbl">Completed Rides</span>
            </div>
            <div className="driver-metric-item">
              <span className="metric-val">
                ⭐ {Number(profile.average_rating || 0).toFixed(2)}
              </span>
              <span className="metric-lbl">Driver Rating</span>
            </div>
          </div>
        </div>

        {/* Right Side: Account Details & Edit Form */}
        <div className="profile-card details-card">
          <h2>Account Information</h2>

          <form onSubmit={handleSave} className="profile-edit-form">
            <div className="form-group">
              <label>Username</label>
              <input type="text" value={profile.username} disabled />
            </div>

            <div className="form-group">
              <label>Email Address</label>
              <input type="email" value={profile.email} disabled />
            </div>

            <div className="form-group">
              <label>Phone Number</label>
              <input type="text" value={profile.phone} disabled />
            </div>

            <div className="form-group">
              <label htmlFor="dob">Date of Birth</label>
              <input
                id="dob"
                type="date"
                value={dob}
                onChange={(e) => setDob(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Member Since</label>
              <input
                type="text"
                value={new Date(profile.created_at).toLocaleDateString()}
                disabled
              />
            </div>

            <div className="form-actions">
              <button
                type="submit"
                className="btn-save-profile"
                disabled={saving}
              >
                {saving ? "Saving Changes..." : "Save Profile Details"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default DriverProfilePage;
