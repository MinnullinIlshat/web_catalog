import os
import uuid
import requests

from PIL import Image
from passlib.hash import pbkdf2_sha256 
from urllib.parse import urlsplit

from models.link import Link




def hash_password(password):
    return pbkdf2_sha256.hash(password)

def check_password(password, hashed):
    return pbkdf2_sha256.verify(password, hashed)

def allowed_image(filename):
    allowed_extensions = ['png', 'jpg', 'jpeg', 'gif']
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in allowed_extensions
        
def compress_image(filename, folder):
    file_path = os.path.join(folder, filename)
    image = Image.open(file_path)
    if image.mode != "RGB":
        image = image.convert("RGB")
    if max(image.width, image.height) > 1600:
        maxsize = (1600, 1600)
        image.thumbnail(maxsize, Image.ANTIALIAS)   
    compressed_filename = f"{uuid.uuid4()}.jpg"
    compressed_file_path = os.path.join(folder, compressed_filename)
    image.save(compressed_file_path, optimize=True, quality=85)
    
    original_size = os.stat(file_path).st_size 
    compressed_size = os.stat(compressed_file_path).st_size 
    percentage = round((original_size - compressed_size) /\
        original_size * 100)
    
    print(f"The file size is reduced by {percentage}%, from \
        {original_size} to {compressed_size}")
    
    os.remove(file_path)
    return compressed_filename

def params_to_dict(params: str) -> dict:
    '''создает словарь из параметров ссылки'''
    p_dict = dict()
    for item in params.split('&'):
        k, v = item.split('=')
        p_dict[k] = v
    return p_dict

def link_to_data(link: str) -> dict:
    '''возвращает словарь с атрибутами
    protocol, domain, domain_zone, path, params'''
    u_p = urlsplit(link)
    
    if not u_p.netloc:
        raise TypeError("некорректная ссылка")
    
    _uuid = uuid.uuid3(uuid.NAMESPACE_DNS, link)

    if Link.get_by_uuid(_uuid):
        return "already exists"
    
    if params:= (u_p.query or {}):
        params = params_to_dict(params)
        
    try:
        status_code = requests.get(link).status_code
    except Exception:
        status_code = None
        
    if not status_code or status_code > 399:
        status = "недоступен"
    else: 
        status = "доступен"
        
    return {
        'protocol': u_p.scheme,
        'domain': u_p.netloc,
        'domain_zone': u_p.netloc.rsplit('.', 1)[-1],
        'path': u_p.path,
        'params': params,
        'status': status,
        'status_code': status_code,
        'uuid': _uuid,
    }