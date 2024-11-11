# app/utils/image_processing.py

import imghdr

def allowed_file(filename):
    """
    Checks if the file has an allowed extension.

    Args:
        filename (str): Name of the file.

    Returns:
        bool: True if allowed, False otherwise.
    """
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def is_image_file(file_stream):
    """
    Validates the MIME type of the file to ensure it's an image.

    Args:
        file_stream (io.BytesIO): File stream.

    Returns:
        bool: True if valid image, False otherwise.
    """
    file_stream.seek(0)
    header = file_stream.read(512)  # Read the first 512 bytes to determine file type
    file_stream.seek(0)  # Reset stream position
    file_type = imghdr.what(None, header)
    return file_type in {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
