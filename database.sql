-- =====================================================
-- ECOCHARGE DATABASE (Comune di Milano)
-- =====================================================
CREATE DATABASE IF NOT EXISTS ecoCharge;
USE EcoCrharge;

-- =====================================================
-- TABELLA: ADMIN
-- =====================================================
CREATE TABLE Admin (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABELLA: USER
-- =====================================================
CREATE TABLE User (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  surname VARCHAR(100) NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  phone VARCHAR(20),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABELLA: VEHICLE
-- =====================================================
CREATE TABLE Vehicle (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  brand VARCHAR(50),
  model VARCHAR(50),
  license_plate VARCHAR(20) UNIQUE,
  battery_capacity_kwh DECIMAL(6,2),
  FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE CASCADE
);

-- =====================================================
-- TABELLA: CHARGING STATION
-- =====================================================
CREATE TABLE ChargingStation (
  id INT AUTO_INCREMENT PRIMARY KEY,
  address VARCHAR(255) NOT NULL,
  latitude DECIMAL(10,7),
  longitude DECIMAL(10,7),
  power_kw DECIMAL(6,2),
  nil VARCHAR(100),
  status ENUM('active', 'maintenance', 'offline') DEFAULT 'active'
);

-- =====================================================
-- TABELLA: CHARGE SESSION
-- =====================================================
CREATE TABLE ChargeSession (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  vehicle_id INT NOT NULL,
  station_id INT NOT NULL,
  start_time DATETIME NOT NULL,
  end_time DATETIME NOT NULL,
  energy_kwh DECIMAL(8,3),
  cost_eur DECIMAL(8,2),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE CASCADE,
  FOREIGN KEY (vehicle_id) REFERENCES Vehicle(id) ON DELETE CASCADE,
  FOREIGN KEY (station_id) REFERENCES ChargingStation(id) ON DELETE CASCADE
);

-- =====================================================
-- TABELLA: PREDICTION (MODELLO ML)
-- =====================================================
CREATE TABLE Prediction (
  id INT AUTO_INCREMENT PRIMARY KEY,
  station_id INT NOT NULL,
  predicted_usage_kwh DECIMAL(8,2),
  prediction_date DATE,
  model_version VARCHAR(20),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (station_id) REFERENCES ChargingStation(id) ON DELETE CASCADE
);

-- =====================================================
-- TABELLA: SYSTEM LOG
-- =====================================================
CREATE TABLE SystemLog (
  id INT AUTO_INCREMENT PRIMARY KEY,
  level ENUM('INFO', 'WARNING', 'ERROR') NOT NULL,
  message TEXT,
  user_id INT NULL,
  admin_id INT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE SET NULL,
  FOREIGN KEY (admin_id) REFERENCES Admin(id) ON DELETE SET NULL
);

-- =====================================================
-- TABELLA: USER SESSION
-- =====================================================
CREATE TABLE UserSession (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  token VARCHAR(255) NOT NULL,
  ip_address VARCHAR(45),
  user_agent VARCHAR(255),
  expires_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE CASCADE
);

-- =====================================================
-- DATI DI ESEMPIO REALISTICI
-- =====================================================

-- Amministratori
INSERT INTO Admin (name, email, password_hash) VALUES
('Luca Rossi', 'luca.rossi@comune.milano.it', 'hash_admin1'),
('Maria Bianchi', 'maria.bianchi@comune.milano.it', 'hash_admin2');

-- Utenti
INSERT INTO User (name, surname, email, password_hash, phone) VALUES
('Giulia', 'Verdi', 'giulia.verdi@email.com', 'hash_user1', '3331122334'),
('Marco', 'Neri', 'marco.neri@email.com', 'hash_user2', '3398877665'),
('Elisa', 'Fontana', 'elisa.fontana@email.com', 'hash_user3', '3209988776');

-- Auto
INSERT INTO Vehicle (user_id, brand, model, license_plate, battery_capacity_kwh) VALUES
(1, 'Tesla', 'Model 3', 'AA123BB', 75.00),
(2, 'Fiat', '500e', 'BB456CC', 42.00),
(3, 'Renault', 'Zoe', 'CC789DD', 52.00);

-- Colonnine (coordinate Milano)
INSERT INTO ChargingStation (address, latitude, longitude, power_kw, nil, status) VALUES
('Via Torino 45, Milano', 45.4602000, 9.1855000, 50.0, 'Centro Storico', 'active'),
('Viale Monza 101, Milano', 45.5110000, 9.2210000, 22.0, 'Turro', 'active'),
('Piazza Leonardo da Vinci, Milano', 45.4781000, 9.2272000, 100.0, 'Città Studi', 'maintenance');

-- Sessioni di ricarica
INSERT INTO ChargeSession (user_id, vehicle_id, station_id, start_time, end_time, energy_kwh, cost_eur) VALUES
(1, 1, 1, '2025-10-20 08:15:00', '2025-10-20 09:05:00', 23.500, 7.05),
(2, 2, 2, '2025-10-21 18:00:00', '2025-10-21 18:45:00', 15.200, 4.56),
(3, 3, 3, '2025-10-22 12:30:00', '2025-10-22 13:20:00', 20.000, 6.00);

-- Predizioni (output modello ML)
INSERT INTO Prediction (station_id, predicted_usage_kwh, prediction_date, model_version) VALUES
(1, 250.75, '2025-10-25', 'v1.0'),
(2, 180.30, '2025-10-25', 'v1.0'),
(3, 95.10,  '2025-10-25', 'v1.0');

-- Log di sistema
INSERT INTO SystemLog (level, message, user_id, admin_id) VALUES
('INFO', 'User Giulia Verdi started a new charge session', 1, NULL),
('WARNING', 'Station 3 is under maintenance', NULL, 1),
('ERROR', 'Failed to update prediction model', NULL, 2);

-- Sessioni utente
INSERT INTO UserSession (user_id, token, ip_address, user_agent, expires_at) VALUES
(1, 'token_123abc', '192.168.1.10', 'Mozilla/5.0', '2025-10-30 23:59:00'),
(2, 'token_456def', '192.168.1.11', 'Chrome/122.0', '2025-10-30 23:59:00');
