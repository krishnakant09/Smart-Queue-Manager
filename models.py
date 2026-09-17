import datetime
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from app import db_sql as db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(50), primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), default='customer')  # 'super_admin', 'business_admin', 'staff', 'customer'
    business_id = db.Column(db.String(50), db.ForeignKey('businesses.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Relationship to QueueItem
    queue_items = db.relationship('QueueItem', backref='user', lazy=True)
    feedbacks = db.relationship('QueueFeedback', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'role': self.role or 'customer',
            'business_id': self.business_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Business(db.Model):
    __tablename__ = 'businesses'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))
    status = db.Column(db.String(20), default='Open')
    status_color = db.Column(db.String(20), default='success')
    wait_time = db.Column(db.String(30))
    location = db.Column(db.String(100))
    queue_size = db.Column(db.Integer, default=0)
    business_type = db.Column(db.String(50))
    counters = db.Column(db.Text, default='Counter 1, Counter 2, Desk A')
    categories = db.Column(db.Text, default='General Inquiry:5, Standard Service:15, Priority Support:10')
    max_capacity = db.Column(db.Integer, default=50)
    is_paused = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    queue_items = db.relationship('QueueItem', backref='business', lazy=True)
    feedbacks = db.relationship('QueueFeedback', backref='business', lazy=True)

    def get_counters_list(self):
        if not self.counters:
            return ['Counter 1', 'Counter 2']
        return [c.strip() for c in self.counters.split(',') if c.strip()]

    def get_categories_list(self):
        """Returns list of dicts: [{'name': 'General Inquiry', 'duration': 5}, ...]"""
        if not self.categories:
            return [{'name': 'General Inquiry', 'duration': 5}]
        cats = []
        for cat in self.categories.split(','):
            cat = cat.strip()
            if not cat:
                continue
            if ':' in cat:
                parts = cat.split(':')
                try:
                    duration = int(parts[1].strip())
                except (ValueError, IndexError):
                    duration = 10
                cats.append({'name': parts[0].strip(), 'duration': duration})
            else:
                cats.append({'name': cat, 'duration': 10})
        return cats or [{'name': 'General Inquiry', 'duration': 5}]

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'status': self.status,
            'status_color': self.status_color,
            'wait_time': self.wait_time,
            'location': self.location,
            'queue_size': self.queue_size,
            'type': self.business_type,
            'counters': self.get_counters_list(),
            'categories': self.get_categories_list(),
            'max_capacity': self.max_capacity or 50,
            'is_paused': bool(self.is_paused)
        }


class QueueItem(db.Model):
    __tablename__ = 'queue_items'

    id = db.Column(db.String(50), primary_key=True)
    business_id = db.Column(db.String(50), db.ForeignKey('businesses.id'), nullable=False)
    user_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))  # Phone number for SMS notifications
    details = db.Column(db.Text)
    priority = db.Column(db.Integer, default=3)
    status = db.Column(db.String(20), default='waiting')  # 'waiting', 'called', 'completed', 'no_show', 'cancelled'
    service_category = db.Column(db.String(100), default='General Inquiry')
    assigned_counter = db.Column(db.String(50), nullable=True)
    delay_count = db.Column(db.Integer, default=0)
    delay_until = db.Column(db.DateTime, nullable=True)
    called_at = db.Column(db.DateTime, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    notified = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'business_id': self.business_id,
            'user_id': self.user_id,
            'name': self.name,
            'phone': self.phone,
            'details': self.details,
            'priority': self.priority,
            'status': self.status,
            'service_category': self.service_category or 'General Inquiry',
            'assigned_counter': self.assigned_counter,
            'delay_count': self.delay_count or 0,
            'called_at': self.called_at.isoformat() if self.called_at else None,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'notified': self.notified
        }


class QueueStatistics(db.Model):
    __tablename__ = 'queue_statistics'

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.String(50), db.ForeignKey('businesses.id'), nullable=False)
    total_served = db.Column(db.Integer, default=0)
    avg_wait_time = db.Column(db.Float, default=0.0)
    peak_queue_length = db.Column(db.Integer, default=0)
    current_queue_length = db.Column(db.Integer, default=0)
    csat_score = db.Column(db.Float, default=5.0)
    csat_count = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationship to Business
    business = db.relationship('Business', backref='statistics', lazy=True)

    def to_dict(self):
        avg_wait_time = self.avg_wait_time or 0
        if avg_wait_time < 1:
            avg_wait_time_display = f"{int(avg_wait_time * 60)} seconds"
        else:
            avg_wait_time_display = f"{round(avg_wait_time, 1)} minutes"

        return {
            'business_id': self.business_id,
            'total_served': self.total_served,
            'avg_wait_time': self.avg_wait_time,
            'avg_wait_time_display': avg_wait_time_display,
            'peak_queue_length': self.peak_queue_length,
            'current_queue_length': self.current_queue_length,
            'csat_score': round(self.csat_score or 5.0, 1),
            'csat_count': self.csat_count or 0
        }


class QueueFeedback(db.Model):
    __tablename__ = 'queue_feedback'

    id = db.Column(db.String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    queue_item_id = db.Column(db.String(50), nullable=True)
    business_id = db.Column(db.String(50), db.ForeignKey('businesses.id'), nullable=False)
    user_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=True)
    customer_name = db.Column(db.String(100), nullable=True)
    rating = db.Column(db.Integer, nullable=False, default=5)  # 1 to 5 stars
    tags = db.Column(db.String(255), nullable=True)  # e.g. "Fast Service, Friendly Staff"
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'queue_item_id': self.queue_item_id,
            'business_id': self.business_id,
            'customer_name': self.customer_name or 'Customer',
            'rating': self.rating,
            'tags': [t.strip() for t in self.tags.split(',')] if self.tags else [],
            'comment': self.comment or '',
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class QueueHistory(db.Model):
    __tablename__ = 'queue_history'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.String(50))
    business_id = db.Column(db.String(50), db.ForeignKey('businesses.id'), nullable=False)
    name = db.Column(db.String(100))
    wait_time = db.Column(db.Float)  # in minutes
    service_category = db.Column(db.String(100), nullable=True)
    counter = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    is_reset_marker = db.Column(db.Boolean, default=False)

    # Relationship to Business
    business = db.relationship('Business', backref='history', lazy=True)

    def to_dict(self):
        return {
            'id': self.item_id,
            'business_id': self.business_id,
            'name': self.name,
            'wait_time': self.wait_time,
            'service_category': self.service_category or 'General',
            'counter': self.counter or 'Counter 1',
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'is_reset_marker': self.is_reset_marker
        }