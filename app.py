import os
import logging
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from replit_db import ReplitDB
from queue_manager import QueueManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Setup database
class Base(DeclarativeBase):
    pass

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key-for-development")

# Configure the database
db_url = os.environ.get("DATABASE_URL")
if not db_url:
    # Use SQLite when DATABASE_URL is not set for local development
    db_url = "sqlite:///queue_manager.db"
elif db_url.startswith("postgres://"):
    # SQLAlchemy 2.0+ requires postgresql:// instead of postgres://
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
if db_url.startswith("sqlite"):
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {}
else:
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the SQLAlchemy extension
db_sql = SQLAlchemy(model_class=Base)
db_sql.init_app(app)

# Initialize Replit DB and Queue Manager (for backward compatibility during migration)
replit_db = ReplitDB()
queue_manager = QueueManager(replit_db)

# Add a db alias to remain compatible with existing code during transition
db = replit_db

# Admin credentials - configurable via environment
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# Check if admin is set up
def initialize_admin():
    if not db.get("admin_password"):
        # Set default admin password if not exists
        db.set("admin_password", ADMIN_PASSWORD)
        logging.info("Admin password initialized")

# Initialize sample businesses if none exist
def initialize_businesses():
    # Check if we have any business entries in Replit DB (legacy)
    if not db.get("businesses_list"):
        # Store the list of business IDs
        business_ids = [
            "cafe-central",
            "urgent-care",
            "tech-store",
            "city-dmv",
            "hair-salon",
            "bank-first"
        ]
        db.set("businesses_list", business_ids)
        
        # Store each business as a separate entry to avoid size limitations
        db.set("business_cafe-central", {
            "id": "cafe-central",
            "name": "Cafe Central",
            "description": "Popular coffee shop with breakfast and lunch options",
            "icon": "fa-coffee",
            "status": "Open",
            "status_color": "success",
            "wait_time": "~10 min wait",
            "location": "Downtown",
            "queue_size": 4,
            "type": "cafe"
        })
        
        db.set("business_urgent-care", {
            "id": "urgent-care",
            "name": "Urgent Care Clinic",
            "description": "Walk-in medical clinic for non-emergency care",
            "icon": "fa-hospital",
            "status": "Busy",
            "status_color": "warning",
            "wait_time": "~45 min wait",
            "location": "Medical District",
            "queue_size": 12,
            "type": "medical"
        })
        
        db.set("business_tech-store", {
            "id": "tech-store",
            "name": "TechNow Store",
            "description": "Electronics retail store with repair services",
            "icon": "fa-laptop",
            "status": "Open",
            "status_color": "success",
            "wait_time": "~5 min wait",
            "location": "Shopping Mall",
            "queue_size": 2,
            "type": "retail"
        })
        
        db.set("business_city-dmv", {
            "id": "city-dmv",
            "name": "City DMV Office",
            "description": "Driver and vehicle services",
            "icon": "fa-id-card",
            "status": "Very Busy",
            "status_color": "danger",
            "wait_time": "~90 min wait",
            "location": "City Center",
            "queue_size": 35,
            "type": "government"
        })
        
        db.set("business_hair-salon", {
            "id": "hair-salon",
            "name": "Chic Hair Salon",
            "description": "Full-service hair salon and beauty services",
            "icon": "fa-cut",
            "status": "Moderate",
            "status_color": "info",
            "wait_time": "~25 min wait",
            "location": "Fashion District",
            "queue_size": 5,
            "type": "beauty"
        })
        
        db.set("business_bank-first", {
            "id": "bank-first",
            "name": "First National Bank",
            "description": "Banking services with personal assistance",
            "icon": "fa-university",
            "status": "Open",
            "status_color": "success",
            "wait_time": "~15 min wait",
            "location": "Financial District",
            "queue_size": 7,
            "type": "financial"
        })
        
        logging.info("Sample businesses initialized in Replit DB")
    
    # Check if we have any business entries in PostgreSQL
    from models import Business
    if db_sql.session.query(Business).count() == 0:
        # Create sample businesses in the PostgreSQL database
        businesses = [
            Business(
                id="cafe-central",
                name="Cafe Central",
                description="Popular coffee shop with breakfast and lunch options",
                icon="fa-coffee",
                status="Open",
                status_color="success",
                wait_time="~10 min wait",
                location="Downtown",
                queue_size=4,
                business_type="cafe"
            ),
            Business(
                id="urgent-care",
                name="Urgent Care Clinic",
                description="Walk-in medical clinic for non-emergency care",
                icon="fa-hospital",
                status="Busy",
                status_color="warning",
                wait_time="~45 min wait",
                location="Medical District",
                queue_size=12,
                business_type="medical"
            ),
            Business(
                id="tech-store",
                name="TechNow Store",
                description="Electronics retail store with repair services",
                icon="fa-laptop",
                status="Open",
                status_color="success",
                wait_time="~5 min wait",
                location="Shopping Mall",
                queue_size=2,
                business_type="retail"
            ),
            Business(
                id="city-dmv",
                name="City DMV Office",
                description="Driver and vehicle services",
                icon="fa-id-card",
                status="Very Busy",
                status_color="danger",
                wait_time="~90 min wait",
                location="City Center",
                queue_size=35,
                business_type="government"
            ),
            Business(
                id="hair-salon",
                name="Chic Hair Salon",
                description="Full-service hair salon and beauty services",
                icon="fa-cut",
                status="Moderate",
                status_color="info",
                wait_time="~25 min wait",
                location="Fashion District",
                queue_size=5,
                business_type="beauty"
            ),
            Business(
                id="bank-first",
                name="First National Bank",
                description="Banking services with personal assistance",
                icon="fa-university",
                status="Open",
                status_color="success",
                wait_time="~15 min wait",
                location="Financial District",
                queue_size=7,
                business_type="financial"
            )
        ]
        
        # Add the businesses to the database
        for business in businesses:
            db_sql.session.add(business)
        
        # Create initial statistics for each business
        from models import QueueStatistics
        for business in businesses:
            stats = QueueStatistics(
                business_id=business.id,
                total_served=0,
                avg_wait_time=0.0,
                peak_queue_length=0,
                current_queue_length=business.queue_size
            )
            db_sql.session.add(stats)
        
        db_sql.session.commit()
        logging.info("Sample businesses initialized in PostgreSQL")

def ensure_database_schema():
    """Ensure newly added columns and tables are safely migrated in SQLite/Postgres"""
    from sqlalchemy import inspect, text
    inspector = inspect(db_sql.engine)
    
    migrations = {
        'users': [
            ('role', "VARCHAR(20) DEFAULT 'customer'"),
            ('business_id', "VARCHAR(50)")
        ],
        'businesses': [
            ('counters', "TEXT DEFAULT 'Counter 1, Counter 2, Desk A'"),
            ('categories', "TEXT DEFAULT 'General Inquiry:5, Standard Service:15, Priority Support:10'"),
            ('max_capacity', "INTEGER DEFAULT 50"),
            ('is_paused', "BOOLEAN DEFAULT 0")
        ],
        'queue_items': [
            ('service_category', "VARCHAR(100) DEFAULT 'General Inquiry'"),
            ('assigned_counter', "VARCHAR(50)"),
            ('delay_count', "INTEGER DEFAULT 0"),
            ('delay_until', "DATETIME"),
            ('called_at', "DATETIME")
        ],
        'queue_statistics': [
            ('csat_score', "FLOAT DEFAULT 5.0"),
            ('csat_count', "INTEGER DEFAULT 0")
        ],
        'queue_history': [
            ('service_category', "VARCHAR(100)"),
            ('counter', "VARCHAR(50)")
        ]
    }
    
    with db_sql.engine.connect() as conn:
        for table_name, columns in migrations.items():
            if inspector.has_table(table_name):
                existing_cols = [c['name'] for c in inspector.get_columns(table_name)]
                for col_name, col_type in columns:
                    if col_name not in existing_cols:
                        try:
                            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))
                            conn.commit()
                            logging.info(f"Added missing column {col_name} to {table_name}")
                        except Exception as ex:
                            logging.warning(f"Could not add column {col_name} to {table_name}: {ex}")

