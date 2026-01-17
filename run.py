#!/usr/bin/env python
"""
StructSim AI Platform - Backend Server Entry Point

Usage:
    python run.py                    # Run in development mode
    python run.py --env production   # Run in production mode
    python run.py --seed             # Seed the database with initial data
"""
import os
import argparse
from app import create_app, db


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='StructSim Backend Server')
    parser.add_argument(
        '--env', 
        type=str, 
        default='development',
        choices=['development', 'production', 'testing'],
        help='Environment to run the server in'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Host to bind the server to'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to bind the server to'
    )
    parser.add_argument(
        '--seed',
        action='store_true',
        help='Seed the database with initial data'
    )
    parser.add_argument(
        '--init-db',
        action='store_true',
        help='Initialize the database (create tables)'
    )
    return parser.parse_args()


def init_database(app):
    """Initialize the database."""
    with app.app_context():
        db.create_all()
        print("Database tables created successfully.")


def seed_database():
    """Seed the database with initial data."""
    from seed import seed_database as run_seed
    run_seed()
    print("Database seeded successfully.")


def main():
    """Main entry point."""
    args = parse_args()
    
    # Set environment
    os.environ['FLASK_ENV'] = args.env
    
    # Create application
    app = create_app(args.env)
    
    # Initialize database if requested
    if args.init_db:
        init_database(app)
        return
    
    # Seed database if requested
    if args.seed:
        seed_database()
        return
    
    # Run the server
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║           StructSim AI Platform - Backend Server             ║
╠══════════════════════════════════════════════════════════════╣
║  Environment: {args.env:<45} ║
║  Server URL:  http://{args.host}:{args.port:<35} ║
║  API Base:    http://{args.host}:{args.port}/api{' '*27} ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    app.run(
        host=args.host,
        port=args.port,
        debug=(args.env == 'development')
    )


if __name__ == '__main__':
    main()

