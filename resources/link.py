import requests
import os
import uuid
from flask import request, current_app
from flask_restful import Resource
from http import HTTPStatus
from marshmallow import ValidationError
from zipfile import ZipFile
from io import BytesIO
from requests.exceptions import ConnectionError
from werkzeug.utils import secure_filename

from schemas.link import LinkSchema, LinkPaginationSchema
from models.link import Link
from utils import link_to_data, csvfile_processing, allowed_image, compress_image




link_schema = LinkSchema()
link_pagination_schema = LinkPaginationSchema()


class LinkListResource(Resource):
    def get(self):
        args = request.args.to_dict()
        
        per_page = int(args.get('per_page') or 20)
        page = int(args.get('page') or 1)
        q = args.get('q') or ''
        sort = args.get('sort') or 'id'
        order = args.get('order') or 'desc'
        
        if sort not in ['id', 'uuid', 'domain_zone', 'status']:
            sort = 'id'
            
        if order not in ['asc', 'desc']:
            order = 'desc'
        
        paginated_links = Link.get_all_published(q, page, per_page, sort, order)
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
        current_app.logger.info(f'add link to db: {link.url}')
        
        return link_schema.dump(link), HTTPStatus.CREATED


class LinkResource(Resource):
    pass


class LinkImageUploadResource(Resource):
    def put(self, link_uuid):
        file = request.files.get('image')
        if not file:
            return {"message": "Файл не найден"}, HTTPStatus.BAD_REQUEST
        if not allowed_image(file.filename):
            return {"message": "Некорректный тип файла."}, HTTPStatus.BAD_REQUEST 
        
        folder = current_app.config["UPLOADED_IMAGES_DEST"] + '/links'
        link: Link = Link.get_by_uuid(_uuid=link_uuid)
        
        if link is None:
            return {"message": "Link is not found"}, HTTPStatus.BAD_REQUEST
        
        if link.cover_image:
            cover_path = os.path.join(folder, link.cover_image)
            if os.path.exists(cover_path):
                os.remove(cover_path)
        
        extension = secure_filename(file.filename).rsplit('.', 1)[1]
        filename = f"{uuid.uuid4()}.{extension}"
    
        file.save(os.path.join(folder, filename))
        filename = compress_image(filename, folder)
        
        link.cover_image = filename
        link.save() 
        current_app.logger.info(f'add image to url: {link.url}')
        
        return LinkSchema(only=("image_url",)).dump(link), HTTPStatus.OK


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