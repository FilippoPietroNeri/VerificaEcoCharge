from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import secrets
import config as cfg

app = Flask(__name__)
CORS(app)

# -------------------------
# DB CONNECTION
# -------------------------
def get_db():
    try:
        conn = mysql.connector.connect(
            host=cfg.DB_CONFIG['host'],
            user=cfg.DB_CONFIG['user'],
            password=cfg.DB_CONFIG['password'],
            database=cfg.DB_CONFIG['database'],
            port=cfg.DB_CONFIG.get('port', 18611)
        )
        return conn
    except Error as e:
        print(f"[DB] Error: {e}")
        return None


# -------------------------
# AUTH & SESSION HELPERS
# -------------------------
def generate_token():
    return secrets.token_hex(32)

def require_session(token):
    """Verifica la validità del token"""
    if not token:
        return None
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT s.*, u.name, u.surname, u.email, u.role
        FROM UserSession s
        JOIN User u ON s.user_id = u.id
        WHERE s.token=%s AND s.expiration > NOW()
    """, (token,))
    session = cur.fetchone()
    cur.close()
    conn.close()
    return session


# -------------------------
# LOGIN / LOGOUT
# -------------------------
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email e password obbligatorie'}), 400

    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Errore DB'}), 500
    cur = conn.cursor(dictionary=True)

    # Cerca in Admin o User
    cur.execute("""
        SELECT id, password_hash, 'admin' AS role FROM Admin WHERE email=%s
        UNION
        SELECT id, password_hash, 'user' AS role FROM User WHERE email=%s
    """, (email, email))
    user = cur.fetchone()
    if not user:
        cur.close(); conn.close()
        return jsonify({'success': False, 'message': 'Utente non trovato'}), 404

    if not check_password_hash(user['password_hash'], password):
        cur.close(); conn.close()
        return jsonify({'success': False, 'message': 'Password errata'}), 401

    # Genera token
    token = generate_token()
    expiration = datetime.utcnow() + timedelta(hours=6)

    cur.execute("""
        INSERT INTO UserSession (user_id, token, created_at, expires_at)
        VALUES (%s, %s, NOW(), %s)
    """, (user['id'], token, expiration))
    conn.commit()
    cur.close(); conn.close()

    return jsonify({
        'success': True,
        'token': token,
        'user': {'id': user['id'], 'role': user['role']}
    })


@app.route('/api/logout', methods=['POST'])
def api_logout():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({'success': False, 'message': 'Token mancante'}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM UserSession WHERE token=%s", (token,))
    conn.commit()
    cur.close(); conn.close()

    return jsonify({'success': True, 'message': 'Logout eseguito'})


# -------------------------
# COLONNINE (CRUD)
# -------------------------
@app.route('/api/stations', methods=['GET'])
def api_get_stations():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT s.*, EXISTS(
            SELECT 1 FROM ChargeSession cs
            WHERE cs.station_id = s.id AND cs.end_time > NOW()
        ) AS occupied
        FROM ChargingStation s
    """)
    stations = cur.fetchall()
    for s in stations:
        s['occupied'] = bool(s['occupied'])
    cur.close(); conn.close()
    return jsonify(stations)


@app.route('/api/stations/<int:station_id>', methods=['GET'])
def api_get_station(station_id):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM ChargingStation WHERE id=%s", (station_id,))
    station = cur.fetchone()
    if not station:
        return jsonify({'error': 'Colonnina non trovata'}), 404

    cur.execute("""
        SELECT cs.*, u.name, u.surname, v.license_plate
        FROM ChargeSession cs
        LEFT JOIN User u ON cs.user_id=u.id
        LEFT JOIN Vehicle v ON cs.vehicle_id=v.id
        WHERE cs.station_id=%s
        ORDER BY cs.start_time DESC
        LIMIT 10
    """, (station_id,))
    station['recent_sessions'] = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(station)


@app.route('/api/stations', methods=['POST'])
def api_create_station():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    s = require_session(token)
    if not s or s['role'] != 'admin':
        return jsonify({'error': 'Non autorizzato'}), 403

    d = request.get_json()
    conn = get_db(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO ChargingStation (address, latitude, longitude, power_kw, nil, status)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (d['address'], d['latitude'], d['longitude'], d['power_kw'], d['nil'], d.get('status', 'active')))
    conn.commit(); cur.close(); conn.close()
    return jsonify({'success': True})


