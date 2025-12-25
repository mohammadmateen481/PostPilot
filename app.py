from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
import os
import uuid
from datetime import datetime
import bleach
from PIL import Image
import io

from config import Config
from database import db, User, Post, Comment, Like, Category
from forms import LoginForm, RegistrationForm, PostForm, CommentForm, ProfileForm

# Initialize extensions
bcrypt = Bcrypt()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'login'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)
    
    # Helper functions
    def generate_slug(title):
        """Generate URL-friendly slug from title"""
        import re
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s-]+', '-', slug)
        slug = slug.strip('-')
        return slug
    
    def save_image(image_file):
        """Save and resize uploaded image"""
        if not image_file:
            return None
        
        filename = str(uuid.uuid4()) + '.jpg'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Create upload folder if it doesn't exist
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Open and process image
        img = Image.open(image_file)
        
        # Resize if too large
        max_size = (1200, 800)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Save image
        img.save(filepath, 'JPEG', quality=85)
        
        return filename
    
    def sanitize_html(content):
        """Sanitize HTML content to prevent XSS"""
        allowed_tags = ['p', 'br', 'b', 'i', 'u', 'em', 'strong', 'h1', 'h2', 'h3', 
                       'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'a', 'blockquote', 'code', 'pre']
        allowed_attributes = {'a': ['href', 'title', 'target']}
        return bleach.clean(content, tags=allowed_tags, attributes=allowed_attributes)
    
    # Context processors
    @app.context_processor
    def inject_categories():
        categories = Category.query.all()
        return dict(categories=categories)
    
    @app.context_processor
    def inject_user():
        return dict(current_user=current_user)
    
    # Routes
    
    @app.route('/')
    def index():
        """Public blog feed"""
        page = request.args.get('page', 1, type=int)
        category = request.args.get('category')
        
        # Base query for published posts
        query = Post.query.filter_by(is_published=True)
        
        # Filter by category
        if category:
            query = query.filter_by(category=category)
        
        # Order by publication date
        posts = query.order_by(Post.published_at.desc()).paginate(
            page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False
        )
        
        # Get featured posts (most viewed in last 7 days)
        featured_query = Post.query.filter_by(is_published=True).filter(
            Post.published_at >= datetime.utcnow().date().replace(day=datetime.utcnow().day-7)
        ).order_by(Post.views.desc()).limit(3)
        
        featured_posts = featured_query.all()
        
        return render_template('index.html', posts=posts, featured_posts=featured_posts, category=category)
    
    @app.route('/post/<slug>')
    def view_post(slug):
        """Individual blog post"""
        post = Post.query.filter_by(slug=slug, is_published=True).first_or_404()
        
        # Increment view count
        post.increment_views()
        
        # Get comments
        comments = Comment.query.filter_by(
            post_id=post.id, 
            parent_id=None,
            is_approved=True
        ).order_by(Comment.created_at.desc()).all()
        
        # Check if current user liked this post
        user_liked = False
        if current_user.is_authenticated:
            user_liked = Like.query.filter_by(
                user_id=current_user.id, 
                post_id=post.id
            ).first() is not None
        
        # Get similar posts
        similar_posts = Post.query.filter(
            Post.category == post.category,
            Post.id != post.id,
            Post.is_published == True
        ).order_by(Post.views.desc()).limit(3).all()
        
        form = CommentForm()
        return render_template('post.html', 
                             post=post, 
                             comments=comments, 
                             form=form,
                             user_liked=user_liked,
                             similar_posts=similar_posts)
    
    @app.route('/search')
    def search():
        """Search blog posts"""
        query = request.args.get('q', '')
        page = request.args.get('page', 1, type=int)
        
        if query:
            posts = Post.query.filter(
                Post.is_published == True,
                (Post.title.ilike(f'%{query}%') | 
                 Post.content.ilike(f'%{query}%') |
                 Post.tags.ilike(f'%{query}%'))
            ).order_by(Post.published_at.desc()).paginate(
                page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False
            )
        else:
            posts = []
        
        return render_template('search.html', posts=posts, query=query)
    
    # Authentication routes
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            
            if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
                if user.is_active:
                    login_user(user, remember=form.remember.data)
                    next_page = request.args.get('next')
                    flash('Login successful!', 'success')
                    return redirect(next_page or url_for('dashboard'))
                else:
                    flash('Account is disabled. Contact admin.', 'danger')
            else:
                flash('Login unsuccessful. Check email and password.', 'danger')
        
        return render_template('login.html', form=form)
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = RegistrationForm()
        if form.validate_on_submit():
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            
            user = User(
                username=form.username.data,
                email=form.email.data,
                password_hash=hashed_password
            )
            
            db.session.add(user)
            db.session.commit()
            
            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('login'))
        
        return render_template('register.html', form=form)
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))
    
    # Dashboard routes
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """User dashboard"""
        user_posts = Post.query.filter_by(user_id=current_user.id)\
            .order_by(Post.created_at.desc()).all()
        
        stats = {
            'total_posts': len(user_posts),
            'published_posts': len([p for p in user_posts if p.is_published]),
            'total_views': sum(p.views for p in user_posts),
            'total_likes': sum(len(p.likes) for p in user_posts)
        }
        
        return render_template('dashboard.html', posts=user_posts, stats=stats)
    
    @app.route('/post/new', methods=['GET', 'POST'])
    @login_required
    def create_post():
        """Create new blog post"""
        form = PostForm()
        
        if form.validate_on_submit():
            slug = generate_slug(form.title.data)
            
            # Check if slug already exists
            existing_post = Post.query.filter_by(slug=slug).first()
            if existing_post:
                slug = f"{slug}-{str(uuid.uuid4())[:8]}"
            
            # Save cover image if uploaded
            cover_image = None
            if form.cover_image.data:
                cover_image = save_image(form.cover_image.data)
            
            post = Post(
                title=form.title.data,
                slug=slug,
                content=sanitize_html(form.content.data),
                excerpt=form.excerpt.data,
                category=form.category.data,
                tags=form.tags.data,
                cover_image=cover_image,
                is_published=form.is_published.data,
                user_id=current_user.id
            )
            
            if form.is_published.data:
                post.published_at = datetime.utcnow()
            
            db.session.add(post)
            db.session.commit()
            
            flash('Post created successfully!', 'success')
            return redirect(url_for('dashboard'))
        
        return render_template('create_edit_post.html', form=form, title='Create New Post')
    
    @app.route('/post/<slug>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_post(slug):
        """Edit existing blog post"""
        post = Post.query.filter_by(slug=slug).first_or_404()
        
        # Check ownership
        if post.user_id != current_user.id and not current_user.is_admin():
            abort(403)
        
        form = PostForm(obj=post)
        
        if form.validate_on_submit():
            # Update post
            post.title = form.title.data
            post.content = sanitize_html(form.content.data)
            post.excerpt = form.excerpt.data
            post.category = form.category.data
            post.tags = form.tags.data
            post.is_published = form.is_published.data
            post.updated_at = datetime.utcnow()
            
            # Update slug if title changed
            new_slug = generate_slug(form.title.data)
            if new_slug != post.slug:
                existing_post = Post.query.filter_by(slug=new_slug).first()
                if not existing_post:
                    post.slug = new_slug
            
            # Update cover image if new one uploaded
            if form.cover_image.data:
                post.cover_image = save_image(form.cover_image.data)
            
            # Update publication date if just published
            if form.is_published.data and not post.published_at:
                post.published_at = datetime.utcnow()
            
            db.session.commit()
            flash('Post updated successfully!', 'success')
            return redirect(url_for('view_post', slug=post.slug))
        
        return render_template('create_edit_post.html', form=form, post=post, title='Edit Post')
    
    @app.route('/post/<slug>/delete', methods=['POST'])
    @login_required
    def delete_post(slug):
        """Delete blog post"""
        post = Post.query.filter_by(slug=slug).first_or_404()
        
        # Check ownership or admin
        if post.user_id != current_user.id and not current_user.is_admin():
            abort(403)
        
        db.session.delete(post)
        db.session.commit()
        
        flash('Post deleted successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    # Comment routes
    @app.route('/post/<slug>/comment', methods=['POST'])
    @login_required
    def add_comment(slug):
        """Add comment to post"""
        post = Post.query.filter_by(slug=slug, is_published=True).first_or_404()
        
        form = CommentForm()
        if form.validate_on_submit():
            comment = Comment(
                content=form.content.data,
                user_id=current_user.id,
                post_id=post.id,
                parent_id=form.parent_id.data if form.parent_id.data else None
            )
            
            # Auto-approve for admin, others need approval
            if not current_user.is_admin():
                comment.is_approved = False
                flash('Your comment will be visible after approval.', 'info')
            else:
                flash('Comment added successfully!', 'success')
            
            db.session.add(comment)
            db.session.commit()
        
        return redirect(url_for('view_post', slug=slug) + '#comments')
    
    @app.route('/comment/<comment_id>/delete', methods=['POST'])
    @login_required
    def delete_comment(comment_id):
        """Delete comment"""
        comment = Comment.query.get_or_404(comment_id)
        
        # Check ownership or admin
        if comment.user_id != current_user.id and not current_user.is_admin():
            abort(403)
        
        db.session.delete(comment)
        db.session.commit()
        
        flash('Comment deleted successfully!', 'success')
        return redirect(url_for('view_post', slug=comment.post.slug))
    
    # Like routes
    @app.route('/post/<slug>/like', methods=['POST'])
    @login_required
    def toggle_like(slug):
        """Toggle like on post"""
        post = Post.query.filter_by(slug=slug, is_published=True).first_or_404()
        
        existing_like = Like.query.filter_by(
            user_id=current_user.id,
            post_id=post.id
        ).first()
        
        if existing_like:
            # Unlike
            db.session.delete(existing_like)
            liked = False
        else:
            # Like
            like = Like(user_id=current_user.id, post_id=post.id)
            db.session.add(like)
            liked = True
        
        db.session.commit()
        
        return jsonify({
            'liked': liked,
            'like_count': len(post.likes)
        })
    
    # Profile routes
    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        """User profile"""
        form = ProfileForm(obj=current_user)
        
        if form.validate_on_submit():
            current_user.username = form.username.data
            current_user.bio = form.bio.data
            
            # Update profile image if new one uploaded
            if form.profile_image.data:
                current_user.profile_image = save_image(form.profile_image.data)
            
            # Update password if provided
            if form.password.data:
                current_user.password_hash = bcrypt.generate_password_hash(
                    form.password.data
                ).decode('utf-8')
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        
        return render_template('profile.html', form=form)
    
    # Admin routes
    @app.route('/admin')
    @login_required
    def admin_dashboard():
        """Admin dashboard"""
        if not current_user.is_admin():
            abort(403)
        
        stats = {
            'total_users': User.query.count(),
            'total_posts': Post.query.count(),
            'total_comments': Comment.query.count(),
            'pending_comments': Comment.query.filter_by(is_approved=False).count()
        }
        
        # Recent activity
        recent_posts = Post.query.order_by(Post.created_at.desc()).limit(10).all()
        recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
        
        return render_template('admin.html', 
                             stats=stats,
                             recent_posts=recent_posts,
                             recent_users=recent_users)
    
    @app.route('/admin/comments')
    @login_required
    def admin_comments():
        """Manage comments (admin only)"""
        if not current_user.is_admin():
            abort(403)
        
        pending_comments = Comment.query.filter_by(is_approved=False).all()
        all_comments = Comment.query.order_by(Comment.created_at.desc()).all()
        
        return render_template('admin_comments.html',
                             pending_comments=pending_comments,
                             all_comments=all_comments)
    
    @app.route('/admin/comment/<comment_id>/approve', methods=['POST'])
    @login_required
    def approve_comment(comment_id):
        """Approve comment (admin only)"""
        if not current_user.is_admin():
            abort(403)
        
        comment = Comment.query.get_or_404(comment_id)
        comment.is_approved = True
        db.session.commit()
        
        flash('Comment approved!', 'success')
        return redirect(request.referrer or url_for('admin_comments'))
    
    @app.route('/admin/users')
    @login_required
    def admin_users():
        """Manage users (admin only)"""
        if not current_user.is_admin():
            abort(403)
        
        users = User.query.order_by(User.created_at.desc()).all()
        return render_template('admin_users.html', users=users)
    
    @app.route('/admin/user/<user_id>/toggle', methods=['POST'])
    @login_required
    def toggle_user_status(user_id):
        """Toggle user active status (admin only)"""
        if not current_user.is_admin():
            abort(403)
        
        user = User.query.get_or_404(user_id)
        user.is_active = not user.is_active
        db.session.commit()
        
        status = "activated" if user.is_active else "deactivated"
        flash(f'User {status} successfully!', 'success')
        return redirect(request.referrer or url_for('admin_users'))
    
    # API endpoints for analytics
    @app.route('/api/analytics')
    @login_required
    def get_analytics():
        """Get analytics data"""
        if not current_user.is_admin():
            abort(403)
        
        # Daily post counts for last 30 days
        import datetime
        thirty_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=30)
        
        daily_posts = db.session.query(
            db.func.date(Post.created_at).label('date'),
            db.func.count(Post.id).label('count')
        ).filter(
            Post.created_at >= thirty_days_ago
        ).group_by(
            db.func.date(Post.created_at)
        ).all()
        
        # Top categories
        top_categories = db.session.query(
            Post.category,
            db.func.count(Post.id).label('count')
        ).filter(
            Post.is_published == True
        ).group_by(
            Post.category
        ).order_by(
            db.desc('count')
        ).limit(5).all()
        
        return jsonify({
            'daily_posts': [{'date': str(d[0]), 'count': d[1]} for d in daily_posts],
            'top_categories': [{'category': c[0], 'count': c[1]} for c in top_categories]
        })
    
    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create admin user if doesn't exist
        admin = User.query.filter_by(email='admin@blog.com').first()
        if not admin:
            hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin = User(
                username='admin',
                email='admin@blog.com',
                password_hash=hashed_password,
                role='admin',
                bio='System Administrator'
            )
            db.session.add(admin)
            db.session.commit()
    
    app.run(debug=True)