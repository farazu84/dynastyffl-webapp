import os
from app import create_app
from config import ProdConfig, DevConfig

# Determine which config to use based on environment
if os.environ.get('FLASK_ENV') == 'production':
    application = create_app(ProdConfig)
else:
    application = create_app(DevConfig)

if __name__ == '__main__':
    application.run()
