import os
import tempfile
import time
from flask import render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
from app import app
from services.imgfoto_service import ImgfotoService
from services.telegraph_service import TelegraphService

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_files():
    # Ensure we always return JSON responses
    from flask import jsonify
    try:
        # Get form data
        api_key = request.form.get('api_key')
        title = request.form.get('title')
        author = request.form.get('author')
        content = request.form.get('content', '')

        # Validate required fields
        if not api_key or not title or not author:
            return jsonify({
                'success':
                False,
                'error':
                'API key, title, and author are required fields'
            }), 400

        # Get uploaded files
        files = request.files.getlist('photos')
        if not files or all(file.filename == '' for file in files):
            return jsonify({
                'success': False,
                'error': 'No files selected for upload'
            }), 400

        # Limit batch size to prevent overwhelming the API
        valid_files = [f for f in files if f.filename and f.filename != '']
        if len(valid_files) > 50:
            return jsonify({
                'success':
                False,
                'error':
                f'Too many files selected ({len(valid_files)}). Please upload 50 files or fewer at a time to ensure reliability.'
            }), 400

        # Validate file types
        for file in files:
            if file.filename != '' and not allowed_file(file.filename):
                return jsonify({
                    'success':
                    False,
                    'error':
                    f'File type not allowed: {file.filename}. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
                }), 400

        # Initialize services
        imgfoto_service = ImgfotoService(api_key)
        telegraph_service = TelegraphService()

        # Upload photos to imgfoto.host
        uploaded_images = []
        failed_uploads = []

        for i, file in enumerate(files):
            if file.filename and file.filename != '':
                temp_file = None
                try:
                    app.logger.info(
                        f"Uploading file {i+1}/{len(files)}: {file.filename}")

                    # Save file temporarily
                    filename = secure_filename(file.filename)
                    temp_file = tempfile.NamedTemporaryFile(
                        delete=False, suffix=os.path.splitext(filename)[1])
                    file.save(temp_file.name)

                    # Upload to imgfoto.host with retry logic
                    image_url = imgfoto_service.upload_image(temp_file.name)
                    uploaded_images.append(image_url)
                    app.logger.info(f"Successfully uploaded: {file.filename}")

                    # Clean up temp file
                    os.unlink(temp_file.name)
                    temp_file = None

                except Exception as e:
                    error_msg = str(e)
                    app.logger.error(
                        f"Error uploading {file.filename}: {error_msg}")
                    failed_uploads.append(file.filename or "unknown")

                    # Clean up temp file if it exists
                    if temp_file is not None:
                        try:
                            os.unlink(temp_file.name)
                        except:
                            pass

                    # Check if this is a critical error that should stop processing
                    if any(phrase in error_msg.lower() for phrase in
                           ['api key', 'rate limit', 'service maintenance']):
                        app.logger.warning(
                            f"Critical error detected, stopping further uploads: {error_msg}"
                        )
                        break

                    # Continue with other uploads for non-critical errors
                    continue

        # Create Telegraph account and post
        try:
            telegraph_url = telegraph_service.create_post(
                title, author, content, uploaded_images)

            response_data = {
                'success': True,
                'telegraph_url': telegraph_url,
                'uploaded_images': uploaded_images,
                'total_uploaded': len(uploaded_images),
                'total_files': len([f for f in files if f.filename != ''])
            }

            # Include warning about failed uploads if any
            if failed_uploads:
                response_data[
                    'warning'] = f"Some uploads failed: {', '.join(failed_uploads[:3])}"
                if len(failed_uploads) > 3:
                    response_data[
                        'warning'] += f" and {len(failed_uploads) - 3} more."

            return jsonify(response_data)

        except Exception as e:
            app.logger.error(f"Error creating Telegraph post: {str(e)}")
            return jsonify({
                'success':
                False,
                'error':
                f'Failed to create Telegraph post: {str(e)}. However, {len(uploaded_images)} images were uploaded successfully.'
            }), 500

    except Exception as e:
        app.logger.error(f"Unexpected error in upload_files: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'An unexpected error occurred: {str(e)}'
        }), 500


@app.errorhandler(413)
def too_large(e):
    return jsonify({
        'success': False,
        'error': 'File too large. Maximum file size is 50MB.'
    }), 413
