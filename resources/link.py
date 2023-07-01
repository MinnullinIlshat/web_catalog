import requests
from flask import request
from flask_restful import Resource
from http import HTTPStatus
from marshmallow import ValidationError
from zipfile import ZipFile
from io import BytesIO
from requests.exceptions import ConnectionError

from schemas.link import LinkSchema, LinkPaginationSchema
from models.link import Link
from utils import link_to_data, csvfile_processing




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
        url = request.get_json()['link']
        
        if not isinstance(url, str) or not url.startswith('http'):
            return {"message": "ссылка должна быть строкой и начинаться с http/https"}, HTTPStatus.BAD_REQUEST
        
        link_data = link_to_data(url)
        
        if link_data == "already exists": 
            return {"message": "Ссылка уже существует в базе данных"}, HTTPStatus.BAD_REQUEST
        if link_data == "incorrecr url":
            return {"message": "Некорректный формат ссылки"}, HTTPStatus.BAD_REQUEST

        # сделать запрос к url и добавить поля status и status_code
        try:
            status_code = requests.get(url).status_code
            link_data["status_code"] = status_code
            link_data["status"] = "недоступен" if status_code > 399 else "доступен"
        except ConnectionError as err:
            return {"message": "такой страницы не существует"}, HTTPStatus.BAD_REQUEST
        
        # валидация данных
        try:
            data = link_schema.load(data=link_data)
        except ValidationError as err:
            return {"message": "Validation errors", 'errors': err.messages}, HTTPStatus.BAD_REQUEST
        
        # создаем экземпляр Link и сохраняем в базе данных
        link = Link(**data)
        link.save()
        
        return link_schema.dump(link), HTTPStatus.CREATED


class LinkResource(Resource):
    pass


class LinkImageUploadResource(Resource):
    pass


class LinkCsvUploadResource(Resource):
    def post(self):
        file = request.files.get('csv')
        
        if file.filename.rsplit('.', 1)[-1] != 'zip':
            return {"message": "Файл должен иметь расширение'.zip'"}, HTTPStatus.BAD_REQUEST
        
        file_io = BytesIO()
        file.save(file_io)
        
        with ZipFile(file_io) as zip_file: 
            # в архиве должен быть только один файл
            if len(zip_file.infolist()) != 1: 
                return {"message": "В zip архиве должен быть только один файл формата csv"}, HTTPStatus.BAD_REQUEST
            
            csv_filename = zip_file.infolist()[0].filename
            if csv_filename.rsplit('.', 1)[-1] != 'csv':
                return {"message": "Архив должен содержать один csv файл"}, HTTPStatus.BAD_REQUEST
            
            with zip_file.open(csv_filename) as csv_file:
                links_count, errors, links_to_save = csvfile_processing(csv_file)
                
            return {
                "обработано ссылок": links_count,
                "количество ошибок": errors,
                "количество сохраненных": links_to_save,
            }, HTTPStatus.CREATED