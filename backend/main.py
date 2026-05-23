#!/usr/bin/env python3
import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from routes import api_bp

# 1. Setup Structured Logging (JSON-like format is best for production tools)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('app')

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 2. Proper CORS setup
    # This automatically handles OPTIONS requests and headers
    CORS(app, resources={r"/*": {"origins": Config.CORS_ORIGINS}})

    # 3. Register Blueprints
    app.register_blueprint(api_bp)

    # 4. Global Error Handlers
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({'error': f'File too large. Limit is {Config.MAX_CONTENT_LENGTH // 1024 // 1024}MB'}), 413

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500

    return app

if __name__ == "__main__":
    app = create_app()

    # Environment Check
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    port = int(os.getenv('PORT', 5000))

    logger.info(f"🚀 Server running on port {port} (Debug: {debug_mode})")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)