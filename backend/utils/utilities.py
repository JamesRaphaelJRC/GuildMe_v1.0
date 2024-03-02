#!/usr/bin/env python3
''' Utilities module '''
from PIL import Image
import os
import shutil

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

    def copy_and_rename_file(self, original_path, new_name):
        try:
            # Copy the file to the new name
            shutil.copy(original_path, new_name)
            print(f"File copied successfully as {new_name}")
            return True
        except FileNotFoundError:
            print(f"Error: File not found at {original_path}")
        except shutil.SameFileError:
            print("Error: The source and destination files are the same.")
        except PermissionError:
            print("Error: Permission error. Make sure you have the necessary permissions.")
        except Exception as e:
            print(f"Error: {e}")
        return False
