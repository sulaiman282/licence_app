"""
Spidy Browser License Server
Web UI and API for managing license keys with authentication
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import sqlite3
import hashlib
import secrets
import datetime
import jwt
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins

DATABASE = "licenses.db"
JWT_EXPIRY_DAYS = 7

def init_db():
    """Initialize database"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  is_active BOOLEAN DEFAULT 1)''')
    
    # Create default user if not exists
    default_email = "sulaiman35282@gmail.com"
    default_password = "Spidy@123"
    password_hash = hashlib.sha256(default_password.encode()).hexdigest()
    
    try:
        c.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)", 
                  (default_email, password_hash))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # User already exists
    
    # Licenses table
    c.execute('''CREATE TABLE IF NOT EXISTS licenses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  license_key TEXT UNIQUE NOT NULL,
                  machine_id TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  expires_at TIMESTAMP NOT NULL,
                  is_active BOOLEAN DEFAULT 1,
                  max_activations INTEGER DEFAULT 1,
                  activation_count INTEGER DEFAULT 0,
                  notes TEXT)''')
    
    # Activation logs
    c.execute('''CREATE TABLE IF NOT EXISTS activation_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  license_key TEXT NOT NULL,
                  machine_id TEXT NOT NULL,
                  action TEXT NOT NULL,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  ip_address TEXT)''')
    
    # Browsing history
    c.execute('''CREATE TABLE IF NOT EXISTS browsing_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  machine_id TEXT NOT NULL,
                  url TEXT NOT NULL,
                  title TEXT,
                  visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  profile_name TEXT)''')
    
    # Create indexes
    c.execute('''CREATE INDEX IF NOT EXISTS idx_history_machine 
                 ON browsing_history(machine_id)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_history_visited 
                 ON browsing_history(visited_at DESC)''')
    
    conn.commit()
    conn.close()

def generate_license_key():
    """Generate a unique license key"""
    return f"SPIDY-{secrets.token_hex(8).upper()}-{secrets.token_hex(4).upper()}"

def generate_token(user_id, email):
    """Generate JWT token"""
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=JWT_EXPIRY_DAYS)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorator for token authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({"error": "Token is invalid or expired"}), 401
        
        return f(payload, *args, **kwargs)
    return decorated

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

@app.route('/history')
def history():
    """Browsing history page"""
    return render_template('history.html')

@app.route('/login')
def login_page():
    """Login page"""
    return render_template('login.html')

# Authentication APIs
@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login and get JWT token"""
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT * FROM users WHERE email = ? AND password_hash = ? AND is_active = 1",
              (email, password_hash))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    
    token = generate_token(user['id'], user['email'])
    
    return jsonify({
        "success": True,
        "token": token,
        "email": user['email'],
        "expires_in_days": JWT_EXPIRY_DAYS
    })

@app.route('/api/auth/verify', methods=['POST'])
def verify():
    """Verify token"""
    data = request.json
    token = data.get('token')
    
    if not token:
        return jsonify({"valid": False}), 400
    
    payload = verify_token(token)
    if payload:
        return jsonify({"valid": True, "email": payload['email']})
    else:
        return jsonify({"valid": False}), 401

@app.route('/api/users', methods=['GET'])
@token_required
def get_users(payload):
    """Get all users"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT id, email, created_at, is_active FROM users ORDER BY created_at DESC")
    users = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return jsonify(users)

