#!/usr/bin/env python3
''' Utilities module '''
from PIL import Image
import os

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


class Utils:
    ''' Defines the various app utilities '''
    def allowed_file(self, filename: str) -> bool:
        ''' verifies if a among the allowed extensions'''
        return '.' in filename and filename.rsplit(
            '.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def get_file_size_mb(self, file_path: str) -> float:
        ''' Gets the file size of a file in mb '''
        return os.path.getsize(file_path) / (1024 * 1024)

    def compress_image(self, input_path: str, output_path: str, quality=70):
        ''' compresses a file and saving to the output path '''
        img = Image.open(input_path)
        img.save(output_path, quality=quality)
