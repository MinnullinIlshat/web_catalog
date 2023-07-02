import os
import uuid
import aiohttp
import asyncio

from PIL import Image
from flask import current_app
from passlib.hash import pbkdf2_sha256 
from urllib.parse import urlsplit
from concurrent.futures import ProcessPoolExecutor
from aiohttp.client_exceptions import ClientConnectionError, ServerTimeoutError
from asyncio import TimeoutError
from marshmallow import ValidationError

from models.link import Link
from schemas.link import LinkSchema




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
        try:
            k, v = item.split('=')
            p_dict[k] = v
        except ValueError:
            p_dict[item] = ''
    return p_dict

def link_to_data(link: str) -> dict:
    '''возвращает словарь с атрибутами
    protocol, domain, domain_zone, path, params'''
    u_p = urlsplit(link)
    
    if not u_p.netloc or not u_p.scheme:
        return "incorrect url"
    
    _uuid = uuid.uuid3(uuid.NAMESPACE_DNS, link)

    if Link.get_by_uuid(_uuid):
        return "already exists"
    
    if params:= (u_p.query or {}):
        params = params_to_dict(params)
        
    return {
        'url': link,
        'protocol': u_p.scheme,
        'domain': u_p.netloc,
        'domain_zone': u_p.netloc.rsplit('.', 1)[-1],
        'path': u_p.path,
        'params': params,
        'uuid': _uuid,
    }

def save_news(s: str) -> None: 
    with open('news.txt', 'a') as file:
        file.write(s)

async def get_status(result: dict, 
                     session: aiohttp.ClientSession) -> dict:
    '''добавляет status "доступен/недоступен" и status_code
    к словарю с данными по url'''
    try:
        url = result['url']
        response = await session.get(url)
        current_app.logger.info(f'link status update: {url}')
    except (TimeoutError, ServerTimeoutError): 
        result['status_code'] = 999 
        result['status'] = "недоступен"
        save_news(f'Изменился статус для сайта {url}: 999')
        return result
    except ClientConnectionError as err:
        return "url not exists"
    else: 
        result['status_code'] = response.status
        result['status'] = "доступен" if result['status_code'] < 400 else "недоступен"
        save_news(f'Изменился статус для сайта {url}: {response.status}')
        return result

def csvfile_processing(csv_file) -> tuple:
    '''обрабатывает ссылки из csv файла.
    возвращает кортеж из трех значений int, int, int:
    1) общ. кол-во ссылок 2) ссылок с ошибками 3) ссылок сохр. в бд.'''
    
    errors = 0
    urls = [line.decode('utf-8').strip() for line in csv_file]
    
    with ProcessPoolExecutor() as process_pool:
        results = list(process_pool.map(link_to_data, urls))
    
    async def main():
        nonlocal errors, results
        timeout = aiohttp.ClientTimeout(1, .3)
        
        tasks = []
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for result in results:
                if result in ["incorrect url", "already exists"]:
                    errors += 1
                else:
                    task = asyncio.create_task(get_status(result, session))
                    tasks.append(task)

            for res in await asyncio.gather(*tasks):
                if res == "url not exists":
                    errors += 1
                else:
                    try:
                        data = LinkSchema().load(data=res)
                    except ValidationError as err:
                        errors += 1
                    else: 
                        link = Link(**data)
                        link.save() 
        
    asyncio.run(main())
    
    return len(urls), errors, len(urls) - errors