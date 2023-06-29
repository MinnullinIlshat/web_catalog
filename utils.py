import os
import uuid

from PIL import Image
from passlib.hash import pbkdf2_sha256 


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