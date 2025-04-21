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
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
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

# Admin credentials - hardcoded for simplicity
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Check if admin is set up
def initialize_admin():
    if not db.get("admin_password"):
        # Set default admin password if not exists
        db.set("admin_password", "admin123")  # Default password
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

# Create database tables before initialization
with app.app_context():
    # Import models to ensure they're registered with SQLAlchemy
    from models import Business, QueueItem, QueueStatistics, QueueHistory
    
    # Create all tables
    db_sql.create_all()
    
    # Then initialize data
    initialize_admin()
    initialize_businesses()

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
    business_sql = Business.query.get(business_id)
    
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
    """Process joining the queue via form submission"""
    # Get business details
    from models import Business, QueueItem, QueueStatistics
    business = Business.query.get(business_id)
    
    if not business:
        flash("Business not found", "danger")
        return redirect(url_for('index'))
    
    # Get form data
    name = request.form.get('name')
    phone = request.form.get('phone')
    details = request.form.get('details', '')
    
    if not name or not phone:
        flash("Name and phone number are required", "danger")
        return redirect(url_for('business_queue', business_id=business_id))
    
    # Create a new queue item
    item_id = str(uuid.uuid4())
    current_time = datetime.now()
    
    # Create new queue item in PostgreSQL
    new_item = QueueItem(
        id=item_id,
        business_id=business_id,
        name=name,
        phone=phone,
        details=details,
        priority=3,  # Default priority for form submissions
        status='waiting',
        timestamp=current_time
    )
    
    # Add to database
    db_sql.session.add(new_item)
    
    # Update statistics
    stats = QueueStatistics.query.filter_by(business_id=business_id).first()
    if stats:
        stats.current_queue_length += 1
        if stats.current_queue_length > stats.peak_queue_length:
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
    
    # Add to Replit DB for backward compatibility
    queue_prefix = f"{business_id}_"
    replit_item = {
        'name': name,
        'phone': phone,
        'details': details,
        'priority': 3,
        'timestamp': current_time.isoformat(),
        'status': 'waiting'
    }
    queue_manager.add_item(replit_item, queue_prefix=queue_prefix)
    
    db_sql.session.commit()
    
    # Calculate estimated wait time
    wait_time = "Unknown"
    if stats.avg_wait_time and stats.avg_wait_time > 0:
        if stats.avg_wait_time < 1:
            wait_min = int(stats.avg_wait_time * 60)
            wait_time = f"{wait_min} seconds"
        else:
            wait_min = int(stats.avg_wait_time)
            wait_time = f"{wait_min} minutes"
    elif stats.current_queue_length > 0:
        # If no avg wait time available, estimate based on number of people
        wait_min = stats.current_queue_length * 5  # Assume 5 minutes per person
        wait_time = f"~{wait_min} minutes"
    
    # Get position in queue
    position = stats.current_queue_length
    
    # Send SMS confirmation
    try:
        from notifications import send_queue_confirmation
        business_name = business.name
        send_queue_confirmation(name, business_name, position, phone)
    except Exception as e:
        logging.error(f"Error sending SMS: {str(e)}")
    
    # Redirect to confirmation page
    return render_template('queue_confirmation.html', 
                           business=business,
                           position=position,
                           phone=phone,
                           wait_time=wait_time,
                           total_waiting=stats.current_queue_length)

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    # If already logged in, redirect to admin panel
    if session.get('admin'):
        return redirect(url_for('admin_panel'))
    
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
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
    
    # Get selected business ID from query parameter
    selected_business_id = request.args.get('business_id')
    selected_business = None
    queue_items = []
    stats = None
    queue_count = 0
    
    if selected_business_id:
        # Get business details
        business = Business.query.get(selected_business_id)
        if business:
            selected_business = business.to_dict()
            
            # Get queue items for this business
            queue_items_sql = QueueItem.query.filter_by(
                business_id=selected_business_id,
                status='waiting'
            ).order_by(
                QueueItem.priority.desc(),
                QueueItem.timestamp.asc()
            ).all()
            
            queue_items = [item.to_dict() for item in queue_items_sql]
            queue_count = len(queue_items)
            
            # Get statistics
            stats_sql = QueueStatistics.query.filter_by(business_id=selected_business_id).first()
            if stats_sql:
                stats = stats_sql.to_dict()
            else:
                # Fallback to Replit DB
                queue_prefix = f"{selected_business_id}_"
                stats = queue_manager.get_statistics(queue_prefix=queue_prefix)
    
    return render_template('admin_panel.html',
                         businesses=businesses_list,
                         selected_business_id=selected_business_id,
                         selected_business=selected_business,
                         queue_items=queue_items,
                         stats=stats,
                         queue_count=queue_count)

