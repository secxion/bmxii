from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
import logging
from urllib.parse import quote_plus
from sqlalchemy import inspect
from dotenv import load_dotenv # Import load_dotenv

# Load environment variables from .env file (if it exists)
# This is good practice for local development, even if some values are hardcoded for now.
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Set the provided SECRET_KEY
# IMPORTANT: For production, this should be loaded from an environment variable!
app.config['SECRET_KEY'] = '928ye420-98-78398hr39\\LKJ'

# Database configuration for MySQL
# The '@' in your password 'Bmxii.DataBase@0219' needs to be URL-encoded as %40
# Using quote_plus to safely encode the password.
# IMPORTANT: For production, the database credentials should be loaded from environment variables!
db_password_encoded = quote_plus("Bmxii.DataBase@0219")
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://bmxii_user:{db_password_encoded}@localhost/bmxii_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_timeout': 20,
    'pool_recycle': 3600, # Recommended for MySQL to avoid "MySQL has gone away"
    'pool_pre_ping': True
}

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Models
class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    service = db.Column(db.String(100), nullable=True)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'service': self.service,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'is_read': self.is_read
        }

def init_database():
    """Initialize database tables using SQLAlchemy for MySQL"""
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully or already exist.")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise # Re-raise to ensure app doesn't start if tables can't be created

# Email configuration and sending function removed as per request for now.
# If you need email notifications later, you'll re-add this section
# and ensure credentials are loaded securely (e.g., from environment variables).

# Routes
@app.route('/')
def index():
    """Serve the main portfolio page by rendering index.html from the 'templates' folder."""
    # Flask's render_template automatically looks for 'index.html' in the 'templates' directory.
    return render_template('index.html')

@app.route('/api/contact', methods=['POST'])
def contact():
    """Handle contact form submissions"""
    try:
        data = request.get_json()

        # Validate required fields
        if not data or not data.get('name') or not data.get('email') or not data.get('message'):
            return jsonify({
                'error': 'Missing required fields: name, email, and message are required'
            }), 400

        # Create new contact message
        contact_message = ContactMessage(
            name=data['name'].strip(),
            email=data['email'].strip().lower(),
            phone=data.get('phone', '').strip() if data.get('phone') else None,
            service=data.get('service', '').strip() if data.get('service') else None,
            message=data['message'].strip()
        )

        # Save to database with error handling
        try:
            db.session.add(contact_message)
            db.session.commit()
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"Database error: {db_error}")
            return jsonify({'error': 'Database error occurred'}), 500

        # send_email_notification(data) # Removed as per request

        logger.info(f"New contact message received from {data['name']} ({data['email']})")

        return jsonify({
            'message': 'Contact message received successfully',
            'id': contact_message.id
        }), 201

    except Exception as e:
        logger.error(f"Error processing contact form: {str(e)}")
        return jsonify({
            'error': 'An error occurred while processing your message'
        }), 500

@app.route('/api/messages', methods=['GET'])
def get_messages():
    """Get all contact messages (admin endpoint)"""
    # Simple token-based authentication
    AUTH_TOKEN = os.getenv('ADMIN_API_TOKEN', 'changeme123')  # Set this in your .env for production
    auth_header = request.headers.get('Authorization', '')
    logger.info(f"DEBUG: Loaded AUTH_TOKEN from env: '{AUTH_TOKEN}'")
    logger.info(f"DEBUG: Received Authorization header: '{auth_header}'")
    if auth_header != f'Bearer {AUTH_TOKEN}':
        logger.warning(f"DEBUG: Authorization failed. Expected 'Bearer {AUTH_TOKEN}', got '{auth_header}'")
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        unread_only = request.args.get('unread_only', False, type=bool)

        query = ContactMessage.query

        if unread_only:
            query = query.filter_by(is_read=False)

        messages = query.order_by(ContactMessage.timestamp.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'messages': [msg.to_dict() for msg in messages.items],
            'total': messages.total,
            'pages': messages.pages,
            'current_page': page
        })

    except Exception as e:
        logger.error(f"Error fetching messages: {str(e)}")
        return jsonify({'error': 'Failed to fetch messages'}), 500

@app.route('/api/messages/<int:message_id>', methods=['GET'])
def get_message(message_id):
    """Get a specific message by ID"""
    try:
        message = ContactMessage.query.get_or_404(message_id)

        # Mark as read when accessed
        if not message.is_read:
            message.is_read = True
            db.session.commit()

        return jsonify(message.to_dict())

    except Exception as e:
        logger.error(f"Error fetching message {message_id}: {str(e)}")
        return jsonify({'error': 'Message not found'}), 404

@app.route('/api/messages/<int:message_id>/read', methods=['PUT'])
def mark_message_read(message_id):
    """Mark a message as read/unread"""
    try:
        message = ContactMessage.query.get_or_404(message_id)
        data = request.get_json()

        message.is_read = data.get('is_read', True)
        db.session.commit()

        return jsonify({
            'message': 'Message status updated',
            'is_read': message.is_read
        })

    except Exception as e:
        logger.error(f"Error updating message {message_id}: {str(e)}")
        return jsonify({'error': 'Failed to update message'}), 500

@app.route('/api/messages/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    """Delete a message"""
    try:
        message = ContactMessage.query.get_or_404(message_id)
        db.session.delete(message)
        db.session.commit()

        return jsonify({'message': 'Message deleted successfully'})

    except Exception as e:
        logger.error(f"Error deleting message {message_id}: {str(e)}")
        return jsonify({'error': 'Failed to delete message'}), 500

@app.route('/api/db-check', methods=['GET'])
def check_database():
    """Check database health and structure for MySQL"""
    try:
        with app.app_context():
            # Attempt a simple query to check connectivity
            db.session.execute(db.text("SELECT 1"))

            # Get table info using SQLAlchemy's inspector
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

            table_info = {}
            record_count = 0

            if 'contact_messages' in tables:
                # Get column info
                columns = inspector.get_columns('contact_messages')
                table_info['contact_messages_structure'] = [{'name': col['name'], 'type': str(col['type'])} for col in columns]

                # Count records
                record_count = db.session.query(ContactMessage).count()
            else:
                logger.warning("Table 'contact_messages' not found in MySQL database.")

        return jsonify({
            'status': 'success',
            'database_type': 'MySQL',
            'tables': tables,
            'contact_messages_structure': table_info.get('contact_messages_structure'),
            'record_count': record_count
        })

    except Exception as e:
        logger.error(f"Database check failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Database connection or query failed: {str(e)}"
        }), 500


@app.route('/admin')
def admin_dashboard():
    """Serve the admin dashboard page from a template file."""
    # This will now look for 'admin.html' in the 'templates' folder.
    return render_template('admin.html')

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get dashboard statistics"""
    try:
        total_messages = ContactMessage.query.count()
        unread_messages = ContactMessage.query.filter_by(is_read=False).count()
        today_messages = ContactMessage.query.filter(
            ContactMessage.timestamp >= datetime.now().date()
        ).count()

        return jsonify({
            'total_messages': total_messages,
            'unread_messages': unread_messages,
            'today_messages': today_messages
        })

    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        return jsonify({'error': 'Failed to fetch statistics'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Initialize database with proper error handling
    init_database()
    
    # Run the application
    # app.run(debug=False, host='0.0.0.0', port=5000)  # Commented out for Gunicorn deployment
