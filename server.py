from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cjonyx.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size

# Allowed file extensions for uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Helper functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_upload_folder():
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])


def get_event_status(event):
    """Return 'upcoming', 'ongoing' or 'past' for an event using actual datetimes."""
    now = datetime.utcnow()
    start = event.start_datetime or event.event_date
    end = event.end_datetime
    if start and end:
        if now < start:
            return 'upcoming'
        elif start <= now <= end:
            return 'ongoing'
        else:
            return 'past'
    elif start:
        return 'upcoming' if now < start else 'past'
    return 'unknown'


def get_event_sort_datetime(event):
    """Best-effort datetime used for sorting events."""
    return event.start_datetime or event.event_date or event.created_at or datetime.min


def classify_gallery_image_tags(image):
    """Infer gallery tags from linked event + description for client-side filtering."""
    tags = set()
    description = (image.description or '').lower()

    if image.event_id:
        tags.add('events')
        tags.add(f'event-{image.event_id}')

    if any(keyword in description for keyword in ['project', 'baseline', 'impact', 'enterprise', 'industry']):
        tags.add('projects')
    if any(keyword in description for keyword in ['team', 'staff', 'member']):
        tags.add('team')
    if any(keyword in description for keyword in ['facility', 'facilities', 'office', 'hub', 'center', 'centre', 'lab']):
        tags.add('facilities')

    # Keep non-event images visible under at least one non-event filter.
    if not tags:
        tags.add('projects')

    return sorted(tags)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.String(500))  # Keep nullable for SQLite compatibility
    image_url = db.Column(db.String(200))
    category = db.Column(db.String(50), nullable=False, default='Business')
    tags = db.Column(db.String(500))
    author_name = db.Column(db.String(100), default='Shulammite P.')
    author_title = db.Column(db.String(100), default='CEO & Founder at CJONYX')
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published = db.Column(db.Boolean, default=True)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    # For backward compatibility keep `event_date` but prefer `start_datetime`/`end_datetime`
    event_date = db.Column(db.DateTime)
    start_datetime = db.Column(db.DateTime)
    end_datetime = db.Column(db.DateTime)
    location = db.Column(db.String(200))
    image_url = db.Column(db.String(200))
    max_participants = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    published = db.Column(db.Boolean, default=True)
    allow_late_registration = db.Column(db.Boolean, default=False)
    # Relationship to gallery images
    galleries = db.relationship('Gallery', backref='event', lazy='dynamic')


class Gallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Optional link to an event
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=True)

class EventRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    event = db.relationship('Event', backref='registrations')
    user = db.relationship('User', backref='event_registrations')

class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100))
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    youtube_url = db.Column(db.String(200), nullable=False)
    thumbnail_url = db.Column(db.String(200))
    duration = db.Column(db.String(50))
    category = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    published = db.Column(db.Boolean, default=True)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    replied = db.Column(db.Boolean, default=False)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    replied = db.Column(db.Boolean, default=False)

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        print(f"[DEBUG] admin_required check: user_id={session.get('user_id')}, user={user}, is_admin={user.is_admin if user else 'N/A'}")
        if not user or not user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/debug/session')
