import os
import re
from werkzeug.utils import secure_filename

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def secure_filename_safe(filename):
    # werkzeug.secure_filename but also fallback for no extension
    filename = secure_filename(filename)
    if not filename:
        filename = "upload"
    # truncate to avoid very long names
    return filename[:120]
