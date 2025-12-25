# PostPilot

PostPilot is a modern, full-featured blogging platform built with Flask. It allows users to create, edit, and share blog posts, comment, like, and manage their profiles. The project is designed for writers, thinkers, and readers who want a beautiful, easy-to-use platform for sharing ideas.

## Features
- User registration and authentication (login/logout)
- Create, edit, and delete blog posts with rich content
- Categories, tags, and featured posts
- Commenting system with replies
- Like system for posts
- User dashboard with stats
- Profile management (bio, avatar)
- Responsive, modern UI
- Admin features (user roles, post moderation)

## Tech Stack
- Python 3
- Flask (with Flask-Login, Flask-WTF, Flask-Bcrypt, Flask-SQLAlchemy)
- SQLite (default, can be changed)
- HTML/CSS (Jinja2 templates, custom styles)
- JavaScript (for interactivity)

## Setup & Installation
1. **Clone the repository:**
   ```sh
   git clone <repo-url>
   cd PostPilot
   ```
2. **Create a virtual environment (optional but recommended):**
   ```sh
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Set environment variables (optional):**
   - You can create a `.env` file for custom config (see `config.py`).
5. **Initialize the database:**
   ```sh
   python
   >>> from app import create_app
   >>> app = create_app()
   >>> from database import db
   >>> with app.app_context():
   ...     db.create_all()
   ...
   exit()
   ```
6. **Run the app:**
   ```sh
   python app.py
   ```
7. **Open your browser:**
   Visit [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Usage
- Register a new account or log in.
- Create, edit, and manage your posts from the dashboard.
- Browse, comment, and like posts.
- Admin users can moderate content and manage users.

## Folder Structure
- `app.py` - Main application entry point
- `database.py` - Database models
- `forms.py` - WTForms classes
- `templates/` - Jinja2 HTML templates
- `static/` - CSS, JS, images
- `utils/` - Helper functions

## License
MIT License

---
*Generated on December 25, 2025*
