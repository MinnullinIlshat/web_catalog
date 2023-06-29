from flask import request
from flask_restful import Resource
from http import HTTPStatus
from marshmallow import ValidationError

from schemas.link import LinkSchema, LinkPaginationSchema
from models.link import Link
from utils import link_to_data




link_schema = LinkSchema()
link_pagination_schema = LinkPaginationSchema()


class LinkListResource(Resource):
    def get(self):
        args = request.args.to_dict()
        
        per_page = int(args.get('per_page') or 20)
        page = int(args.get('page') or 1)
        q = args.get('q') or ''
        
        paginated_links = Link.get_all_published(q, page, per_page)
        return link_pagination_schema.dump(paginated_links), HTTPStatus.OK
    
    def post(self):
        link = request.get_json()['link']
        
        if not isinstance(link, str):
            return {"message": "link must be a string"}, HTTPStatus.BAD_REQUEST
        
        try: 
            link_data = link_to_data(link)
            if link_data == "already exists": 
                return {"message": "Ссылка уже существует в базе данных"}, HTTPStatus.BAD_REQUEST
        except TypeError as err:
            return {"message": "Incorrect link format", "errors": str(err)}, HTTPStatus.BAD_REQUEST

        try:
            data = link_schema.load(data=link_data)
        except ValidationError as err:
            return {"message": "Validation errors", 'errors': err.messages}, HTTPStatus.BAD_REQUEST
        
        print(data, '\n')
        link = Link(**data)
        link.save()
        print(link.params)
        
        return link_schema.dump(link), HTTPStatus.CREATED


class LinkResource(Resource):
    pass


class LinkImageUploadResource(Resource):
    pass


class LinkCsvUploadResource(Resource):
    pass