def debug_session():
    return jsonify({
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'is_admin': session.get('is_admin'),
        'all_session': dict(session)
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            # Only allow non-admin users to login here
            if user.is_admin:
                flash('Admin users must use the admin login portal', 'error')
                return render_template('login.html')
            
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            print(f"[DEBUG] User login successful: user_id={user.id}, username={user.username}")
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('signup.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('signup.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

# Admin Authentication Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            # Only allow admin users to login here
            if not user.is_admin:
                flash('Only admin users can access this portal', 'error')
                return render_template('admin/admin_login.html')
            
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            print(f"[DEBUG] Admin login successful: user_id={user.id}, username={user.username}")
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials', 'error')
    
    return render_template('admin/admin_login.html')

# Admin Signup Route
@app.route('/admin/signup', methods=['GET', 'POST'])
def admin_signup():
    # Optional secret key for admin registration
    ADMIN_SECRET_KEY = "SUPER_ADMIN_2026"

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        secret_key = request.form['secret_key']

        # Validate secret key
        if secret_key != ADMIN_SECRET_KEY:
            flash('Invalid admin secret key', 'error')
            return render_template('admin/admin_signup.html')

        # Check passwords match
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('admin/admin_signup.html')

        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'error')
            return render_template('admin/admin_signup.html')

        # Check if email already exists
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email already exists', 'error')
            return render_template('admin/admin_signup.html')

        # Create admin account
        hashed_password = generate_password_hash(password)

        new_admin = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            is_admin=True
        )

        try:
            db.session.add(new_admin)
            db.session.commit()

            flash('Admin account created successfully', 'success')
            print(f"[DEBUG] Admin created: {username}")

            return redirect(url_for('admin_login'))

        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Admin signup failed: {e}")
            flash('Error creating admin account', 'error')

    return render_template('admin/admin_signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    # Get dashboard statistics
    total_users = User.query.count()
    total_blogs = Blog.query.count()
    total_events = Event.query.count()
    total_subscribers = Subscriber.query.count()
    total_contacts = Contact.query.count()
    total_chat_messages = ChatMessage.query.count()
    total_gallery_images = Gallery.query.count()
    unread_chat_messages = ChatMessage.query.filter_by(is_read=False).count()
    
    # Recent activities
    recent_blogs = Blog.query.order_by(Blog.created_at.desc()).limit(5).all()
    recent_events = Event.query.order_by(Event.created_at.desc()).limit(5).all()
    recent_subscribers = Subscriber.query.order_by(Subscriber.subscribed_at.desc()).limit(5).all()
    recent_chat_messages = ChatMessage.query.order_by(ChatMessage.created_at.desc()).limit(5).all()
    recent_gallery_images = Gallery.query.order_by(Gallery.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_blogs=total_blogs,
                         total_events=total_events,
                         total_subscribers=total_subscribers,
                         total_contacts=total_contacts,
                         total_chat_messages=total_chat_messages,
                         total_gallery_images=total_gallery_images,
                         unread_chat_messages=unread_chat_messages,
                         recent_blogs=recent_blogs,
                         recent_events=recent_events,
                         recent_subscribers=recent_subscribers,
                         recent_chat_messages=recent_chat_messages,
                         recent_gallery_images=recent_gallery_images)

# Blog Management Routes
@app.route('/admin/blogs')
@admin_required
def admin_blogs():
    blogs = Blog.query.order_by(Blog.created_at.desc()).all()
    return render_template('admin/blogs.html', blogs=blogs)

@app.route('/admin/blogs/new', methods=['GET', 'POST'])
@admin_required
def admin_new_blog():
    if request.method == 'POST':
        try:
            title = request.form['title']
            category = request.form['category']
            summary = request.form.get('summary', '')
            content = request.form['content']
            tags = request.form.get('tags', '')
            author_name = request.form.get('author_name', 'Shulammite P.')
            author_title = request.form.get('author_title', 'CEO & Founder at CJONYX')
            image_url = request.form.get('image_url', '').strip()
            image_file = request.files.get('image-upload')
            image_path = ''

            # Handle file upload if present
            if image_file and image_file.filename != '' and allowed_file(image_file.filename):
                create_upload_folder()
                filename = str(uuid.uuid4()) + '.' + image_file.filename.rsplit('.', 1)[1].lower()
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image_file.save(filepath)
                image_path = url_for('static', filename=f'uploads/{filename}')
            elif image_url:
                image_path = image_url
            else:
                image_path = ''

            blog = Blog(
                title=title,
                category=category,
                summary=summary,
                content=content,
                tags=tags,
                author_name=author_name,
                author_title=author_title,
                image_url=image_path,
                author_id=session['user_id'],
                published=(request.form.get('action') == 'publish')
            )
            db.session.add(blog)
            db.session.commit()
            flash('Blog post created successfully!', 'success')
            return redirect(url_for('admin_blogs'))
        except Exception as e:
            flash('Error creating blog post: ' + str(e), 'error')
    return render_template('admin/blog_form.html')

@app.route('/admin/blogs/<int:blog_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    if request.method == 'POST':
        try:
            blog.title = request.form['title']
            blog.category = request.form['category']
            blog.summary = request.form.get('summary', '')
            blog.content = request.form['content']
            blog.tags = request.form.get('tags', '')
            blog.author_name = request.form.get('author_name', 'Shulammite P.')
            blog.author_title = request.form.get('author_title', 'CEO & Founder at CJONYX')
            image_url = request.form.get('image_url', '').strip()
            image_file = request.files.get('image-upload')
            image_path = blog.image_url

            # Handle file upload if present
            if image_file and image_file.filename != '' and allowed_file(image_file.filename):
                create_upload_folder()
                filename = str(uuid.uuid4()) + '.' + image_file.filename.rsplit('.', 1)[1].lower()
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image_file.save(filepath)
                image_path = url_for('static', filename=f'uploads/{filename}')
            elif image_url:
                image_path = image_url
            blog.image_url = image_path
            blog.published = (request.form.get('action') == 'publish')
            db.session.commit()
            flash('Blog post updated successfully!', 'success')
            return redirect(url_for('admin_blogs'))
        except Exception as e:
            flash('Error updating blog post: ' + str(e), 'error')
    return render_template('admin/blog_form.html', blog=blog)

@app.route('/admin/blogs/<int:blog_id>/delete', methods=['POST'])
@admin_required
def admin_delete_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    db.session.delete(blog)
    db.session.commit()
    
    flash('Blog post deleted successfully!', 'success')
    return redirect(url_for('admin_blogs'))

# Image Upload Route
@app.route('/upload-image', methods=['POST'])
@admin_required
def upload_image():
    if 'image-upload' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['image-upload']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        # Create upload folder if it doesn't exist
        create_upload_folder()
        
        # Generate unique filename
        filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save file
        file.save(filepath)
        
        # Return URL for the uploaded image
        image_url = url_for('static', filename=f'uploads/{filename}')
        return jsonify({'url': image_url}), 200
    
    return jsonify({'error': 'Invalid file type'}), 400

# Serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Event Management Routes
@app.route('/admin/events')
@admin_required
def admin_events():
    events = Event.query.order_by(Event.start_datetime.desc()).all()
    for ev in events:
        ev.status = None
        try:
            ev.status = (get_event_status(ev) if 'get_event_status' in globals() else 'unknown')
        except Exception:
            ev.status = 'unknown'
    return render_template('admin/events.html', events=events)


@app.route('/admin/events/new', methods=['GET', 'POST'])
@admin_required
def admin_new_event():
    if request.method == 'POST':
        # parse start and end datetimes
        start_raw = request.form.get('start_datetime')
        end_raw = request.form.get('end_datetime')
        start_dt = datetime.strptime(start_raw, '%Y-%m-%dT%H:%M') if start_raw else None
        end_dt = datetime.strptime(end_raw, '%Y-%m-%dT%H:%M') if end_raw else None

        # image upload or URL
        image_path = request.form.get('image_url', '').strip()
        image_file = request.files.get('image-upload')
        if image_file and image_file.filename != '' and allowed_file(image_file.filename):
            create_upload_folder()
            filename = str(uuid.uuid4()) + '.' + image_file.filename.rsplit('.', 1)[1].lower()
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(filepath)
            image_path = url_for('static', filename=f'uploads/{filename}')

        event = Event(
            title=request.form.get('title', ''),
            description=request.form.get('description', ''),
            event_date=start_dt,
            start_datetime=start_dt,
            end_datetime=end_dt,
            location=request.form.get('location', ''),
            image_url=image_path,
            max_participants=int(request.form['max_participants']) if request.form.get('max_participants') else None,
            published=request.form.get('published') == 'on',
            allow_late_registration=(request.form.get('allow_late_registration') == 'on')
        )
        db.session.add(event)
        db.session.commit()
        # Handle multiple gallery image uploads (optional)
        gallery_files = request.files.getlist('gallery_images')
        # Descriptions can be provided as lines in a textarea; each line corresponds to a file by order
        gallery_descs = [line.strip() for line in request.form.get('gallery_descriptions', '').splitlines() if line.strip()]
        if gallery_files:
            create_upload_folder()
            for idx, gf in enumerate(gallery_files):
                if gf and gf.filename != '' and allowed_file(gf.filename):
                    filename = str(uuid.uuid4()) + '.' + gf.filename.rsplit('.', 1)[1].lower()
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    gf.save(filepath)
                    image_path = url_for('static', filename=f'uploads/{filename}')
                    desc = gallery_descs[idx] if idx < len(gallery_descs) else ''
                    gallery_item = Gallery(image_url=image_path, description=desc, event_id=event.id)
                    db.session.add(gallery_item)
            db.session.commit()
        flash('Event created successfully!', 'success')
        return redirect(url_for('admin_events'))

    return render_template('admin/event_form.html')


@app.route('/admin/events/<int:event_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    if request.method == 'POST':
        start_raw = request.form.get('start_datetime')
        end_raw = request.form.get('end_datetime')
        start_dt = datetime.strptime(start_raw, '%Y-%m-%dT%H:%M') if start_raw else None
        end_dt = datetime.strptime(end_raw, '%Y-%m-%dT%H:%M') if end_raw else None

        image_url = request.form.get('image_url', '').strip()
        image_file = request.files.get('image-upload')
        image_path = event.image_url
        if image_file and image_file.filename != '' and allowed_file(image_file.filename):
            create_upload_folder()
            filename = str(uuid.uuid4()) + '.' + image_file.filename.rsplit('.', 1)[1].lower()
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(filepath)
            image_path = url_for('static', filename=f'uploads/{filename}')
        elif image_url:
            image_path = image_url

        event.title = request.form.get('title', event.title)
        event.description = request.form.get('description', event.description)
        event.start_datetime = start_dt or event.start_datetime
        event.end_datetime = end_dt or event.end_datetime
        event.event_date = event.start_datetime or event.event_date
        event.location = request.form.get('location', event.location)
        event.image_url = image_path
        event.max_participants = int(request.form['max_participants']) if request.form.get('max_participants') else event.max_participants
        event.published = request.form.get('published') == 'on'
        event.allow_late_registration = (request.form.get('allow_late_registration') == 'on')

        db.session.commit()
        # Handle additional gallery uploads on edit (append)
        gallery_files = request.files.getlist('gallery_images')
        gallery_descs = [line.strip() for line in request.form.get('gallery_descriptions', '').splitlines() if line.strip()]
        if gallery_files:
            create_upload_folder()
            for idx, gf in enumerate(gallery_files):
                if gf and gf.filename != '' and allowed_file(gf.filename):
                    filename = str(uuid.uuid4()) + '.' + gf.filename.rsplit('.', 1)[1].lower()
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    gf.save(filepath)
                    image_path = url_for('static', filename=f'uploads/{filename}')
                    desc = gallery_descs[idx] if idx < len(gallery_descs) else ''
                    gallery_item = Gallery(image_url=image_path, description=desc, event_id=event.id)
                    db.session.add(gallery_item)
            db.session.commit()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('admin_events'))

    return render_template('admin/event_form.html', event=event)


@app.route('/admin/events/<int:event_id>/delete', methods=['POST'])
@admin_required
def admin_delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Delete all event registrations first (foreign key constraint)
    EventRegistration.query.filter_by(event_id=event_id).delete()
    
    # Now delete the event
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully!', 'success')
    return redirect(url_for('admin_events'))


@app.route('/admin/events/<int:event_id>/end', methods=['POST'])
@admin_required
def admin_end_event(event_id):
    event = Event.query.get_or_404(event_id)
    # Mark the event as ended by setting end_datetime to now
    event.end_datetime = datetime.utcnow()
    db.session.commit()
    flash('Event has been marked as ended.', 'success')
    return redirect(url_for('admin_events'))


# Gallery Admin Routes
@app.route('/admin/gallery')
@admin_required
def admin_gallery():
    images = Gallery.query.order_by(Gallery.created_at.desc()).all()
    return render_template('admin/gallery.html', images=images)


@app.route('/admin/gallery/new', methods=['GET', 'POST'])
@admin_required
def admin_new_gallery():
    if request.method == 'POST':
        description = request.form.get('description', '')
        image_file = request.files.get('image-upload')
        image_path = ''

        if image_file and image_file.filename != '' and allowed_file(image_file.filename):
            create_upload_folder()
            filename = str(uuid.uuid4()) + '.' + image_file.filename.rsplit('.', 1)[1].lower()
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(filepath)
            image_path = url_for('static', filename=f'uploads/{filename}')

        if not image_path:
            flash('Please provide an image file.', 'error')
            return redirect(url_for('admin_new_gallery'))

        gallery_item = Gallery(image_url=image_path, description=description)
        db.session.add(gallery_item)
        db.session.commit()
        flash('Gallery image added.', 'success')
        return redirect(url_for('admin_gallery'))

    return render_template('admin/gallery_form.html')


@app.route('/admin/gallery/<int:image_id>/delete', methods=['POST'])
@admin_required
def admin_delete_gallery(image_id):
    item = Gallery.query.get_or_404(image_id)
    db.session.delete(item)
    db.session.commit()
    flash('Gallery image deleted.', 'success')
    return redirect(url_for('admin_gallery'))

# Course Management Routes
@app.route('/admin/courses')
@login_required
def admin_courses():
    courses = Course.query.order_by(Course.created_at.desc()).all()
    return render_template('admin/courses.html', courses=courses)

@app.route('/admin/courses/new', methods=['GET', 'POST'])
@login_required
def admin_new_course():
    if request.method == 'POST':
        course = Course(
            title=request.form['title'],
            description=request.form['description'],
            youtube_url=request.form['youtube_url'],
            thumbnail_url=request.form['thumbnail_url'],
            duration=request.form['duration'],
            category=request.form['category'],
            published=request.form.get('published') == 'on'
        )
        
        db.session.add(course)
        db.session.commit()
        
        flash('Course created successfully!', 'success')
        return redirect(url_for('admin_courses'))
    
    return render_template('admin/course_form.html')

@app.route('/admin/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    if request.method == 'POST':
        course.title = request.form['title']
        course.description = request.form['description']
        course.youtube_url = request.form['youtube_url']
        course.thumbnail_url = request.form['thumbnail_url']
        course.duration = request.form['duration']
        course.category = request.form['category']
        course.published = request.form.get('published') == 'on'
        
        db.session.commit()
        
        flash('Course updated successfully!', 'success')
        return redirect(url_for('admin_courses'))
    
    return render_template('admin/course_form.html', course=course)

@app.route('/admin/courses/<int:course_id>/delete', methods=['POST'])
@login_required
def admin_delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    
    flash('Course deleted successfully!', 'success')
    return redirect(url_for('admin_courses'))

# Subscriber Management
@app.route('/admin/subscribers')
@login_required
def admin_subscribers():
    subscribers = Subscriber.query.order_by(Subscriber.subscribed_at.desc()).all()
    return render_template('admin/subscribers.html', subscribers=subscribers)

# Contact Messages Management
@app.route('/admin/contacts')
@login_required
def admin_contacts():
    contacts = Contact.query.order_by(Contact.created_at.desc()).all()
    return render_template('admin/contacts.html', contacts=contacts)

@app.route('/admin/contacts/<int:contact_id>/mark-read', methods=['POST'])
@login_required
def admin_mark_contact_read(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    contact.is_read = True
    db.session.commit()
    flash('Contact marked as read.', 'success')
    return redirect(url_for('admin_contacts'))

@app.route('/admin/contacts/<int:contact_id>/delete', methods=['POST'])
@login_required
def admin_delete_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    db.session.delete(contact)
    db.session.commit()
    flash('Contact message deleted successfully!', 'success')
    return redirect(url_for('admin_contacts'))

# Chat Messages Management
@app.route('/admin/chat-messages')
@login_required
def admin_chat_messages():
    chat_messages = ChatMessage.query.order_by(ChatMessage.created_at.desc()).all()
    return render_template('admin/chat_messages.html', chat_messages=chat_messages)

@app.route('/admin/chat-messages/<int:message_id>/mark-read', methods=['POST'])
@login_required
def admin_mark_chat_read(message_id):
    message = ChatMessage.query.get_or_404(message_id)
    message.is_read = True
    db.session.commit()
    flash('Chat message marked as read.', 'success')
    return redirect(url_for('admin_chat_messages'))

@app.route('/admin/chat-messages/<int:message_id>/delete', methods=['POST'])
@login_required
def admin_delete_chat_message(message_id):
    message = ChatMessage.query.get_or_404(message_id)
    db.session.delete(message)
    db.session.commit()
    flash('Chat message deleted successfully!', 'success')
    return redirect(url_for('admin_chat_messages'))

# Event Registration Management
@app.route('/admin/events/<int:event_id>/registrations')
@login_required
def admin_event_registrations(event_id):
    event = Event.query.get_or_404(event_id)
    registrations = EventRegistration.query.filter_by(event_id=event_id).all()
    return render_template('admin/event_registrations.html', event=event, registrations=registrations)

# Public subscription route
@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form['email']
    name = request.form.get('name', '')
    
    if Subscriber.query.filter_by(email=email).first():
        flash('Email already subscribed!', 'info')
        return redirect(request.referrer or url_for('index'))
    else:
        subscriber = Subscriber(email=email, name=name)
        db.session.add(subscriber)
        db.session.commit()
        flash('Successfully subscribed to our newsletter!', 'success')
        # Redirect to index with success parameter to show modal
        return redirect(url_for('index', subscribed='success'))

# Event registration route
@app.route('/events/<int:event_id>/register', methods=['POST'])
@login_required
def register_for_event(event_id):
    event = Event.query.get_or_404(event_id)
    # Prevent registration for past events
    try:
        status = get_event_status(event)
    except Exception:
        status = None
    if status in ('past', 'ongoing') and not getattr(event, 'allow_late_registration', False):
        if status == 'past':
            flash('This event has already ended. Registration is closed.', 'error')
        else:
            flash('This event is already ongoing. Registration is closed.', 'error')
        return redirect(request.referrer or url_for('events'))
    # Check if already registered
    existing_registration = EventRegistration.query.filter_by(event_id=event_id, user_id=session['user_id']).first()
    if existing_registration:
        flash('You are already registered for this event.', 'info')
    elif event.max_participants and len(event.registrations) >= event.max_participants:
        flash('Sorry, this event is full.', 'error')
    else:
        registration = EventRegistration(event_id=event_id, user_id=session['user_id'])
        db.session.add(registration)
        db.session.commit()
        flash('You have successfully registered for the event!', 'success')
    return redirect(request.referrer or url_for('events'))

@app.route('/')
def index():
    # Query all published events and choose a fallback set:
    # upcoming -> ongoing -> past.
    all_events = Event.query.filter(Event.published == True).all()

    upcoming_events = []
    ongoing_events = []
    past_events = []
    now = datetime.utcnow()

    for event in all_events:
        status = get_event_status(event)
        event.status = status
        event_start = get_event_sort_datetime(event)

        if status == 'upcoming' and event_start and now < event_start:
            upcoming_events.append(event)
        elif status == 'ongoing':
            ongoing_events.append(event)
        elif status == 'past':
            past_events.append(event)

    upcoming_events = sorted(upcoming_events, key=get_event_sort_datetime)[:2]
    ongoing_events = sorted(ongoing_events, key=get_event_sort_datetime, reverse=True)[:2]
    past_events = sorted(past_events, key=get_event_sort_datetime, reverse=True)[:2]

    if upcoming_events:
        selected_events = upcoming_events
        event_feed_type = 'upcoming'
    elif ongoing_events:
        selected_events = ongoing_events
        event_feed_type = 'ongoing'
    elif past_events:
        selected_events = past_events
        event_feed_type = 'past'
    else:
        selected_events = []
        event_feed_type = 'none'

    return render_template('index.html', events=selected_events, event_feed_type=event_feed_type)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/csed')
def csed():
    return render_template('csed.html')

@app.route('/course')
def course():
    courses = Course.query.filter_by(published=True).order_by(Course.created_at.desc()).all()
    # Get unique categories for filter buttons
    categories = list(set([course.category for course in courses if course.category]))
    return render_template('course.html', courses=courses, categories=categories)

@app.route('/contact', methods=['POST'])
def contact():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        if not all([name, email, message]):
            return jsonify({'success': False, 'message': 'All fields are required.'}), 400
        
        # Create new contact entry
        new_contact = Contact(
            name=name,
            email=email,
            message=message
        )
        
        db.session.add(new_contact)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Thank you for your message! We will get back to you soon.'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred while sending your message.'}), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        if not all([name, email, message]):
            return jsonify({'success': False, 'message': 'All fields are required.'}), 400
        
        # Create new chat message entry
        new_chat = ChatMessage(
            name=name,
            email=email,
            message=message
        )
        
        db.session.add(new_chat)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Thank you for reaching out! We will respond to your message shortly.'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred while sending your message.'}), 500

@app.route('/blog')
def blog():
    blogs = Blog.query.filter_by(published=True).order_by(Blog.created_at.desc()).all()
    return render_template('blog.html', blogs=blogs)

@app.route('/gallery')
def gallery():
    images = Gallery.query.order_by(Gallery.created_at.desc()).all()
    event_filters = {}
    for image in images:
        image.filter_tags = classify_gallery_image_tags(image)
        if image.event_id and image.event:
            event_filters[image.event_id] = image.event.title
    ordered_event_filters = sorted(event_filters.items(), key=lambda item: item[1].lower())
    return render_template('gallery.html', images=images, event_filters=ordered_event_filters)

@app.route('/blog/<int:blog_id>')
def blog_details(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    return render_template('blog_details.html', blog=blog)

@app.route('/events')
def events():
    events = Event.query.filter_by(published=True).order_by(Event.start_datetime.asc()).all()
    # annotate status for each event
    for ev in events:
        try:
            ev.status = get_event_status(ev)
        except Exception:
            ev.status = 'unknown'
    return render_template('events.html', events=events)

@app.route('/events/<int:event_id>')
def event_details(event_id):
    event = Event.query.get_or_404(event_id)
    if not event.published:
        return redirect(url_for('events'))
    
    # Get event status
    event.status = get_event_status(event)
    
    # Check if user is registered
    user_registered = False
    if 'user_id' in session:
        user_registered = EventRegistration.query.filter_by(
            event_id=event_id,
            user_id=session['user_id']
        ).first() is not None

    event_images = Gallery.query.filter_by(event_id=event_id).order_by(Gallery.created_at.desc()).all()

    return render_template('event_details.html', 
                         event=event, 
                         user_registered=user_registered,
                         event_images=event_images)

with app.app_context():
    # Create upload folder
    create_upload_folder()
    
    # Create database tables
    db.create_all()
    
    # Create admin user if it doesn't exist
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@cjonyx.com',
            password_hash=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created: username='admin', password='admin123'")

if __name__ == '__main__':
    app.run(debug=True)
