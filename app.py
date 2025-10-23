from flask import Flask, render_template, redirect, url_for, request, session, flash
from datetime import datetime, timedelta
import requests
import config as cfg

app = Flask(__name__)
app.secret_key = cfg.SECRET_KEY

API_URL = "https://verbose-cod-5j74gxwp7r63wj4-5001.app.github.dev/api"  # URL del server API
SESSION_TIMEOUT = 360  # minuti

# -------------------------
# SESSIONE LOCALE (solo token)
# -------------------------
def require_login(role=None):
    token = session.get('token')
    role_s = session.get('role')
    last = session.get('last_activity')

    if not token or not last:
        return False

    # Timeout automatico
    if datetime.utcnow() - datetime.fromisoformat(last) > timedelta(minutes=SESSION_TIMEOUT):
        session.clear()
        return False

    # Aggiorna timestamp
    session['last_activity'] = datetime.utcnow().isoformat()

    # Ruolo
    if role and role_s != role:
        return False

    return True

# -------------------------
# LOGIN / LOGOUT
# -------------------------
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            resp = requests.post(f"{API_URL}/login", json={'email': email, 'password': password})
            data = resp.json()
            if resp.status_code == 200 and data.get('success'):
                session['token'] = data['token']
                session['role'] = data['user']['role']
                session['user_id'] = data['user']['id']
                session['last_activity'] = datetime.utcnow().isoformat()
                if data['user']['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('user_dashboard'))
            else:
                flash(data.get('message', 'Credenziali errate'), 'danger')
        except Exception as e:
            flash(f"Errore server: {e}", 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    token = session.get('token')
    if token:
        try:
            requests.post(f"{API_URL}/logout", headers={'Authorization': f'Bearer {token}'})
        except:
            pass
    session.clear()
    flash("Logout effettuato.", "info")
    return redirect(url_for('login'))


# -------------------------
# USER AREA
# -------------------------
@app.route('/user/dashboard')
def user_dashboard():
    if not require_login('user'):
        return redirect(url_for('login'))
    return render_template('user_dashboard.html')


@app.route('/map')
def map_view():
    if not require_login('user'):
        return redirect(url_for('login'))
    return render_template('map.html')


# -------------------------
# ADMIN AREA
# -------------------------
@app.route('/admin/dashboard')
def admin_dashboard():
    if not require_login('admin'):
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html')

@app.route('/admin/stations')
def admin_stations():
    if not require_login('admin'):
        return redirect(url_for('login'))
    return render_template('admin_stations.html')

@app.route('/admin/users')
def admin_users():
    if not require_login('admin'):
        return redirect(url_for('login'))
    return render_template('admin_users.html')

@app.route('/admin/stats')
def admin_stats():
    if not require_login('admin'):
        return redirect(url_for('login'))
    return render_template('admin_stats.html')


# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
