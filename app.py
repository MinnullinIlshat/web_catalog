from flask import Flask, request
from flask_restful import Api
from flask_migrate import Migrate

from config import Config
from extensions import db, jwt
from resources.user import UserListResource
from resources.link import LinkListResource, LinkResource, LinkImageUploadResource, LinkCsvUploadResource
from resources.token_res import TokenResource, RefreshResource, RevokeResource, jwt_redis_blocklist




def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    register_extensions(app)
    register_resources(app)

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
    
    # @app.before_request
    # def before_request():
    #     print('\n' + "BEFORE REQUEST".center(30, '=') + '\n')
    #     print(request)
    #     print('\n' + "".center(30, '=') + '\n')
        
    # @app.after_request 
    # def after_request(response):
    #     print('\n' + 'AFTER REQUEST'.center(30, '=') + '\n')
    #     print(response)
    #     print('\n', "".center(30, '=') + '\n')
    #     return response 

def register_resources(app):
    api = Api(app)

    api.add_resource(UserListResource, '/users')

    api.add_resource(TokenResource, '/token')
    api.add_resource(RefreshResource, '/refresh')
    api.add_resource(RevokeResource, '/revoke')

    api.add_resource(LinkListResource, '/links')
    api.add_resource(LinkResource, '/links/<string:link_uuid>')
    api.add_resource(LinkImageUploadResource, '/links/<string:link_uuid>/image')
    api.add_resource(LinkCsvUploadResource, '/links/csv')

if __name__ == '__main__':
    app = create_app()
    app.run()