@app.route('/api/users', methods=['POST'])
@token_required
def create_user(payload):
    """Create new user"""
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    try:
        c.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)",
                  (email, password_hash))
        conn.commit()
        return jsonify({"success": True, "email": email})
    except sqlite3.IntegrityError:
        return jsonify({"error": "User already exists"}), 400
    finally:
        conn.close()

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@token_required
def update_user(payload, user_id):
    """Update user"""
    data = request.json
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    updates = []
    params = []
    
    if 'password' in data:
        password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
        updates.append("password_hash = ?")
        params.append(password_hash)
    
    if 'is_active' in data:
        updates.append("is_active = ?")
        params.append(1 if data['is_active'] else 0)
    
    if not updates:
        return jsonify({"error": "No updates provided"}), 400
    
    params.append(user_id)
    query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
    
    c.execute(query, params)
    conn.commit()
    
    if c.rowcount == 0:
        conn.close()
        return jsonify({"error": "User not found"}), 404
    
    conn.close()
    return jsonify({"success": True})

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(payload, user_id):
    """Delete user"""
    # Prevent deleting yourself
    if payload['user_id'] == user_id:
        return jsonify({"error": "Cannot delete yourself"}), 400
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    
    if c.rowcount == 0:
        conn.close()
        return jsonify({"error": "User not found"}), 404
    
    conn.close()
    return jsonify({"success": True})

@app.route('/api/licenses', methods=['GET'])
@token_required
def get_licenses(payload):
    """Get all licenses"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('''SELECT * FROM licenses ORDER BY created_at DESC''')
    licenses = [dict(row) for row in c.fetchall()]
    
    conn.close()
    return jsonify(licenses)

@app.route('/api/licenses', methods=['POST'])
@requires_auth
def create_license():
    """Create a new license"""
    data = request.json
    duration_days = data.get('duration_days', 30)
    notes = data.get('notes', '')
    max_activations = data.get('max_activations', 1)
    
    license_key = generate_license_key()
    expires_at = datetime.datetime.now() + datetime.timedelta(days=duration_days)
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    try:
        c.execute('''INSERT INTO licenses (license_key, expires_at, notes, max_activations)
                     VALUES (?, ?, ?, ?)''',
                  (license_key, expires_at, notes, max_activations))
        conn.commit()
        
        return jsonify({
            "success": True,
            "license_key": license_key,
            "expires_at": expires_at.isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

@app.route('/api/licenses/<license_key>', methods=['PUT'])
@requires_auth
def update_license(license_key):
    """Update license (extend duration, block/unblock)"""
    data = request.json
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    updates = []
    params = []
    
    if 'extend_days' in data:
        updates.append("expires_at = datetime(expires_at, '+' || ? || ' days')")
        params.append(data['extend_days'])
    
    if 'is_active' in data:
        updates.append("is_active = ?")
        params.append(1 if data['is_active'] else 0)
    
    if 'notes' in data:
        updates.append("notes = ?")
        params.append(data['notes'])
    
    if 'max_activations' in data:
        updates.append("max_activations = ?")
        params.append(data['max_activations'])
    
    if not updates:
        return jsonify({"error": "No updates provided"}), 400
    
    params.append(license_key)
    query = f"UPDATE licenses SET {', '.join(updates)} WHERE license_key = ?"
    
    c.execute(query, params)
    conn.commit()
    
    if c.rowcount == 0:
        conn.close()
        return jsonify({"error": "License not found"}), 404
    
    conn.close()
    return jsonify({"success": True})

@app.route('/api/licenses/<license_key>', methods=['DELETE'])
@requires_auth
def delete_license(license_key):
    """Delete a license"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    c.execute("DELETE FROM licenses WHERE license_key = ?", (license_key,))
    conn.commit()
    
    if c.rowcount == 0:
        conn.close()
        return jsonify({"error": "License not found"}), 404
    
    conn.close()
    return jsonify({"success": True})