# Create database tables before initialization
with app.app_context():
    # Import models to ensure they're registered with SQLAlchemy
    from models import User, Business, QueueItem, QueueStatistics, QueueHistory, QueueFeedback
    
    # Create any missing tables (e.g. queue_feedback)
    db_sql.create_all()
    
    # Safely migrate existing tables for newly added columns
    ensure_database_schema()
    
    # Then initialize data
    initialize_admin()
    initialize_businesses()

# Context processor to inject authenticated customer user into all templates
@app.context_processor
def inject_user():
    current_user = None
    user_id = session.get('user_id')
    if user_id:
        from models import User
        user = db_sql.session.get(User, user_id)
        if user:
            current_user = user.to_dict()
    return dict(current_user=current_user)

# ==========================================
# Anti-Abuse, AI Predictor & RBAC Helpers
# ==========================================
JOIN_RATE_LIMIT = {}  # ip -> [timestamps]

def check_join_rate_limit(ip_address):
    """Rate limit join requests: max 6 requests per 5 minutes per IP"""
    import time
    now = time.time()
    window = 300  # 5 minutes
    timestamps = JOIN_RATE_LIMIT.get(ip_address, [])
    timestamps = [t for t in timestamps if now - t < window]
    if len(timestamps) >= 6:
        JOIN_RATE_LIMIT[ip_address] = timestamps
        return False
    timestamps.append(now)
    JOIN_RATE_LIMIT[ip_address] = timestamps
    return True

def predict_wait_time(business_id, position, service_category=None):
    """
    Intelligent AI wait time estimation engine.
    Factors in service category duration, number of active counters,
    time-of-day rush multiplier, and historical throughput.
    """
    from models import Business, QueueStatistics
    business = db_sql.session.get(Business, business_id)
    stats = QueueStatistics.query.filter_by(business_id=business_id).first()
    
    base_duration = 10  # minutes default
    if business:
        cats = business.get_categories_list()
        for c in cats:
            if service_category and c['name'].lower() == service_category.lower():
                base_duration = c['duration']
                break
    
    num_counters = len(business.get_counters_list()) if business else 1
    effective_counters = max(1, num_counters)
    
    # Historical blend
    hist_avg = stats.avg_wait_time if (stats and stats.avg_wait_time and stats.avg_wait_time > 0) else base_duration
    blended_unit_time = (base_duration * 0.6) + (hist_avg * 0.4)
    
    # Rush hour multiplier (lunch 12-14 and evening 17-19)
    current_hour = datetime.utcnow().hour
    rush_multiplier = 1.25 if current_hour in [12, 13, 14, 17, 18, 19] else 1.0
    
    if position <= 0:
        est_minutes = 0
    else:
        est_minutes = max(1, round(((position * blended_unit_time) / effective_counters) * rush_multiplier))
        
    confidence = 95 if (stats and (stats.total_served or 0) > 10) else 82
    
    return {
        "minutes": est_minutes,
        "display": f"~{est_minutes} min",
        "confidence": f"{confidence}%",
        "is_rush_hour": rush_multiplier > 1.0
    }

def is_admin_or_staff(business_id=None):
    """Check if current session or user has admin or staff privileges"""
    if session.get('admin'):
        return True
    user_id = session.get('user_id')
    if user_id:
        from models import User
        user = db_sql.session.get(User, user_id)
        if user and user.role in ('super_admin', 'business_admin', 'staff'):
            if business_id and user.role in ('business_admin', 'staff') and user.business_id:
                return user.business_id == business_id
            return True
    return False

# Routes
@app.route('/')
def index():
    """Home page displaying available businesses"""
    # Get businesses from PostgreSQL
    from models import Business
    businesses_sql = Business.query.all()
    businesses = [business.to_dict() for business in businesses_sql]
    
    return render_template('businesses.html', businesses=businesses)

@app.route('/queue/<business_id>')
def business_queue(business_id):
    """Individual business queue page"""
    # Get business details from PostgreSQL
    from models import Business, QueueStatistics, QueueItem
    business_sql = db_sql.session.get(Business, business_id)
    
    if not business_sql:
        flash("Business not found", "danger")
        return redirect(url_for('index'))
    
    business = business_sql.to_dict()
    
    # Get queue items from PostgreSQL
    queue_items_sql = QueueItem.query.filter_by(
        business_id=business_id, 
        status='waiting'
    ).order_by(
        QueueItem.priority.desc(),
        QueueItem.timestamp.asc()
    ).all()
    
    # Convert to dict for template
    queue_items = [item.to_dict() for item in queue_items_sql]
    
    # If no items in PostgreSQL, fallback to Replit DB
    if not queue_items:
        # Get queue specific to this business (prefixed with business_id)
        queue_prefix = f"{business_id}_"
        queue_items = queue_manager.get_all_items(queue_prefix=queue_prefix)
    
    # Get statistics from PostgreSQL
    stats_sql = QueueStatistics.query.filter_by(business_id=business_id).first()
    if stats_sql:
        stats = stats_sql.to_dict()
    else:
        # Fallback to Replit DB
        queue_prefix = f"{business_id}_"
        stats = queue_manager.get_statistics(queue_prefix=queue_prefix)
    
    return render_template('business_queue.html', 
                          queue_items=queue_items, 
                          stats=stats, 
                          business=business)

