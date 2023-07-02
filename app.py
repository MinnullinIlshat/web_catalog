import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request
from flask_restful import Api
from flask_migrate import Migrate

from config import Config
from extensions import db, jwt
from wi import get_logs, table, index, upload, file_upload
from resources.user import UserListResource
from resources.link import LinkListResource, LinkResource, LinkImageUploadResource, LinkCsvUploadResource
from resources.token_res import TokenResource, RefreshResource, RevokeResource, jwt_redis_blocklist



def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    register_extensions(app)
    register_resources(app)
    
    logging.basicConfig(filename='logfile.log', level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s")

    handler = RotatingFileHandler("logfile.log", maxBytes=1024*1024, backupCount=3)
    handler.setLevel(logging.INFO)
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(handler)

    return app 

def register_extensions(app):
    db.init_app(app)
    migrate = Migrate(app, db)
    jwt.init_app(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_is_revoked(jwt_header, jwt_payload: dict):
        jti = jwt_payload['jti']
        token_in_redis = jwt_redis_blocklist.get(jti)
        return token_in_redis is not None
    
    @app.before_request
    def before_request():
        app.logger.info(request)
        
    @app.after_request 
    def after_request(response):
        app.logger.info(response)
        return response 

def register_resources(app: Flask):
    api = Api(app)

    api.add_resource(UserListResource, '/users')

    api.add_resource(TokenResource, '/token')
    api.add_resource(RefreshResource, '/refresh')
    api.add_resource(RevokeResource, '/revoke')

    api.add_resource(LinkListResource, '/links')
    api.add_resource(LinkResource, '/links/<string:link_uuid>')
    api.add_resource(LinkImageUploadResource, '/links/<string:link_uuid>/image')
    api.add_resource(LinkCsvUploadResource, '/links/csv')
    
    app.add_url_rule('/logs', view_func=get_logs)
    app.add_url_rule('/', view_func=index)
    app.add_url_rule('/table/<string:sort>/<string:order>/<int:page>', view_func=table)
    app.add_url_rule('/upload', view_func=upload, methods=['GET', 'POST'])
    app.add_url_rule('/file_upload', view_func=file_upload, methods=['POST'])
    
if __name__ == '__main__':
    app = create_app()
    app.run()