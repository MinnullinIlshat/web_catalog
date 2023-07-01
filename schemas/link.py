from flask import url_for 
from marshmallow import Schema, fields, validate

from schemas.pagination import PaginationSchema 




class LinkSchema(Schema):
    class Meta: 
        ordered = True 

    id = fields.Integer(dump_only=True)
    uuid = fields.UUID()
    url = fields.String(load_only=True)
    protocol = fields.String()
    domain = fields.String()
    domain_zone = fields.String()
    path = fields.String()
    status_code = fields.Integer()
    status = fields.String(validate=validate.OneOf(["доступен", "недоступен"]))   

    params = fields.Dict()
    image_url = fields.Method(serialize='image_url_dump')
    
    def image_url_dump(self, link):
        if link.cover_image:
            return url_for('static', filename=f"images/links/{link.cover_image}", _external=True)
        else: 
            return url_for('static', filename="images/assets/default_link_image.jpg", _external=True)
        
        
class LinkPaginationSchema(PaginationSchema):
    data = fields.Nested(LinkSchema, attribute='items', many=True)