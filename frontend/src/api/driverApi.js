import api from "./axios";

export const driverApi = {
  // Driver Profile
  getProfile: () => api.get("/drivers/me/"),
  updateProfile: (data) => api.patch("/drivers/me/", data),

  // Driver Rides
  getEligibleRides: () => api.get("/drivers/rides/eligible/"),
  getMyRides: (status) =>
    api.get("/drivers/rides/", { params: status ? { status } : {} }),
  getRideDetail: (id) => api.get(`/drivers/rides/${id}/`),
  acceptRide: (id) => api.post(`/drivers/rides/${id}/accept/`),

  // Ride Lifecycle Progression
  markArriving: (id) => api.post(`/drivers/rides/${id}/arriving/`),
  markArrived: (id) => api.post(`/drivers/rides/${id}/arrived/`),
  startRide: (id, otp) => api.post(`/drivers/rides/${id}/start/`, { otp }),
  completeRide: (id, data = {}) =>
    api.post(`/drivers/rides/${id}/complete/`, data),
  ratePassenger: (id, rating, feedback = "") =>
    api.post(`/drivers/rides/${id}/rate/`, { rating, feedback }),

  // Vehicles
  getVehicles: () => api.get("/drivers/vehicles/"),
  getVehicleDetail: (id) => api.get(`/drivers/vehicles/${id}/`),
  createVehicle: (data) => api.post("/drivers/vehicles/", data),
  updateVehicle: (id, data) => api.patch(`/drivers/vehicles/${id}/`, data),
  deleteVehicle: (id) => api.delete(`/drivers/vehicles/${id}/`),

  // Vehicle Categories
  getCategories: () => api.get("/categories/"),
};

export default driverApi;
