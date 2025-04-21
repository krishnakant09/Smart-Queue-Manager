import datetime
from app import db_sql as db


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
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationship to QueueItem
    queue_items = db.relationship('QueueItem', backref='business', lazy=True)

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
            'type': self.business_type
        }


class QueueItem(db.Model):
    __tablename__ = 'queue_items'

    id = db.Column(db.String(50), primary_key=True)
    business_id = db.Column(db.String(50), db.ForeignKey('businesses.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))  # Phone number for SMS notifications
    details = db.Column(db.Text)
    priority = db.Column(db.Integer, default=3)
    status = db.Column(db.String(20), default='waiting')
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    notified = db.Column(db.Boolean, default=False)  # Track if customer has been notified

    def to_dict(self):
        return {
            'id': self.id,
            'business_id': self.business_id,
            'name': self.name,
            'phone': self.phone,
            'details': self.details,
            'priority': self.priority,
            'status': self.status,
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
            'current_queue_length': self.current_queue_length
        }


class QueueHistory(db.Model):
    __tablename__ = 'queue_history'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.String(50))
    business_id = db.Column(db.String(50), db.ForeignKey('businesses.id'), nullable=False)
    name = db.Column(db.String(100))
    wait_time = db.Column(db.Float)  # in minutes
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
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'is_reset_marker': self.is_reset_marker
        }