@app.route('/api/stations/<int:station_id>', methods=['PUT'])
def api_update_station(station_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    s = require_session(token)
    if not s or s['role'] != 'admin':
        return jsonify({'error': 'Non autorizzato'}), 403

    d = request.get_json()
    conn = get_db(); cur = conn.cursor()
    cur.execute("""
        UPDATE ChargingStation SET address=%s, latitude=%s, longitude=%s,
            power_kw=%s, nil=%s, status=%s WHERE id=%s
    """, (d['address'], d['latitude'], d['longitude'], d['power_kw'], d['nil'], d['status'], station_id))
    conn.commit(); cur.close(); conn.close()
    return jsonify({'success': True})


@app.route('/api/stations/<int:station_id>', methods=['DELETE'])
def api_delete_station(station_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    s = require_session(token)
    if not s or s['role'] != 'admin':
        return jsonify({'error': 'Non autorizzato'}), 403

    conn = get_db(); cur = conn.cursor()
    cur.execute("DELETE FROM ChargingStation WHERE id=%s", (station_id,))
    conn.commit(); cur.close(); conn.close()
    return jsonify({'success': True})


# -------------------------
# UTENTI (CRUD)
# -------------------------
@app.route('/api/users', methods=['GET'])
def api_get_users():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    s = require_session(token)
    if not s or s['role'] != 'admin':
        return jsonify({'error': 'Non autorizzato'}), 403

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, name, surname, email, phone FROM User")
    users = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(users)


@app.route('/api/users', methods=['POST'])
def api_create_user():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    s = require_session(token)
    if not s or s['role'] != 'admin':
        return jsonify({'error': 'Non autorizzato'}), 403

    d = request.get_json()
    hashed = generate_password_hash(d.get('password', 'defaultpass'))
    conn = get_db(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO User (name, surname, email, password_hash, phone)
        VALUES (%s,%s,%s,%s,%s)
    """, (d['name'], d['surname'], d['email'], hashed, d.get('phone')))
    conn.commit(); cur.close(); conn.close()
    return jsonify({'success': True})


@app.route('/api/users/<int:user_id>', methods=['PUT'])
def api_update_user(user_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    s = require_session(token)
    if not s or s['role'] != 'admin':
        return jsonify({'error': 'Non autorizzato'}), 403

    d = request.get_json()
    conn = get_db(); cur = conn.cursor()
    if 'password' in d and d['password']:
        hashed = generate_password_hash(d['password'])
        cur.execute("""
            UPDATE User SET name=%s, surname=%s, email=%s, password_hash=%s, phone=%s WHERE id=%s
        """, (d['name'], d['surname'], d['email'], hashed, d['phone'], user_id))
    else:
        cur.execute("""
            UPDATE User SET name=%s, surname=%s, email=%s, phone=%s WHERE id=%s
        """, (d['name'], d['surname'], d['email'], d['phone'], user_id))
    conn.commit(); cur.close(); conn.close()
    return jsonify({'success': True})


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def api_delete_user(user_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    s = require_session(token)
    if not s or s['role'] != 'admin':
        return jsonify({'error': 'Non autorizzato'}), 403

    conn = get_db(); cur = conn.cursor()
    cur.execute("DELETE FROM User WHERE id=%s", (user_id,))
    conn.commit(); cur.close(); conn.close()
    return jsonify({'success': True})


# -------------------------
# PRENOTAZIONE / RICARICHE
# -------------------------
@app.route('/api/book', methods=['POST'])
def api_book_station():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    s = require_session(token)
    if not s or s['role'] != 'user':
        return jsonify({'error': 'Non autorizzato'}), 403

    d = request.get_json()
    station_id = d.get('station_id')
    vehicle_id = d.get('vehicle_id')
    duration = int(d.get('duration', 60))

    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM ChargeSession WHERE station_id=%s AND end_time>NOW()", (station_id,))
    if cur.fetchone()[0] > 0:
        cur.close(); conn.close()
        return jsonify({'error': 'Colonnina occupata'}), 400

    start_time = datetime.utcnow()
    end_time = start_time + timedelta(minutes=duration)
    cur.execute("""
        INSERT INTO ChargeSession (user_id, vehicle_id, station_id, start_time, end_time, energy_kwh, cost_eur)
        VALUES (%s,%s,%s,%s,%s,NULL,NULL)
    """, (s['user_id'], vehicle_id, station_id, start_time, end_time))
    conn.commit(); cur.close(); conn.close()

    return jsonify({'success': True, 'start_time': start_time.isoformat(), 'end_time': end_time.isoformat()})


# -------------------------
# STATISTICHE
# -------------------------
@app.route('/api/stats', methods=['GET'])
def api_stats():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    s = require_session(token)
    if not s or s['role'] != 'admin':
        return jsonify({'error': 'Non autorizzato'}), 403

    neighborhood = request.args.get('neighborhood')
    days = int(request.args.get('days', 30))
    if not neighborhood:
        return jsonify({'error': 'Parametro neighborhood richiesto'}), 400

    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT DATE(cs.start_time) AS day, COUNT(*) AS charges_count
        FROM ChargeSession cs
        JOIN ChargingStation s ON cs.station_id = s.id
        WHERE s.nil=%s AND cs.start_time >= DATE_SUB(NOW(), INTERVAL %s DAY)
        GROUP BY DATE(cs.start_time)
        ORDER BY day
    """, (neighborhood, days))
    data = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(data)


# -------------------------
# MAIN
# -------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
