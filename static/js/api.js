const API_URL = "https://verbose-cod-5j74gxwp7r63wj4-5001.app.github.dev/api";

// Recupera token da sessione Flask (iniettato da backend)
const TOKEN = sessionStorage.getItem("token") || null;

// Helper per chiamate API
async function apiFetch(endpoint, method = "GET", body = null) {
  const headers = {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${TOKEN}`
  };
  const options = { method, headers };
  if (body) options.body = JSON.stringify(body);

  const res = await fetch(`${API_URL}${endpoint}`, options);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || data.message || "Errore API");
  return data;
}

// Funzioni di alto livello
async function getStations() { return apiFetch("/stations"); }
async function getStation(id) { return apiFetch(`/stations/${id}`); }
async function bookStation(stationId, vehicleId, duration = 60) {
  return apiFetch("/book", "POST", { station_id: stationId, vehicle_id: vehicleId, duration });
}
async function getUsers() { return apiFetch("/users"); }
async function createUser(user) { return apiFetch("/users", "POST", user); }
async function updateUser(id, user) { return apiFetch(`/users/${id}`, "PUT", user); }
async function deleteUser(id) { return apiFetch(`/users/${id}`, "DELETE"); }
async function getStats(nil, days = 30) { return apiFetch(`/stats?neighborhood=${nil}&days=${days}`); }