# Legacy login routes - kept for backward compatibility
@app.route('/login', methods=['POST'])
def login():
    """Legacy admin login"""
    password = request.form.get('password')
    stored_password = db.get("admin_password")
    
    if password == stored_password:
        session['admin'] = True
        flash('Login successful', 'success')
    else:
        flash('Invalid password', 'danger')
    
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    """Legacy admin logout"""
    session.pop('admin', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/manage')
def manage():
    """Queue management page (admin only)"""
    if not session.get('admin'):
        flash('Admin login required', 'danger')
        return redirect(url_for('index'))
    
    queue_items = queue_manager.get_all_items()
    return render_template('queue_management.html', queue_items=queue_items)

@app.route('/statistics')
def statistics():
    """Queue statistics page"""
    stats = queue_manager.get_statistics()
    history = queue_manager.get_history()
    return render_template('statistics.html', stats=stats, history=history)

# API Endpoints
@app.route('/api/queue', methods=['GET'])
def get_queue():
    """Get all queue items"""
    business_id = request.args.get('business_id')
    queue_prefix = f"{business_id}_" if business_id else None
    return jsonify(queue_manager.get_all_items(queue_prefix=queue_prefix))

@app.route('/api/queue', methods=['POST'])
def add_to_queue():
    """Add a new item to the queue"""
    data = request.json
    if not data or 'name' not in data:
        return jsonify({"error": "Name is required"}), 400
    
    # Get business ID if provided 
    business_id = data.get('business_id')
    
    # Create a unique ID
    item_id = str(uuid.uuid4())
    current_time = datetime.now()
    
    # Add item to PostgreSQL database
    if business_id:
        # Check if business exists
        from models import Business, QueueItem, QueueStatistics
        business = Business.query.get(business_id)
        
        if business:
            # Create new queue item
            new_item = QueueItem(
                id=item_id,
                business_id=business_id,
                name=data['name'],
                phone=data.get('phone', ''),
                details=data.get('details', ''),
                priority=int(data.get('priority', 3)),
                status='waiting',
                timestamp=current_time
            )
            
            # Add to database
            db_sql.session.add(new_item)
            
            # Update statistics
            stats = QueueStatistics.query.filter_by(business_id=business_id).first()
            if stats:
                stats.current_queue_length += 1
                if stats.current_queue_length > stats.peak_queue_length:
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
    queue_item = QueueItem.query.get(item_id)
    
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
            stats.current_queue_length = max(0, stats.current_queue_length - 1)
            
            # Update total served
            stats.total_served += 1
            
            # Update average wait time
            if stats.avg_wait_time == 0:
                stats.avg_wait_time = wait_time_minutes
            else:
                # Weighted average calculation
                stats.avg_wait_time = (stats.avg_wait_time * (stats.total_served - 1) + wait_time_minutes) / stats.total_served
            
            # Update business queue size
            business = Business.query.get(business_id)
            if business:
                business.queue_size = stats.current_queue_length
        
        # Commit changes
        db_sql.session.commit()
        
        # Also update in Replit DB for backward compatibility
        try:
            queue_manager.complete_item(item_id)
        except Exception as e:
            logging.error(f"Error updating item in Replit DB: {str(e)}")
        
        # Try to send notification if phone number is available
        if queue_item.phone:
            try:
                from notifications import send_turn_notification
                business = Business.query.get(business_id)
                business_name = business.name if business else "Business"
                send_turn_notification(name, business_name, queue_item.phone)
            except Exception as e:
                logging.error(f"Error sending SMS: {str(e)}")
        
        return jsonify({"success": True})
    else:
        # Fallback to Replit DB
        success = queue_manager.complete_item(item_id)
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Item not found"}), 404

@app.route('/api/queue/statistics', methods=['GET'])
def get_statistics():
    """Get queue statistics"""
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
                business = Business.query.get(business_id)
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
        phone = request.form.get('phone')
        business_id = request.form.get('business_id')
        
        if not phone or not business_id:
            return render_template('check_position.html', 
                                  error="Phone number and business are required",
                                  businesses=businesses_list,
                                  business_id=business_id)
        
        # Get business details
        business = Business.query.get(business_id)
        if not business:
            return render_template('check_position.html', 
                                  error="Business not found",
                                  businesses=businesses_list)
        
        # Find the queue item by phone number and business ID
        queue_item = QueueItem.query.filter_by(
            business_id=business_id,
            phone=phone,
            status='waiting'
        ).first()
        
        if not queue_item:
            # Try to find in Replit DB as fallback
            queue_prefix = f"{business_id}_"
            replit_items = queue_manager.get_all_items(queue_prefix=queue_prefix)
            
            for idx, item in enumerate(replit_items):
                if item.get('phone') == phone and item.get('status') == 'waiting':
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
