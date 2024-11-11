# run.py

from app import create_app
import os
import logging

app = create_app()

if __name__ == '__main__':
    # Determine debug mode based on environment
    debug_mode = app.config.get('DEBUG', False)
    
    # Run the Flask development server only if in development
    if app.config['ENV'] == 'development':
        app.run(host="0.0.0.0", port=8080, debug=debug_mode)
    else:
        app.logger.error("Use a production-ready server for deployment.")