@app.route('/queue/<business_id>/join', methods=['POST'])
def join_queue(business_id):
    """Process joining the queue via form submission (Requires user sign in)"""
    user_id = session.get('user_id')
    if not user_id:
        flash("Please sign in or create an account to join the queue.", "warning")
        return redirect(url_for('user_login', next=url_for('business_queue', business_id=business_id)))

    # Anti-abuse: Check IP rate limit
    client_ip = request.remote_addr or '127.0.0.1'
    if not check_join_rate_limit(client_ip):
        flash("Too many requests from your device. Please wait a few minutes before taking another ticket.", "danger")
        return redirect(url_for('business_queue', business_id=business_id))

    # Get business details
    from models import Business, QueueItem, QueueStatistics, User
    business = db_sql.session.get(Business, business_id)
    
    if not business:
        flash("Business not found", "danger")
        return redirect(url_for('index'))

    # Check if business queue is paused
    if getattr(business, 'is_paused', False):
        flash("This venue has temporarily paused new queue entries. Please check back shortly.", "warning")
        return redirect(url_for('business_queue', business_id=business_id))
    
    # Check max capacity
    stats = QueueStatistics.query.filter_by(business_id=business_id).first()
    max_cap = getattr(business, 'max_capacity', 50) or 50
    if stats and (stats.current_queue_length or 0) >= max_cap:
        flash(f"This queue is currently at maximum capacity ({max_cap} customers). Please check back soon.", "warning")
        return redirect(url_for('business_queue', business_id=business_id))
    
    user = db_sql.session.get(User, user_id)
    # Get form data
    name = request.form.get('name') or (user.full_name if user else None) or (user.username if user else 'Customer')
    phone = (request.form.get('phone') or (user.phone if user else '')).strip()
    details = request.form.get('details', '')
    service_category = request.form.get('service_category') or 'General Inquiry'
    
    if not name or not phone:
        flash("Name and phone number are required to join the queue.", "danger")
        return redirect(url_for('business_queue', business_id=business_id))

    # Anti-abuse: Duplicate active ticket check for the same phone number
    existing_ticket = QueueItem.query.filter(
        QueueItem.business_id == business_id,
        QueueItem.phone == phone,
        QueueItem.status.in_(['waiting', 'called', 'delayed'])
    ).first()
    if existing_ticket:
        flash("You already have an active ticket in this queue!", "info")
        return redirect(url_for('ticket_pass', item_id=existing_ticket.id))
    
    # Create a new queue item
    item_id = str(uuid.uuid4())
    current_time = datetime.now()
    
    # Create new queue item in PostgreSQL/SQLite
    new_item = QueueItem(
        id=item_id,
        business_id=business_id,
        user_id=user_id,
        name=name,
        phone=phone,
        details=details,
        service_category=service_category,
        priority=3,
        status='waiting',
        timestamp=current_time
    )
    
    # Add to database
    db_sql.session.add(new_item)
    
    # Update statistics
    if stats:
        stats.current_queue_length = (stats.current_queue_length or 0) + 1
        if stats.current_queue_length > (stats.peak_queue_length or 0):
            stats.peak_queue_length = stats.current_queue_length
    else:
        stats = QueueStatistics(
            business_id=business_id,
            total_served=0,
            avg_wait_time=0.0,
            peak_queue_length=1,
            current_queue_length=1
        )
        db_sql.session.add(stats)
    
    # Update business queue size
    business.queue_size = stats.current_queue_length
    
    # Add to Replit DB for backward compatibility
    queue_prefix = f"{business_id}_"
    replit_item = {
        'id': item_id,
        'name': name,
        'phone': phone,
        'details': details,
        'service_category': service_category,
        'priority': 3,
        'timestamp': current_time.isoformat(),
        'status': 'waiting'
    }
    queue_manager.add_item(replit_item, queue_prefix=queue_prefix)
    
    db_sql.session.commit()
    
    # AI Predicted wait time
    position = stats.current_queue_length
    prediction = predict_wait_time(business_id, position, service_category)
    wait_time = prediction["display"]
    
    # Send SMS confirmation
    try:
        from notifications import send_queue_confirmation
        business_name = business.name
        send_queue_confirmation(name, business_name, position, phone)
    except Exception as e:
        logging.error(f"Error sending SMS: {str(e)}")
    
    # Redirect to confirmation page
    ticket_url = url_for('ticket_pass', item_id=item_id, _external=True)
    return render_template('queue_confirmation.html', 
                           business=business,
                           item=new_item,
                           item_id=item_id,
                           position=position,
                           phone=phone,
                           wait_time=wait_time,
                           prediction=prediction,
                           ticket_url=ticket_url,
                           total_waiting=stats.current_queue_length)

# ==========================================
# User / Customer Authentication & Dashboard
# ==========================================