@app.route('/api/validate', methods=['POST'])
def validate_license():
    """Validate license key (called by browser app)"""
    data = request.json
    license_key = data.get('license_key')
    machine_id = data.get('machine_id')
    
    if not license_key or not machine_id:
        return jsonify({"valid": False, "error": "Missing license_key or machine_id"}), 400
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('''SELECT * FROM licenses WHERE license_key = ?''', (license_key,))
    license_data = c.fetchone()
    
    if not license_data:
        conn.close()
        return jsonify({"valid": False, "error": "Invalid license key"})
    
    license_dict = dict(license_data)
    
    # Check if active
    if not license_dict['is_active']:
        conn.close()
        return jsonify({"valid": False, "error": "License is blocked"})
    
    # Check expiration
    expires_at = datetime.datetime.fromisoformat(license_dict['expires_at'])
    if datetime.datetime.now() > expires_at:
        conn.close()
        return jsonify({"valid": False, "error": "License expired"})
    
    # Check machine binding
    if license_dict['machine_id']:
        if license_dict['machine_id'] != machine_id:
            conn.close()
            return jsonify({"valid": False, "error": "License already activated on another machine"})
    else:
        # First activation - bind to this machine
        c.execute('''UPDATE licenses SET machine_id = ?, activation_count = activation_count + 1
                     WHERE license_key = ?''', (machine_id, license_key))
        conn.commit()
        
        # Log activation
        c.execute('''INSERT INTO activation_logs (license_key, machine_id, action, ip_address)
                     VALUES (?, ?, ?, ?)''',
                  (license_key, machine_id, 'activated', request.remote_addr))
        conn.commit()
    
    conn.close()
    
    return jsonify({
        "valid": True,
        "expires_at": license_dict['expires_at'],
        "days_remaining": (expires_at - datetime.datetime.now()).days
    })

@app.route('/api/stats', methods=['GET'])
@requires_auth
def get_stats():
    """Get license statistics"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM licenses")
    total = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM licenses WHERE is_active = 1")
    active = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM licenses WHERE datetime(expires_at) > datetime('now')")
    valid = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM licenses WHERE machine_id IS NOT NULL")
    activated = c.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        "total": total,
        "active": active,
        "valid": valid,
        "activated": activated
    })

@app.route('/api/licenses/filter', methods=['POST'])
@requires_auth
def filter_licenses():
    """Filter licenses by date range"""
    data = request.json
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    filter_type = data.get('filter_type', 'created')  # 'created' or 'expires'
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query = "SELECT * FROM licenses WHERE 1=1"
    params = []
    
    if start_date:
        if filter_type == 'created':
            query += " AND date(created_at) >= date(?)"
        else:
            query += " AND date(expires_at) >= date(?)"
        params.append(start_date)
    
    if end_date:
        if filter_type == 'created':
            query += " AND date(created_at) <= date(?)"
        else:
            query += " AND date(expires_at) <= date(?)"
        params.append(end_date)
    
    query += " ORDER BY created_at DESC"
    
    c.execute(query, params)
    licenses = [dict(row) for row in c.fetchall()]
    
    conn.close()
    return jsonify(licenses)

@app.route('/api/history', methods=['POST'])
def add_history():
    """Add browsing history entry (called by browser)"""
    data = request.json
    machine_id = data.get('machine_id')
    url = data.get('url')
    title = data.get('title', '')
    profile_name = data.get('profile_name', 'Unknown')
    
    if not machine_id or not url:
        return jsonify({"error": "Missing machine_id or url"}), 400
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    try:
        c.execute('''INSERT INTO browsing_history (machine_id, url, title, profile_name)
                     VALUES (?, ?, ?, ?)''',
                  (machine_id, url, title, profile_name))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

@app.route('/api/history', methods=['GET'])
@requires_auth
def get_history():
    """Get browsing history - recent 100 mixed or filtered by machine_id"""
    machine_id = request.args.get('machine_id')
    limit = int(request.args.get('limit', 100))
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    if machine_id:
        # Filter by specific machine
        c.execute('''SELECT * FROM browsing_history 
                     WHERE machine_id = ? 
                     ORDER BY visited_at DESC 
                     LIMIT ?''', (machine_id, limit))
    else:
        # Get recent 100 mixed
        c.execute('''SELECT * FROM browsing_history 
                     ORDER BY visited_at DESC 
                     LIMIT ?''', (limit,))
    
    history = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return jsonify(history)

@app.route('/api/history/users', methods=['GET'])
@requires_auth
def get_history_users():
    """Get list of unique machine IDs with history"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('''SELECT DISTINCT machine_id, 
                 COUNT(*) as visit_count,
                 MAX(visited_at) as last_visit
                 FROM browsing_history 
                 GROUP BY machine_id
                 ORDER BY last_visit DESC''')
    
    users = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return jsonify(users)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
