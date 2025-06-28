# Photo to Telegraph Uploader

## Overview

This is a Flask web application that allows users to upload photos to imgfoto.host and create Telegraph posts with those images. The application provides a user-friendly interface for batch photo uploading and automatic Telegraph post generation.

## System Architecture

### Frontend Architecture
- **Framework**: Vanilla JavaScript with Bootstrap 5.3
- **UI Components**: Dark theme interface with drag-and-drop file upload
- **Styling**: Bootstrap CSS with custom CSS for enhanced user experience
- **File Handling**: Client-side file validation and preview functionality

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Structure**: Modular design with separate route handlers and service layers
- **File Handling**: Werkzeug secure filename handling with configurable upload limits
- **Middleware**: ProxyFix for proper header handling in deployment environments

## Key Components

### Core Application (`app.py`)
- Flask application initialization with session management
- File upload configuration (50MB limit)
- Temporary upload directory management
- Debug logging setup

### Route Handlers (`routes.py`)
- Main index route serving the upload interface
- File upload endpoint with validation and processing
- Integration with external services for image hosting and content publishing

### Service Layer
1. **ImgfotoService** (`services/imgfoto_service.py`)
   - Handles image uploads to imgfoto.host API
   - API key authentication
   - Error handling with specific timeout and connection error management
   - Returns direct image URLs for Telegraph integration

2. **TelegraphService** (`services/telegraph_service.py`)
   - Creates Telegraph accounts dynamically
   - Manages Telegraph API interactions
   - Generates unique account identifiers for each session

### Frontend Components
- **Base Template**: Responsive layout with Bootstrap navigation and footer
- **Upload Interface**: File drag-and-drop zone with progress indicators
- **JavaScript**: File handling, form validation, and AJAX submission

## Data Flow

1. User provides imgfoto.host API key and selects image files
2. Client-side validation ensures file types are supported
3. Files are uploaded to Flask backend with form data
4. Images are uploaded to imgfoto.host via API service
5. Telegraph account is created for content publishing
6. Telegraph post is generated with uploaded image URLs
7. User receives final Telegraph post URL

## External Dependencies

### Required Services
- **imgfoto.host**: Image hosting service requiring API key authentication
- **Telegraph API**: Content publishing platform for creating posts

### Python Dependencies
- Flask: Web framework
- Werkzeug: WSGI utilities and secure file handling
- Requests: HTTP client for external API communication

### Frontend Dependencies
- Bootstrap 5.3: UI framework
- Font Awesome 6.4: Icon library

## Deployment Strategy

- **Environment**: Configured for cloud deployment with ProxyFix middleware
- **File Storage**: Temporary file handling in `/tmp/uploads`
- **Configuration**: Environment-based secret key management
- **Hosting**: Ready for deployment on platforms like Replit, Heroku, or similar

## Changelog

- June 28, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.