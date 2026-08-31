import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import driverApi from "../api/driverApi";
import "./DriverVehiclesPage.css";

function DriverVehiclesPage() {
  const [vehicles, setVehicles] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionSuccess, setActionSuccess] = useState("");

  // Modal State for Add / Edit
  const [showModal, setShowModal] = useState(false);
  const [editingVehicle, setEditingVehicle] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  // Form Fields
  const [categoryId, setCategoryId] = useState("");
  const [make, setMake] = useState("");
  const [model, setModel] = useState("");
  const [regNumber, setRegNumber] = useState("");
  const [colour, setColour] = useState("");
  const [seatingCapacity, setSeatingCapacity] = useState(4);

  async function loadData() {
    try {
      setLoading(true);
      setError("");
      const [vehRes, catRes] = await Promise.all([
        driverApi.getVehicles(),
        driverApi.getCategories().catch(() => ({ data: [] })),
      ]);
      setVehicles(vehRes.data || []);
      setCategories(catRes.data || []);
      if (catRes.data && catRes.data.length > 0 && !categoryId) {
        setCategoryId(catRes.data[0].id);
      }
    } catch (err) {
      console.error("Error loading vehicles:", err);
      setError("Unable to load driver vehicles. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  function openAddModal() {
    setEditingVehicle(null);
    setMake("");
    setModel("");
    setRegNumber("");
    setColour("");
    setSeatingCapacity(4);
    if (categories.length > 0) {
      setCategoryId(categories[0].id);
    }
    setFormError("");
    setShowModal(true);
  }

  function openEditModal(veh) {
    setEditingVehicle(veh);
    setCategoryId(veh.category);
    setMake(veh.make);
    setModel(veh.model);
    setRegNumber(veh.registration_number);
    setColour(veh.colour);
    setSeatingCapacity(veh.seating_capacity);
    setFormError("");
    setShowModal(true);
  }

  function closeModal() {
    setShowModal(false);
    setEditingVehicle(null);
    setFormError("");
  }

  async function handleFormSubmit(e) {
    e.preventDefault();
    setFormError("");
    setSubmitting(true);

    const payload = {
      category: Number(categoryId),
      make: make.trim(),
      model: model.trim(),
      registration_number: regNumber.trim().toUpperCase(),
      colour: colour.trim(),
      seating_capacity: Number(seatingCapacity),
    };

    try {
      if (editingVehicle) {
        const res = await driverApi.updateVehicle(editingVehicle.id, payload);
        setVehicles((prev) =>
          prev.map((v) => (v.id === editingVehicle.id ? res.data : v)),
        );
        setActionSuccess("Vehicle updated successfully.");
      } else {
        const res = await driverApi.createVehicle(payload);
        setVehicles((prev) => [res.data, ...prev]);
        setActionSuccess("Vehicle registered! Pending admin verification.");
      }
      closeModal();
    } catch (err) {
      console.error("Vehicle submit error:", err);
      const data = err.response?.data;
      if (data && typeof data === "object") {
        const firstKey = Object.keys(data)[0];
        const msg = Array.isArray(data[firstKey])
          ? data[firstKey][0]
          : data[firstKey];
        setFormError(`${firstKey}: ${msg}`);
      } else {
        setFormError("Failed to save vehicle. Please check inputs.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function handleToggleActive(veh) {
    if (veh.verification_status !== "APPROVED") {
      alert("Only approved vehicles can be activated.");
      return;
    }

    try {
      setActionSuccess("");
      const res = await driverApi.updateVehicle(veh.id, {
        is_active: !veh.is_active,
      });
      setVehicles((prev) =>
        prev.map((v) => (v.id === veh.id ? res.data : v)),
      );
      setActionSuccess(
        `Vehicle ${veh.registration_number} is now ${
          res.data.is_active ? "Active" : "Inactive"
        }.`,
      );
    } catch (err) {
      console.error("Failed to toggle vehicle status:", err);
      alert(
        err.response?.data?.is_active?.[0] ||
          err.response?.data?.detail ||
          "Failed to update vehicle status.",
      );
    }
  }

  async function handleDelete(veh) {
    const confirmDelete = window.confirm(
      `Are you sure you want to remove vehicle ${veh.make} ${veh.model} (${veh.registration_number})?`,
    );
    if (!confirmDelete) return;

    try {
      setActionSuccess("");
      await driverApi.deleteVehicle(veh.id);
      setVehicles((prev) => prev.filter((v) => v.id !== veh.id));
      setActionSuccess("Vehicle removed successfully.");
    } catch (err) {
      console.error("Delete vehicle error:", err);
      alert(
        err.response?.data?.detail ||
          "Cannot delete vehicle. It may have associated active rides.",
      );
    }
  }

  return (
    <div className="driver-vehicles-container">
      <div className="vehicles-header">
        <div>
          <h1>Registered Vehicles</h1>
          <p className="subtitle">
            Manage your vehicles, check verification status, and set your active
            dispatch car.
          </p>
        </div>
        <div className="header-actions">
          <Link to="/driver/dashboard" className="btn-back-dashboard">
            &larr; Driver Dashboard
          </Link>
          <button onClick={openAddModal} className="btn-add-vehicle">
            + Add New Vehicle
          </button>
        </div>
      </div>

      {actionSuccess && (
        <div className="alert-success-banner">{actionSuccess}</div>
      )}

      {loading ? (
        <div className="state-container">
          <div className="spinner"></div>
          <p>Loading your vehicles...</p>
        </div>
      ) : error ? (
        <div className="state-container error-card">
          <p>{error}</p>
          <button onClick={loadData} className="btn-retry">
            Try Again
          </button>
        </div>
      ) : vehicles.length === 0 ? (
        <div className="empty-vehicles-card">
          <div className="empty-icon">🚗</div>
          <h2>No Vehicles Registered Yet</h2>
          <p>
            Register your vehicle to start receiving rides matching its
            category.
          </p>
          <button onClick={openAddModal} className="btn-add-vehicle">
            + Add Your First Vehicle
          </button>
        </div>
      ) : (
        <div className="vehicles-grid">
          {vehicles.map((veh) => {
            const isApproved = veh.verification_status === "APPROVED";

            return (
              <div key={veh.id} className="vehicle-card">
                <div className="veh-card-top">
                  <div>
                    <h3 className="veh-title">
                      {veh.make} {veh.model}
                    </h3>
                    <span className="veh-reg-badge">
                      {veh.registration_number}
                    </span>
                  </div>

                  <span
                    className={`veh-verif-badge verif-${veh.verification_status?.toLowerCase()}`}
                  >
                    {veh.verification_status}
                  </span>
                </div>

                <div className="veh-details-list">
                  <div className="veh-row">
                    <span className="veh-lbl">Category</span>
                    <span className="veh-val">
                      {veh.category_name || "Standard"}
                    </span>
                  </div>
                  <div className="veh-row">
                    <span className="veh-lbl">Color</span>
                    <span className="veh-val">{veh.colour}</span>
                  </div>
                  <div className="veh-row">
                    <span className="veh-lbl">Capacity</span>
                    <span className="veh-val">{veh.seating_capacity} Seats</span>
                  </div>
                  <div className="veh-row">
                    <span className="veh-lbl">Dispatch Status</span>
                    <span
                      className={`veh-val ${veh.is_active ? "status-active" : "status-inactive"}`}
                    >
                      {veh.is_active ? "● Active for Rides" : "○ Inactive"}
                    </span>
                  </div>
                </div>

                <div className="veh-card-actions">
                  {isApproved && (
                    <button
                      onClick={() => handleToggleActive(veh)}
                      className={`btn-veh-toggle ${veh.is_active ? "btn-deactivate" : "btn-activate"}`}
                    >
                      {veh.is_active ? "Deactivate" : "Activate"}
                    </button>
                  )}
                  <button
                    onClick={() => openEditModal(veh)}
                    className="btn-veh-edit"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(veh)}
                    className="btn-veh-delete"
                  >
                    Delete
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal for Add / Edit Vehicle */}
      {showModal && (
        <div className="modal-backdrop">
          <div className="modal-content">
            <div className="modal-header">
              <h2>
                {editingVehicle ? "Edit Vehicle" : "Register New Vehicle"}
              </h2>
              <button onClick={closeModal} className="btn-modal-close">
                ✕
              </button>
            </div>

            {formError && <div className="form-alert-error">{formError}</div>}

            <form onSubmit={handleFormSubmit} className="vehicle-form">
              <div className="form-group">
                <label htmlFor="category">Vehicle Category *</label>
                <select
                  id="category"
                  value={categoryId}
                  onChange={(e) => setCategoryId(e.target.value)}
                  required
                >
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.passenger_capacity} seats, ₹{c.base_fare}{" "}
                      base)
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="make">Make / Manufacturer *</label>
                  <input
                    id="make"
                    type="text"
                    placeholder="e.g. Maruti, Hyundai, Honda"
                    value={make}
                    onChange={(e) => setMake(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="model">Model *</label>
                  <input
                    id="model"
                    type="text"
                    placeholder="e.g. Dzire, City, Verna"
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="regNumber">Registration / Number Plate *</label>
                  <input
                    id="regNumber"
                    type="text"
                    placeholder="e.g. DL01AB1234"
                    value={regNumber}
                    onChange={(e) => setRegNumber(e.target.value.toUpperCase())}
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="colour">Color *</label>
                  <input
                    id="colour"
                    type="text"
                    placeholder="e.g. White, Silver, Black"
                    value={colour}
                    onChange={(e) => setColour(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="seatingCapacity">Seating Capacity *</label>
                <input
                  id="seatingCapacity"
                  type="number"
                  min={1}
                  max={20}
                  value={seatingCapacity}
                  onChange={(e) => setSeatingCapacity(e.target.value)}
                  required
                />
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  onClick={closeModal}
                  className="btn-cancel"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={submitting}
                >
                  {submitting
                    ? "Saving..."
                    : editingVehicle
                      ? "Update Vehicle"
                      : "Register Vehicle"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default DriverVehiclesPage;
