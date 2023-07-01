from flask import request, current_app
from flask_restful import Resource 
from marshmallow import ValidationError
from http import HTTPStatus 

from models.user import User

from schemas.user import UserSchema 




user_schema = UserSchema()


class UserListResource(Resource):
    def post(self):
        json_data = request.get_json()

        try:
            data = user_schema.load(data=json_data)
        except ValidationError as err:
            return {"messages": "Validation errors", "errors": err.messages}, HTTPStatus.BAD_REQUEST

        if User.get_by_username(data.get('username')):
            return {"message": "username already used"}, HTTPStatus.BAD_REQUEST
        
        if User.get_by_email(data.get('email')):
            return {"message": "email already used"}, HTTPStatus.BAD_REQUEST
        
        user = User(**data)

        user.save()
        current_app.logger.info(f'register new user: {user.username}')

        return user_schema.dump(user), HTTPStatus.CREATED