@app.route('/user/register', methods=['GET', 'POST'])
@app.route('/register', methods=['GET', 'POST'])
def user_register():
    """Customer user registration"""
    next_page = request.args.get('next') or request.form.get('next')
    if session.get('user_id'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': True, 'redirect': next_page or url_for('user_dashboard')})
        return redirect(next_page or url_for('user_dashboard'))

    error = None
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json

    if request.method == 'POST':
        from models import User
        if request.is_json:
            req_data = request.get_json() or {}
            full_name = req_data.get('full_name', '').strip()
            username = req_data.get('username', '').strip()
            email = req_data.get('email', '').strip().lower()
            phone = req_data.get('phone', '').strip()
            password = req_data.get('password', '')
            confirm_password = req_data.get('confirm_password', '')
        else:
            full_name = request.form.get('full_name', '').strip()
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            phone = request.form.get('phone', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')

        if not username or not email or not password:
            error = "Username, email, and password are required."
        elif password != confirm_password:
            error = "Passwords do not match."
        elif len(password) < 6:
            error = "Password must be at least 6 characters long."
        elif User.query.filter_by(username=username).first():
            error = f"Username '{username}' is already taken."
        elif User.query.filter_by(email=email).first():
            error = f"An account with email '{email}' already exists."
        else:
            user_id = str(uuid.uuid4())
            new_user = User(
                id=user_id,
                username=username,
                email=email,
                full_name=full_name or username,
                phone=phone
            )
            new_user.set_password(password)
            db_sql.session.add(new_user)
            db_sql.session.commit()

            # Auto log in
            session['user_id'] = new_user.id
            session['user_name'] = new_user.full_name or new_user.username
            flash("Welcome! Your account has been created successfully.", "success")
            target_url = next_page or url_for('user_dashboard')
            if is_ajax:
                return jsonify({'success': True, 'redirect': target_url})
            return redirect(target_url)

        if is_ajax:
            return jsonify({'success': False, 'error': error}), 400

    return render_template('user_login.html', error=error, active_tab='register')

@app.route('/user/login', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def user_login():
    """Customer user login"""
    next_page = request.args.get('next') or request.form.get('next')
    if session.get('user_id'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': True, 'redirect': next_page or url_for('user_dashboard')})
        return redirect(next_page or url_for('user_dashboard'))

    error = None
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json

    if request.method == 'POST':
        from models import User
        if request.is_json:
            req_data = request.get_json() or {}
            login_id = req_data.get('login_id', '').strip()
            password = req_data.get('password', '')
        else:
            login_id = request.form.get('login_id', '').strip()
            password = request.form.get('password', '')

        if not login_id or not password:
            error = "Please provide your username/email and password."
        else:
            # Look up by username or email
            user = User.query.filter(
                (User.username == login_id) | (User.email == login_id.lower())
            ).first()

            if user and user.check_password(password):
                session['user_id'] = user.id
                session['user_name'] = user.full_name or user.username
                flash(f"Welcome back, {user.full_name or user.username}!", "success")
                target_url = next_page or url_for('user_dashboard')
                if is_ajax:
                    return jsonify({'success': True, 'redirect': target_url})
                return redirect(target_url)
            else:
                error = "Invalid username/email or password."

        if is_ajax:
            return jsonify({'success': False, 'error': error}), 400

    active_tab = request.args.get('tab', 'login')
    return render_template('user_login.html', error=error, active_tab=active_tab)

@app.route('/user/logout')
@app.route('/logout')
def user_logout():
    """Customer user logout"""
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('admin', None)
    flash("You have been signed out successfully.", "info")
    return redirect(url_for('user_login'))

@app.route('/user/dashboard')
@app.route('/my-queues')
def user_dashboard():
    """Customer personal dashboard with active tickets & history"""
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to access your dashboard.", "warning")
        return redirect(url_for('user_login', next=request.path))

    from models import User, QueueItem, Business, QueueStatistics
    user = db_sql.session.get(User, user_id)
    if not user:
        session.pop('user_id', None)
        flash("User account not found. Please log in again.", "danger")
        return redirect(url_for('user_login'))

    # Active queues for this user
    active_items = QueueItem.query.filter_by(
        user_id=user_id,
        status='waiting'
    ).order_by(QueueItem.timestamp.asc()).all()

    active_tickets = []
    for item in active_items:
        biz = db_sql.session.get(Business, item.business_id)
        # Calculate current position in line
        earlier_count = QueueItem.query.filter(
            QueueItem.business_id == item.business_id,
            QueueItem.status == 'waiting',
            QueueItem.timestamp < item.timestamp
        ).count()
        position = earlier_count + 1

        # Get estimated wait time
        stats = QueueStatistics.query.filter_by(business_id=item.business_id).first()
        if stats and stats.avg_wait_time and stats.avg_wait_time > 0:
            if stats.avg_wait_time < 1:
                wait_min = int(stats.avg_wait_time * 60)
                wait_time = f"{wait_min} sec"
            else:
                wait_min = int(stats.avg_wait_time * position)
                wait_time = f"~{wait_min} min"
        else:
            wait_min = position * 5
            wait_time = f"~{wait_min} min"

        active_tickets.append({
            'item': item.to_dict(),
            'business': biz.to_dict() if biz else {'name': 'Unknown Business', 'id': item.business_id},
            'position': position,
            'wait_time': wait_time
        })

    # Past completed history
    past_items = QueueItem.query.filter_by(
        user_id=user_id
    ).filter(QueueItem.status != 'waiting').order_by(QueueItem.timestamp.desc()).limit(10).all()

    past_tickets = []
    for item in past_items:
        biz = db_sql.session.get(Business, item.business_id)
        past_tickets.append({
            'item': item.to_dict(),
            'business': biz.to_dict() if biz else {'name': 'Unknown Business', 'id': item.business_id}
        })

    # Suggested businesses
    all_businesses = Business.query.limit(6).all()
    businesses_list = [b.to_dict() for b in all_businesses]

    return render_template('user_dashboard.html',
                           user=user.to_dict(),
                           active_tickets=active_tickets,
                           past_tickets=past_tickets,
                           businesses=businesses_list)

@app.route('/user/queue/<item_id>/cancel', methods=['POST'])
def cancel_user_queue(item_id):
    """Allow customer to cancel their waiting spot"""
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to manage your queue ticket.", "danger")
        return redirect(url_for('user_login'))

    from models import QueueItem, Business, QueueStatistics
    queue_item = db_sql.session.get(QueueItem, item_id)
    if not queue_item or queue_item.user_id != user_id or queue_item.status != 'waiting':
        flash("Queue ticket not found or already completed.", "danger")
        return redirect(url_for('user_dashboard'))

    # Mark as cancelled
    queue_item.status = 'cancelled'
    queue_item.completed_at = datetime.now()

    # Update stats
    stats = QueueStatistics.query.filter_by(business_id=queue_item.business_id).first()
    if stats:
        stats.current_queue_length = max(0, (stats.current_queue_length or 0) - 1)
        biz = db_sql.session.get(Business, queue_item.business_id)
        if biz:
            biz.queue_size = stats.current_queue_length

    db_sql.session.commit()

    # Also remove from Replit DB if present
    try:
        queue_prefix = f"{queue_item.business_id}_"
        queue_manager.remove_item(item_id)
        replit_db.delete(f"{queue_prefix}{item_id}")
    except Exception as e:
        logging.error(f"Error removing from Replit DB: {str(e)}")

    flash("Your queue ticket has been cancelled successfully.", "info")
    return redirect(url_for('user_dashboard'))

@app.route('/admin', methods=['GET', 'POST'])
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    # If already logged in, redirect to admin panel
    if session.get('admin'):
        return redirect(url_for('admin_panel'))
    
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        valid_password = (password == ADMIN_PASSWORD or password == db.get("admin_password"))
        if username == ADMIN_USERNAME and valid_password:
            session['admin'] = True
            flash('Login successful', 'success')
            return redirect(url_for('admin_panel'))
        else:
            error = 'Invalid username or password'
    
    return render_template('admin_login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/panel')
def admin_panel():
    """Admin panel for queue management"""
    # Check if admin is logged in
    if not session.get('admin'):
        flash('Admin login required', 'danger')
        return redirect(url_for('admin_login'))
    
    # Get all businesses
    from models import Business, QueueStatistics, QueueItem
    businesses = Business.query.all()
    businesses_list = [b.to_dict() for b in businesses]
    
    # Get selected business ID from query parameter, defaulting to first business if available
    selected_business_id = request.args.get('business_id')
    if not selected_business_id and businesses_list:
        selected_business_id = businesses_list[0]['id']
        
    selected_business = None
    queue_items = []
    stats = None
    queue_count = 0
    
    if selected_business_id:
        # Get business details
        business = db_sql.session.get(Business, selected_business_id)
        if business:
            selected_business = business.to_dict()
            
            # Get active waiting & delayed queue items for this business
            queue_items_sql = QueueItem.query.filter(
                QueueItem.business_id == selected_business_id,
                QueueItem.status.in_(['waiting', 'delayed'])
            ).order_by(
                QueueItem.priority.desc(),
                QueueItem.timestamp.asc()
            ).all()
            
            queue_items = [item.to_dict() for item in queue_items_sql]
            
            # Get currently called customers (active at counter)
            called_items_sql = QueueItem.query.filter_by(
                business_id=selected_business_id,
                status='called'
            ).order_by(QueueItem.called_at.desc()).limit(5).all()
            called_items = [item.to_dict() for item in called_items_sql]

            # Get recent no-show customers (available for recall)
            no_show_items_sql = QueueItem.query.filter_by(
                business_id=selected_business_id,
                status='no_show'
            ).order_by(QueueItem.completed_at.desc()).limit(10).all()
            no_show_items = [item.to_dict() for item in no_show_items_sql]
            
            # Fallback to Replit DB if none found in SQL
            if not queue_items:
                queue_prefix = f"{selected_business_id}_"
                queue_items = queue_manager.get_all_items(queue_prefix=queue_prefix)
                
            queue_count = len(queue_items)
            
            # Get statistics
            stats_sql = QueueStatistics.query.filter_by(business_id=selected_business_id).first()
            if stats_sql:
                stats = stats_sql.to_dict()
            else:
                queue_prefix = f"{selected_business_id}_"
                stats = queue_manager.get_statistics(queue_prefix=queue_prefix)
        else:
            called_items = []
            no_show_items = []
    else:
        called_items = []
        no_show_items = []
    
    return render_template('admin_panel.html',
                         businesses=businesses_list,
                         selected_business_id=selected_business_id,
                         selected_business=selected_business,
                         queue_items=queue_items,
                         called_items=called_items,
                         no_show_items=no_show_items,
                         stats=stats,
                         queue_count=queue_count)

@app.route('/manage')
def manage():
    """Queue management page (admin only)"""
    if not session.get('admin'):
        flash('Admin login required', 'danger')
        return redirect(url_for('admin_login'))
    
    from models import QueueItem
    queue_items_sql = QueueItem.query.filter_by(status='waiting').order_by(
        QueueItem.priority.desc(),
        QueueItem.timestamp.asc()
    ).all()
    queue_items = [item.to_dict() for item in queue_items_sql]
    if not queue_items:
        queue_items = queue_manager.get_all_items()
        
    return render_template('queue_management.html', queue_items=queue_items)

@app.route('/statistics')
def statistics():
    """Queue statistics page with rush hour heatmap and CSAT reviews"""
    from models import QueueStatistics, QueueHistory, QueueFeedback, Business
    sql_history = QueueHistory.query.order_by(QueueHistory.completed_at.desc()).limit(100).all()
    all_stats = QueueStatistics.query.all()
    feedbacks = QueueFeedback.query.order_by(QueueFeedback.created_at.desc()).limit(10).all()
    businesses = Business.query.all()
    
    # Calculate 24-Hour Rush-Hour Heatmap
    hourly_counts = [0] * 24
    for h in sql_history:
        if h.timestamp:
            hr = h.timestamp.hour
            hourly_counts[hr] += 1
    max_count = max(hourly_counts + [1])
    rush_heatmap = [
        {
            "hour": f"{h:02d}:00",
            "count": count,
            "pct": min(100, max(8, round((count / max_count) * 100))),
            "level": "heat-high" if count >= max_count * 0.7 and count > 0 else ("heat-med" if count >= max_count * 0.35 and count > 0 else "heat-low")
        }
        for h, count in enumerate(hourly_counts)
    ]
    
    total_feedbacks = len(feedbacks)
    avg_csat = round(sum(f.rating for f in feedbacks) / total_feedbacks, 1) if total_feedbacks > 0 else 5.0

    if all_stats or sql_history:
        history = [h.to_dict() for h in sql_history]
        total_served = sum((s.total_served or 0) for s in all_stats)
        current_queue = sum((s.current_queue_length or 0) for s in all_stats)
        peak_queue = max([(s.peak_queue_length or 0) for s in all_stats] + [0])
        weighted_wait_sum = sum((s.avg_wait_time or 0) * (s.total_served or 0) for s in all_stats)
        overall_avg_wait = (weighted_wait_sum / total_served) if total_served > 0 else 0.0
        
        stats = {
            'total_served': total_served,
            'avg_wait_time': overall_avg_wait,
            'peak_queue_length': peak_queue,
            'current_queue_length': current_queue,
            'csat_score': avg_csat,
            'csat_count': total_feedbacks
        }
    else:
        stats = queue_manager.get_statistics()
        history = queue_manager.get_history()
        
    return render_template('statistics.html', 
                           stats=stats, 
                           history=history, 
                           rush_heatmap=rush_heatmap,
                           feedbacks=[f.to_dict() for f in feedbacks],
                           businesses=[b.to_dict() for b in businesses])

# API Endpoints
@app.route('/api/queue', methods=['GET'])
def get_queue():
    """Get all queue items"""
    from models import QueueItem
    business_id = request.args.get('business_id')
    if business_id:
        items = QueueItem.query.filter_by(
            business_id=business_id,
            status='waiting'
        ).order_by(
            QueueItem.priority.desc(),
            QueueItem.timestamp.asc()
        ).all()
        if items:
            return jsonify([item.to_dict() for item in items])
        queue_prefix = f"{business_id}_"
        return jsonify(queue_manager.get_all_items(queue_prefix=queue_prefix))
    else:
        items = QueueItem.query.filter_by(status='waiting').order_by(
            QueueItem.priority.desc(),
            QueueItem.timestamp.asc()
        ).all()
        if items:
            return jsonify([item.to_dict() for item in items])
        return jsonify(queue_manager.get_all_items())

@app.route('/api/queue', methods=['POST'])
def add_to_queue():
    """Add a new item to the queue"""
    # Rate limit check
    client_ip = request.remote_addr or '127.0.0.1'
    if not check_join_rate_limit(client_ip):
        return jsonify({"error": "Rate limit exceeded. Please wait a few minutes."}), 429

    data = request.json
    if not data or 'name' not in data:
        return jsonify({"error": "Name is required"}), 400
    
    # Get business ID if provided 
    business_id = data.get('business_id')
    phone = (data.get('phone') or '').strip()
    service_category = data.get('service_category') or 'General Inquiry'
    
    # Create a unique ID
    item_id = str(uuid.uuid4())
    current_time = datetime.now()
    
    # Add item to PostgreSQL database
    if business_id:
        # Check if business exists
        from models import Business, QueueItem, QueueStatistics
        business = db_sql.session.get(Business, business_id)
        
        if business:
            # Check pause status
            if getattr(business, 'is_paused', False):
                return jsonify({"error": "Queue is temporarily paused by venue"}), 403

            # Check capacity
            stats = QueueStatistics.query.filter_by(business_id=business_id).first()
            max_cap = getattr(business, 'max_capacity', 50) or 50
            if stats and (stats.current_queue_length or 0) >= max_cap:
                return jsonify({"error": f"Queue at maximum capacity ({max_cap})"}), 403

            # Anti-abuse: duplicate phone check
            if phone:
                existing = QueueItem.query.filter(
                    QueueItem.business_id == business_id,
                    QueueItem.phone == phone,
                    QueueItem.status.in_(['waiting', 'called', 'delayed'])
                ).first()
                if existing:
                    return jsonify({
                        "error": "Active ticket already exists for this phone number",
                        "ticket_id": existing.id
                    }), 400

            # Create new queue item
            new_item = QueueItem(
                id=item_id,
                business_id=business_id,
                name=data['name'],
                phone=phone,
                details=data.get('details', ''),
                service_category=service_category,
                priority=int(data.get('priority', 3)),
                status='waiting',
                timestamp=current_time
            )
            
            # Add to database
            db_sql.session.add(new_item)
            
            # Update statistics
            stats = QueueStatistics.query.filter_by(business_id=business_id).first()
            if stats:
                stats.current_queue_length = (stats.current_queue_length or 0) + 1
                if stats.current_queue_length > (stats.peak_queue_length or 0):
                    stats.peak_queue_length = stats.current_queue_length
            else:
                # Create new statistics record if none exists
                stats = QueueStatistics(
                    business_id=business_id,
                    total_served=0,
                    avg_wait_time=0.0,
                    peak_queue_length=1,
                    current_queue_length=1
                )
                db_sql.session.add(stats)
            
            # Update business queue size
            business.queue_size = stats.current_queue_length
            
            db_sql.session.commit()
            
            # Send SMS confirmation if phone number is provided
            phone = data.get('phone')
            if phone:
                try:
                    from notifications import send_queue_confirmation
                    position = stats.current_queue_length
                    business_name = business.name
                    send_queue_confirmation(data['name'], business_name, position, phone)
                except Exception as e:
                    logging.error(f"Error sending SMS: {str(e)}")
            
            # Also add to Replit DB for backward compatibility during transition
            queue_prefix = f"{business_id}_"
            item = {
                'id': item_id,
                'name': data['name'],
                'phone': data.get('phone', ''),
                'details': data.get('details', ''),
                'priority': int(data.get('priority', 3)),
                'timestamp': current_time.isoformat(),
                'status': 'waiting'
            }
            queue_manager.add_item(item, queue_prefix=queue_prefix)
        else:
            return jsonify({"error": "Business not found"}), 404
    else:
        # No business ID provided, just use Replit DB
        item = {
            'id': item_id,
            'name': data['name'],
            'phone': data.get('phone', ''),
            'details': data.get('details', ''),
            'priority': int(data.get('priority', 3)),
            'timestamp': current_time.isoformat(),
            'status': 'waiting'
        }
        item_id = queue_manager.add_item(item)
    
    return jsonify({"success": True, "id": item_id}), 201

@app.route('/api/queue/<item_id>', methods=['PUT'])
def update_queue_item(item_id):
    """Update a queue item"""
    if not session.get('admin'):
        return jsonify({"error": "Admin access required"}), 403
    
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    from models import QueueItem
    queue_item = db_sql.session.get(QueueItem, item_id)
    if queue_item:
        if 'name' in data:
            queue_item.name = data['name']
        if 'phone' in data:
            queue_item.phone = data['phone']
        if 'details' in data:
            queue_item.details = data['details']
        if 'priority' in data:
            try:
                queue_item.priority = int(data['priority'])
            except (ValueError, TypeError):
                pass
        if 'status' in data:
            queue_item.status = data['status']
            
        db_sql.session.commit()
        
        # Also update in Replit DB if present
        try:
            queue_manager.update_item(item_id, data)
        except Exception as e:
            logging.error(f"Error updating in Replit DB: {str(e)}")
            
        return jsonify({"success": True})
    
    # Fallback to Replit DB
    success = queue_manager.update_item(item_id, data)
    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Item not found"}), 404

@app.route('/api/queue/<item_id>', methods=['DELETE'])
def remove_from_queue(item_id):
    """Remove an item from the queue"""
    if not session.get('admin'):
        return jsonify({"error": "Admin access required"}), 403
    
    from models import QueueItem, QueueStatistics, Business
    queue_item = db_sql.session.get(QueueItem, item_id)
    if queue_item:
        business_id = queue_item.business_id
        # Mark as cancelled
        queue_item.status = 'cancelled'
        queue_item.completed_at = datetime.now()
        
        # Update statistics
        stats = QueueStatistics.query.filter_by(business_id=business_id).first()
        if stats:
            stats.current_queue_length = max(0, (stats.current_queue_length or 0) - 1)
            biz = db_sql.session.get(Business, business_id)
            if biz:
                biz.queue_size = stats.current_queue_length
        
        db_sql.session.commit()
        
        # Also clean up from Replit DB if present
        try:
            queue_prefix = f"{business_id}_"
            queue_manager.remove_item(item_id)
            replit_db.delete(f"{queue_prefix}{item_id}")
        except Exception as e:
            logging.error(f"Error removing from Replit DB: {str(e)}")
            
        return jsonify({"success": True})
    
    # Fallback to Replit DB
    success = queue_manager.remove_item(item_id)
    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Item not found"}), 404

@app.route('/api/queue/<item_id>/complete', methods=['POST'])
def complete_queue_item(item_id):
    """Mark an item as completed"""
    if not session.get('admin'):
        return jsonify({"error": "Admin access required"}), 403
    
    # Try to complete item in PostgreSQL
    from models import QueueItem, QueueStatistics, QueueHistory, Business
    
    # First, try to find the item in PostgreSQL
    queue_item = db_sql.session.get(QueueItem, item_id)
    
    if queue_item:
        # Item found in PostgreSQL, mark as completed
        business_id = queue_item.business_id
        name = queue_item.name
        
        # Calculate wait time
        completed_at = datetime.now()
        wait_time_delta = completed_at - queue_item.timestamp
        wait_time_minutes = wait_time_delta.total_seconds() / 60
        
        # Mark as completed
        queue_item.status = 'completed'
        queue_item.completed_at = completed_at
        
        # Add to history
        history_item = QueueHistory(
            item_id=item_id,
            business_id=business_id,
            name=name,
            wait_time=wait_time_minutes,
            timestamp=queue_item.timestamp,
            completed_at=completed_at
        )
        db_sql.session.add(history_item)
        
        # Update statistics
        stats = QueueStatistics.query.filter_by(business_id=business_id).first()
        if stats:
            # Update current queue length
            stats.current_queue_length = max(0, (stats.current_queue_length or 0) - 1)
            
            # Update total served
            stats.total_served = (stats.total_served or 0) + 1
            
            # Update average wait time
            if not stats.avg_wait_time or stats.avg_wait_time == 0:
                stats.avg_wait_time = wait_time_minutes
            else:
                # Weighted average calculation
                stats.avg_wait_time = (stats.avg_wait_time * (stats.total_served - 1) + wait_time_minutes) / stats.total_served
            
            # Update business queue size
            business = db_sql.session.get(Business, business_id)
            if business:
                business.queue_size = stats.current_queue_length
        
        # Commit changes
        db_sql.session.commit()
        
        # Also update in Replit DB for backward compatibility
        try:
            queue_prefix = f"{business_id}_"
            queue_manager.complete_item(item_id)
            replit_db.delete(f"{queue_prefix}{item_id}")
        except Exception as e:
            logging.error(f"Error updating item in Replit DB: {str(e)}")
        
        # Try to send notification if phone number is available
        if queue_item.phone:
            try:
                from notifications import send_turn_notification
                business = db_sql.session.get(Business, business_id)
                business_name = business.name if business else "Business"
                send_turn_notification(name, business_name, queue_item.phone)
            except Exception as e:
                logging.error(f"Error sending SMS: {str(e)}")
        
        feedback_url = url_for('feedback_page', item_id=item_id, _external=True)
        return jsonify({"success": True, "feedback_url": feedback_url})
    else:
        # Fallback to Replit DB
        success = queue_manager.complete_item(item_id)
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Item not found"}), 404

# ==========================================
# Advanced Operational & Voice Calling APIs
# ==========================================

@app.route('/api/queue/<item_id>/call', methods=['POST'])
def call_queue_item(item_id):
    """Staff calls next customer to a specific counter with TTS audio synthesis"""
    if not is_admin_or_staff():
        return jsonify({"error": "Admin/Staff authorization required"}), 403
    
    data = request.json or {}
    counter = data.get('counter', 'Counter 1')
    
    from models import QueueItem, Business
    item = db_sql.session.get(QueueItem, item_id)
    if not item:
        return jsonify({"error": "Queue item not found"}), 404
    
    item.status = 'called'
    item.assigned_counter = counter
    item.called_at = datetime.utcnow()
    db_sql.session.commit()
    
    # Notify customer via SMS if available
    if item.phone:
        try:
            from notifications import send_turn_notification
            biz = db_sql.session.get(Business, item.business_id)
            biz_name = biz.name if biz else "our venue"
            send_turn_notification(item.name, f"{biz_name} ({counter})", item.phone)
        except Exception as ex:
            logging.error(f"Failed to send turn SMS: {ex}")
    
    speech_text = f"Now serving {item.name}. Please proceed to {counter}."
    return jsonify({
        "success": True,
        "item": item.to_dict(),
        "counter": counter,
        "speech_text": speech_text
    })

@app.route('/api/queue/<item_id>/defer', methods=['POST'])
def defer_queue_item(item_id):
    """Customer 'I'm Running Late' action - Delays turn by 10 minutes (max 2 delays)"""
    from datetime import timedelta
    from models import QueueItem
    
    item = db_sql.session.get(QueueItem, item_id)
    if not item:
        return jsonify({"error": "Queue item not found"}), 404
    
    if item.status not in ('waiting', 'delayed'):
        return jsonify({"error": f"Cannot delay a ticket with status '{item.status}'"}), 400
    
    if (item.delay_count or 0) >= 2:
        return jsonify({"error": "Maximum delay limit (2 times) reached for this ticket."}), 400
    
    item.delay_count = (item.delay_count or 0) + 1
    item.status = 'delayed'
    # Shift timestamp forward by 10 minutes to move down in order
    item.timestamp = (item.timestamp or datetime.utcnow()) + timedelta(minutes=10)
    item.delay_until = datetime.utcnow() + timedelta(minutes=10)
    db_sql.session.commit()
    
    # Calculate new position
    earlier_count = QueueItem.query.filter(
        QueueItem.business_id == item.business_id,
        QueueItem.status.in_(['waiting', 'delayed']),
        QueueItem.timestamp < item.timestamp
    ).count()
    new_pos = earlier_count + 1
    
    return jsonify({
        "success": True,
        "message": f"Your turn has been delayed by 10 minutes. Your new position is #{new_pos}.",
        "new_position": new_pos,
        "delay_count": item.delay_count
    })

@app.route('/api/queue/<item_id>/no-show', methods=['POST'])
def no_show_queue_item(item_id):
    """Mark customer as No-Show with ability to recall later"""
    if not is_admin_or_staff():
        return jsonify({"error": "Admin/Staff authorization required"}), 403
    
    from models import QueueItem, QueueStatistics, Business
    item = db_sql.session.get(QueueItem, item_id)
    if not item:
        return jsonify({"error": "Queue item not found"}), 404
    
    item.status = 'no_show'
    item.completed_at = datetime.utcnow()
    
    stats = QueueStatistics.query.filter_by(business_id=item.business_id).first()
    if stats:
        stats.current_queue_length = max(0, (stats.current_queue_length or 0) - 1)
        biz = db_sql.session.get(Business, item.business_id)
        if biz:
            biz.queue_size = stats.current_queue_length
    
    db_sql.session.commit()
    return jsonify({"success": True})

@app.route('/api/queue/<item_id>/recall', methods=['POST'])
def recall_queue_item(item_id):
    """Recall a no-show customer back into the active queue"""
    if not is_admin_or_staff():
        return jsonify({"error": "Admin/Staff authorization required"}), 403
    
    from models import QueueItem, QueueStatistics, Business
    item = db_sql.session.get(QueueItem, item_id)
    if not item:
        return jsonify({"error": "Queue item not found"}), 404
    
    item.status = 'waiting'
    item.timestamp = datetime.utcnow()
    
    stats = QueueStatistics.query.filter_by(business_id=item.business_id).first()
    if stats:
        stats.current_queue_length = (stats.current_queue_length or 0) + 1
        biz = db_sql.session.get(Business, item.business_id)
        if biz:
            biz.queue_size = stats.current_queue_length
    
    db_sql.session.commit()
    return jsonify({"success": True})

@app.route('/api/queue/<item_id>/status')
def get_ticket_status(item_id):
    """Lightweight polling endpoint for live pass & position updates"""
    from models import QueueItem
    item = db_sql.session.get(QueueItem, item_id)
    if not item:
        return jsonify({"error": "Ticket not found"}), 404
    
    earlier_count = QueueItem.query.filter(
        QueueItem.business_id == item.business_id,
        QueueItem.status.in_(['waiting', 'delayed', 'called']),
        QueueItem.timestamp < item.timestamp
    ).count()
    position = earlier_count + 1 if item.status in ('waiting', 'delayed') else (1 if item.status == 'called' else 0)
    prediction = predict_wait_time(item.business_id, position, item.service_category)
    
    return jsonify({
        "id": item.id,
        "status": item.status,
        "position": position,
        "assigned_counter": item.assigned_counter,
        "delay_count": item.delay_count or 0,
        "estimated_wait": prediction["display"],
        "called_at": item.called_at.isoformat() if item.called_at else None
    })

@app.route('/api/business/<business_id>/settings', methods=['POST'])
def update_business_settings(business_id):
    """Update business settings (counters, categories, max capacity, pause)"""
    if not is_admin_or_staff(business_id):
        return jsonify({"error": "Admin authorization required"}), 403
    
    data = request.json or {}
    from models import Business
    biz = db_sql.session.get(Business, business_id)
    if not biz:
        return jsonify({"error": "Business not found"}), 404
    
    if 'counters' in data:
        biz.counters = data['counters']
    if 'categories' in data:
        biz.categories = data['categories']
    if 'max_capacity' in data:
        try:
            biz.max_capacity = int(data['max_capacity'])
        except (ValueError, TypeError):
            pass
    if 'is_paused' in data:
        biz.is_paused = bool(data['is_paused'])
    
    db_sql.session.commit()
    return jsonify({"success": True, "business": biz.to_dict()})

# ==========================================
# Entrance Poster, Digital Pass & CSAT Routes
# ==========================================

@app.route('/business/<business_id>/poster')
def business_poster(business_id):
    """Printable QR Code Entrance Door Poster for physical venues"""
    from models import Business, QueueStatistics
    business = db_sql.session.get(Business, business_id)
    if not business:
        flash("Business not found", "danger")
        return redirect(url_for('index'))
    
    stats = QueueStatistics.query.filter_by(business_id=business_id).first()
    target_url = url_for('business_queue', business_id=business.id, _external=True)
    return render_template('poster.html', business=business, stats=stats, target_url=target_url)

@app.route('/ticket/<item_id>')
def ticket_pass(item_id):
    """Digital Wallet Boarding Pass view with live sync and late deferrals"""
    from models import QueueItem, Business
    item = db_sql.session.get(QueueItem, item_id)
    if not item:
        flash("Ticket not found or expired", "danger")
        return redirect(url_for('index'))
    
    business = db_sql.session.get(Business, item.business_id)
    earlier_count = QueueItem.query.filter(
        QueueItem.business_id == item.business_id,
        QueueItem.status.in_(['waiting', 'delayed', 'called']),
        QueueItem.timestamp < item.timestamp
    ).count()
    position = earlier_count + 1 if item.status in ('waiting', 'delayed') else (1 if item.status == 'called' else 0)
    prediction = predict_wait_time(item.business_id, position, item.service_category)
    ticket_url = url_for('ticket_pass', item_id=item.id, _external=True)
    
    return render_template('ticket_pass.html',
                           item=item,
                           business=business,
                           position=position,
                           prediction=prediction,
                           ticket_url=ticket_url)

@app.route('/feedback/<item_id>')
def feedback_page(item_id):
    """Customer CSAT Feedback rating page"""
    from models import QueueItem, Business, QueueFeedback
    existing = QueueFeedback.query.filter_by(queue_item_id=item_id).first()
    item = db_sql.session.get(QueueItem, item_id)
    business = db_sql.session.get(Business, item.business_id) if item else None
    return render_template('feedback.html', 
                           item=item, 
                           business=business, 
                           existing=existing,
                           item_id=item_id)

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Submit customer CSAT 1-5 star review with sentiment tags"""
    data = request.json or {}
    queue_item_id = data.get('queue_item_id')
    business_id = data.get('business_id')
    rating = int(data.get('rating', 5))
    tags = data.get('tags', '')
    comment = data.get('comment', '')
    customer_name = data.get('customer_name', 'Valued Customer')
    
    if not business_id:
        return jsonify({"error": "Business ID is required"}), 400
    
    from models import QueueFeedback, QueueStatistics
    feedback = QueueFeedback(
        id=str(uuid.uuid4()),
        queue_item_id=queue_item_id,
        business_id=business_id,
        customer_name=customer_name,
        rating=rating,
        tags=tags,
        comment=comment
    )
    db_sql.session.add(feedback)
    
    # Recalculate CSAT score in statistics
    stats = QueueStatistics.query.filter_by(business_id=business_id).first()
    if stats:
        prev_count = stats.csat_count or 0
        prev_score = stats.csat_score or 5.0
        new_count = prev_count + 1
        new_score = ((prev_score * prev_count) + rating) / new_count
        stats.csat_score = round(new_score, 2)
        stats.csat_count = new_count
    
    db_sql.session.commit()
    return jsonify({"success": True, "message": "Thank you for your rating!"})

@app.route('/api/reports/export')
@app.route('/admin/export/csv')
def export_csv_report():
    """Stream downloadable CSV report of queue history and throughput metrics"""
    if not is_admin_or_staff():
        flash("Admin login required to export reports", "danger")
        return redirect(url_for('admin_login'))
    
    import csv
    import io
    from flask import make_response
    from models import QueueHistory
    
    business_id = request.args.get('business_id')
    query = QueueHistory.query
    if business_id:
        query = query.filter_by(business_id=business_id)
    records = query.order_by(QueueHistory.completed_at.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Ticket ID', 'Business ID', 'Customer Name', 'Service Category',
        'Assigned Counter', 'Wait Time (Minutes)', 'Check-in Time',
        'Completed Time', 'Status'
    ])
    
    for r in records:
        writer.writerow([
            r.item_id or '',
            r.business_id,
            r.name or 'Customer',
            r.service_category or 'General',
            r.counter or 'Counter 1',
            round(r.wait_time or 0, 1),
            r.timestamp.isoformat() if r.timestamp else '',
            r.completed_at.isoformat() if r.completed_at else '',
            'Reset Marker' if r.is_reset_marker else 'Completed'
        ])
    
    response = make_response(output.getvalue())
    filename = f"queue_report_{business_id or 'all'}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    response.headers['Content-Type'] = 'text/csv'
    return response

@app.route('/api/queue/statistics', methods=['GET'])
def get_statistics():
    """Get queue statistics"""
    from models import QueueStatistics
    business_id = request.args.get('business_id')
    if business_id:
        stats = QueueStatistics.query.filter_by(business_id=business_id).first()
        if stats:
            return jsonify(stats.to_dict())
        queue_prefix = f"{business_id}_"
        return jsonify(queue_manager.get_statistics(queue_prefix=queue_prefix))
    
    all_stats = QueueStatistics.query.all()
    if all_stats:
        total_served = sum((s.total_served or 0) for s in all_stats)
        current_queue = sum((s.current_queue_length or 0) for s in all_stats)
        peak_queue = max([(s.peak_queue_length or 0) for s in all_stats] + [0])
        weighted_wait_sum = sum((s.avg_wait_time or 0) * (s.total_served or 0) for s in all_stats)
        overall_avg_wait = (weighted_wait_sum / total_served) if total_served > 0 else 0.0
        return jsonify({
            'total_served': total_served,
            'avg_wait_time': overall_avg_wait,
            'peak_queue_length': peak_queue,
            'current_queue_length': current_queue
        })
    return jsonify(queue_manager.get_statistics())

@app.route('/api/queue/reset', methods=['POST'])
def reset_queue():
    """Reset the entire queue (admin only)"""
    if not session.get('admin'):
        return jsonify({"error": "Admin access required"}), 403
    
    # Get business_id from request data if provided
    data = request.json or {}
    business_id = data.get('business_id')
    
    # Reset queue in PostgreSQL
    from models import QueueItem, QueueStatistics, QueueHistory, Business
    
    if business_id:
        # Reset only for specific business
        with db_sql.session.begin():
            # Mark all waiting items as completed
            completed_at = datetime.now()
            
            # Find all waiting items for this business
            queue_items = QueueItem.query.filter_by(
                business_id=business_id,
                status='waiting'
            ).all()
            
            for item in queue_items:
                item.status = 'completed'
                item.completed_at = completed_at
            
            # Add a reset marker to history
            history_item = QueueHistory(
                item_id=f"reset_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                business_id=business_id,
                name="Queue Reset",
                wait_time=0,
                timestamp=completed_at,
                completed_at=completed_at,
                is_reset_marker=True
            )
            db_sql.session.add(history_item)
            
            # Reset statistics
            stats = QueueStatistics.query.filter_by(business_id=business_id).first()
            if stats:
                stats.current_queue_length = 0
                
                # Update business queue size
                business = db_sql.session.get(Business, business_id)
                if business:
                    business.queue_size = 0
        
        # Also reset in Replit DB for backward compatibility
        try:
            queue_prefix = f"{business_id}_"
            replit_items = queue_manager.get_all_items(queue_prefix=queue_prefix)
            
            for item in replit_items:
                # Extract the item ID from the key
                if '_id' in item:
                    item_id = item['_id']
                    queue_manager.remove_item(item_id)
            
            # Reset statistics
            stats_key = f"{queue_prefix}stats"
            stats = {
                "total_served": 0 if data.get('reset_stats') else (queue_manager.get_statistics(queue_prefix=queue_prefix).get('total_served', 0)),
                "avg_wait_time": 0,
                "peak_queue_length": 0,
                "current_queue_length": 0
            }
            db.set(stats_key, stats)
        except Exception as e:
            logging.error(f"Error resetting queue in Replit DB: {str(e)}")
    else:
        # Reset entire queue (this is less common)
        with db_sql.session.begin():
            # Mark all waiting items as completed
            completed_at = datetime.now()
            
            # Find all waiting items
            queue_items = QueueItem.query.filter_by(status='waiting').all()
            
            for item in queue_items:
                item.status = 'completed'
                item.completed_at = completed_at
            
            # Reset all business queue sizes
            businesses = Business.query.all()
            for business in businesses:
                business.queue_size = 0
            
            # Reset all statistics
            stats_all = QueueStatistics.query.all()
            for stats in stats_all:
                stats.current_queue_length = 0
        
        # Also reset in Replit DB for backward compatibility
        try:
            queue_manager.reset_queue()
        except Exception as e:
            logging.error(f"Error resetting queue in Replit DB: {str(e)}")
    
    return jsonify({"success": True})

# User-facing queue position check
@app.route('/check-position', methods=['GET', 'POST'])
def check_position():
    """Check position in queue by phone number"""
    from models import Business, QueueItem, QueueStatistics
    
    # Get all businesses for the dropdown
    businesses = Business.query.all()
    businesses_list = [b.to_dict() for b in businesses]
    
    # Get business ID from query parameter if provided
    business_id = request.args.get('business_id')
    
    if request.method == 'POST':
        # Get form data
        phone = (request.form.get('phone') or '').strip()
        business_id = request.form.get('business_id')
        
        if not phone or not business_id:
            return render_template('check_position.html', 
                                  error="Phone number and business are required",
                                  businesses=businesses_list,
                                  business_id=business_id)
        
        # Get business details
        business = db_sql.session.get(Business, business_id)
        if not business:
            return render_template('check_position.html', 
                                  error="Business not found",
                                  businesses=businesses_list)
        
        # Find the queue item by phone number and business ID
        queue_item = QueueItem.query.filter_by(
            business_id=business_id,
            phone=phone,
            status='waiting'
        ).order_by(QueueItem.timestamp.asc()).first()
        
        if not queue_item:
            # Try to find in Replit DB as fallback
            queue_prefix = f"{business_id}_"
            replit_items = queue_manager.get_all_items(queue_prefix=queue_prefix)
            
            for idx, item in enumerate(replit_items):
                if (item.get('phone') or '').strip() == phone and item.get('status') == 'waiting':
                    # Found in Replit DB
                    position = idx + 1
                    
                    # Get estimated wait time
                    stats = QueueStatistics.query.filter_by(business_id=business_id).first()
                    wait_time = "Unknown"
                    if stats and stats.avg_wait_time:
                        if stats.avg_wait_time < 1:
                            wait_min = int(stats.avg_wait_time * 60)
                            wait_time = f"{wait_min} seconds"
                        else:
                            wait_min = int(stats.avg_wait_time * position)
                            wait_time = f"~{wait_min} minutes"
                    
                    return render_template('check_position.html',
                                         position=position,
                                         wait_time=wait_time,
                                         business=business.to_dict(),
                                         businesses=businesses_list,
                                         business_id=business_id)
            
            # Not found in either database
            return render_template('check_position.html', 
                                  error="No queue entry found for this phone number",
                                  businesses=businesses_list,
                                  business_id=business_id)
        
        # If found in PostgreSQL, calculate position
        earlier_items = QueueItem.query.filter(
            QueueItem.business_id == business_id,
            QueueItem.status == 'waiting',
            QueueItem.timestamp < queue_item.timestamp
        ).count()
        
        position = earlier_items + 1
        
        # Get estimated wait time
        stats = QueueStatistics.query.filter_by(business_id=business_id).first()
        wait_time = "Unknown"
        if stats and stats.avg_wait_time:
            if stats.avg_wait_time < 1:
                wait_min = int(stats.avg_wait_time * 60)
                wait_time = f"{wait_min} seconds"
            else:
                wait_min = int(stats.avg_wait_time * position)
                wait_time = f"~{wait_min} minutes"
        
        return render_template('check_position.html',
                             position=position,
                             wait_time=wait_time,
                             business=business.to_dict(),
                             item=queue_item.to_dict(),
                             businesses=businesses_list,
                             business_id=business_id)
    
    # GET request
    return render_template('check_position.html', 
                          businesses=businesses_list,
                          business_id=business_id)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', error="Server error occurred"), 500
