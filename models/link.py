from extensions import db 
from sqlalchemy import desc
from sqlalchemy_utils import UUIDType



class Link(db.Model):
    __tablename__ = 'link'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUIDType(binary=False), index=True)
    protocol = db.Column(db.String)
    domain = db.Column(db.String)
    domain_zone = db.Column(db.String)
    path = db.Column(db.String)
    params = db.Column(db.PickleType)
    status_code = db.Column(db.Integer)
    status = db.Column(db.String)
    cover_image = db.Column(db.String, default=None)
    
    @classmethod
    def get_all_published(cls, q, page, per_page):
        
        keyword = f'%{q}%'
        
        return cls.query.filter(cls.domain_zone.ilike(keyword)).\
            order_by(desc(cls.domain)).\
                paginate(page=page, per_page=per_page)
                
    @classmethod
    def get_by_uuid(cls, _uuid):
        return cls.query.filter_by(uuid=_uuid).first()
    
    def save(self):
        db.session.add(self)
        db.session.commit()
        
    def delete(self):
        db.session.delete(self)
        db.session.commit()