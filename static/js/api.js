const API_URL = "https://verbose-cod-5j74gxwp7r63wj4-5001.app.github.dev/api";

const TOKEN = document.querySelector('meta[name="api-token"]')?.content || null;

// Helper generale per chiamate API
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

// API specifiche
const API = {
  stations: {
    getAll: () => apiFetch("/stations"),
    get: (id) => apiFetch(`/stations/${id}`),
    create: (data) => apiFetch("/stations", "POST", data),
    update: (id, data) => apiFetch(`/stations/${id}`, "PUT", data),
    delete: (id) => apiFetch(`/stations/${id}`, "DELETE")
  },
  vehicles: {
    getAll: () => apiFetch("/vehicles"),
  },
  users: {
    getAll: () => apiFetch("/users"),
    create: (data) => apiFetch("/users", "POST", data),
    update: (id, data) => apiFetch(`/users/${id}`, "PUT", data),
    delete: (id) => apiFetch(`/users/${id}`, "DELETE")
  },
  stats: {
    get: (nil, days = 30) => apiFetch(`/stats?neighborhood=${nil}&days=${days}`)
  },
  booking: {
    create: (station_id, vehicle_id, duration = 60) =>
      apiFetch("/book", "POST", { station_id, vehicle_id, duration })
  }
};
