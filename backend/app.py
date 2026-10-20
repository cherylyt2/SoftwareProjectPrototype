"""Flask application entry point and factory for Vercel."""

import os
import secrets

import click
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from werkzeug.security import generate_password_hash

from database import db, migrate
from models import User


def create_app(test_config: dict | None = None) -> Flask:
    """Create and configure the Flask API application."""
    load_dotenv()
    app = Flask(__name__)
    is_production = os.getenv("VERCEL_ENV") == "production" or os.getenv("FLASK_ENV") == "production"
    prototype_mode_env = os.getenv("PROTOTYPE_MODE")
    prototype_mode = (
        prototype_mode_env.strip().lower() in {"1", "true", "yes", "on"}
        if prototype_mode_env is not None
        else not is_production
    )
    database_url = os.getenv("DATABASE_URL")
    secret_key = os.getenv("SECRET_KEY")

    if is_production and (not database_url or not secret_key):
        raise RuntimeError("DATABASE_URL and SECRET_KEY must be configured in production.")

    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url and database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    app.config.from_mapping(
        SECRET_KEY=secret_key or secrets.token_urlsafe(32),
        SQLALCHEMY_DATABASE_URI=database_url or "sqlite:///learning-platform-dev.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=is_production,
        PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 7,
        MAX_CONTENT_LENGTH=4 * 1024 * 1024,
        ENVIRONMENT="production" if is_production else "development",
        PROTOTYPE_MODE=prototype_mode,
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    migrate.init_app(app, db)

    from auth_routes import auth_bp, users_bp
    from course_routes import courses_bp
    from ai_routes import ai_bp
    from learning_path_routes import learning_paths_bp
    from stage_routes import stages_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(learning_paths_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(stages_bp)

    @app.get("/api/health")
    def health_check():
        """Return a lightweight status for deployment checks."""
        return jsonify(status="ok", service="learning-platform-api")

    @app.errorhandler(404)
    def api_not_found(error):
        """Return JSON for unknown API routes while leaving other routes unchanged."""
        if request.path.startswith("/api/"):
            return jsonify(error="Not found."), 404
        return error

    @app.cli.command("seed-dev-admin")
    def seed_dev_admin():
        """Create the documented admin account only in development."""
        if app.config["ENVIRONMENT"] != "development":
            raise click.ClickException("The default admin seed is disabled outside development.")
        if db.session.execute(db.select(User).filter_by(username="admin")).scalar_one_or_none():
            click.echo("Development admin already exists.")
            return
        db.session.add(User(
            username="admin",
            display_name="Administrator",
            role="admin",
            password_hash=generate_password_hash("password"),
            must_change_password=True,
        ))
        db.session.commit()
        click.echo("Created the development admin. Change its password after sign-in.")

    @app.cli.command("bootstrap-admin")
    def bootstrap_admin():
        """Create the first administrator from private one-time environment values."""
        username = os.getenv("INITIAL_ADMIN_USERNAME", "").strip().lower()
        password = os.getenv("INITIAL_ADMIN_PASSWORD", "")
        if not username or len(password) < 12:
            raise click.ClickException("Set INITIAL_ADMIN_USERNAME and a 12-character INITIAL_ADMIN_PASSWORD.")
        existing_admin = db.session.execute(db.select(User).filter_by(role="admin")).first()
        if existing_admin:
            raise click.ClickException("An administrator already exists; bootstrap is only for initial setup.")
        db.session.add(User(
            username=username,
            display_name="Administrator",
            role="admin",
            password_hash=generate_password_hash(password),
            must_change_password=True,
        ))
        db.session.commit()
        click.echo("Created the initial administrator. Change the password after sign-in.")

    return app


app = create_app()