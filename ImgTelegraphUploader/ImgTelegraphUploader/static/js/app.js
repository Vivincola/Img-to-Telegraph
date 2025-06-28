document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('photos');
    const selectFilesBtn = document.getElementById('selectFilesBtn');
    const fileList = document.getElementById('fileList');
    const uploadForm = document.getElementById('uploadForm');
    const submitBtn = document.getElementById('submitBtn');
    const progressSection = document.getElementById('progressSection');
    const progressBar = document.querySelector('.progress-bar');
    const progressText = document.getElementById('progressText');
    const resultSection = document.getElementById('resultSection');
    const errorSection = document.getElementById('errorSection');
    const errorText = document.getElementById('errorText');

    let selectedFiles = [];

    // File selection handlers
    selectFilesBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop handlers
    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', handleDragOver);
    dropZone.addEventListener('dragleave', handleDragLeave);
    dropZone.addEventListener('drop', handleDrop);

    // Form submission handler
    uploadForm.addEventListener('submit', handleSubmit);

    function handleDragOver(e) {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    }

    function handleDragLeave(e) {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
    }

    function handleDrop(e) {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        
        const files = Array.from(e.dataTransfer.files);
        addFiles(files);
    }

    function handleFileSelect(e) {
        const files = Array.from(e.target.files);
        addFiles(files);
    }

    function addFiles(files) {
        const validFiles = files.filter(file => {
            const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/bmp', 'image/webp'];
            return validTypes.includes(file.type);
        });

        if (validFiles.length !== files.length) {
            showError('Some files were skipped because they are not supported image formats.');
        }

        selectedFiles = [...selectedFiles, ...validFiles];
        updateFileList();
    }

    function updateFileList() {
        if (selectedFiles.length === 0) {
            fileList.innerHTML = '';
            return;
        }

        const listHTML = selectedFiles.map((file, index) => `
            <div class="file-item">
                <div class="file-info">
                    <i class="fas fa-image me-2 text-primary"></i>
                    <span class="file-name">${file.name}</span>
                    <span class="file-size ms-2">(${formatFileSize(file.size)})</span>
                </div>
                <button type="button" class="btn btn-outline-danger btn-sm btn-remove" onclick="removeFile(${index})">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `).join('');

        fileList.innerHTML = `
            <div class="mb-2">
                <strong>${selectedFiles.length} file(s) selected:</strong>
            </div>
            ${listHTML}
        `;
    }

    window.removeFile = function(index) {
        selectedFiles.splice(index, 1);
        updateFileList();
    };

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function handleSubmit(e) {
        e.preventDefault();
        
        // Hide previous results/errors
        hideMessages();

        // Validate form
        const apiKey = document.getElementById('api_key').value.trim();
        const title = document.getElementById('title').value.trim();
        const author = document.getElementById('author').value.trim();

        if (!apiKey || !title || !author) {
            showError('Please fill in all required fields (API Key, Title, and Author).');
            return;
        }

        if (selectedFiles.length === 0) {
            showError('Please select at least one image to upload.');
            return;
        }

        // Start upload process
        uploadFiles();
    }

    async function uploadFiles() {
        const formData = new FormData();
        
        // Add form fields
        formData.append('api_key', document.getElementById('api_key').value.trim());
        formData.append('title', document.getElementById('title').value.trim());
        formData.append('author', document.getElementById('author').value.trim());
        formData.append('content', document.getElementById('content').value.trim());

        // Add files
        selectedFiles.forEach(file => {
            formData.append('photos', file);
        });

        // Show progress
        showProgress();
        updateProgress(10, 'Uploading images to imgfoto.host...');

        try {
            submitBtn.disabled = true;

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            updateProgress(50, 'Processing images...');

            // Check if response is JSON or HTML
            const contentType = response.headers.get('content-type');
            let result;
            
            if (contentType && contentType.includes('application/json')) {
                result = await response.json();
            } else {
                // Server returned HTML error page
                const errorText = await response.text();
                if (errorText.includes('<html>')) {
                    throw new Error('Server error occurred. This may be due to API rate limits or connection issues. Please try uploading fewer images at once or try again later.');
                } else {
                    result = { success: false, error: 'Unexpected server response format' };
                }
            }

            updateProgress(80, 'Creating Telegraph post...');

            if (result.success) {
                updateProgress(100, 'Complete!');
                setTimeout(() => {
                    showSuccess(result);
                }, 500);
            } else {
                throw new Error(result.error || 'Upload failed');
            }

        } catch (error) {
            console.error('Upload error:', error);
            showError(error.message || 'An unexpected error occurred. Please try again.');
        } finally {
            submitBtn.disabled = false;
        }
    }

    function showProgress() {
        progressSection.style.display = 'block';
        resultSection.style.display = 'none';
        errorSection.style.display = 'none';
    }

    function updateProgress(percent, text) {
        progressBar.style.width = percent + '%';
        progressText.textContent = text;
    }

    function showSuccess(result) {
        progressSection.style.display = 'none';
        
        // Show warning if some uploads failed
        const warningHTML = result.warning ? `
            <div class="alert alert-warning mb-3">
                <h6 class="alert-heading">
                    <i class="fas fa-exclamation-triangle me-2"></i>Partial Upload Warning
                </h6>
                <p class="mb-0">${result.warning}</p>
                <small class="text-muted">
                    Successfully uploaded: ${result.total_uploaded}/${result.total_files} files
                </small>
            </div>
        ` : '';
        
        const successHTML = `
            ${warningHTML}
            <div class="card result-card">
                <div class="card-body">
                    <h5 class="card-title text-success">
                        <i class="fas fa-check-circle me-2"></i>Telegraph Post Created!
                    </h5>
                    <p class="card-text">
                        ${result.warning ? 
                            `Your Telegraph post was created with ${result.total_uploaded} of ${result.total_files} images.` :
                            'Your Telegraph post has been created successfully!'
                        }
                    </p>
                    
                    <div class="mb-3">
                        <strong>Telegraph Post URL:</strong>
                        <div class="input-group mt-2">
                            <input type="text" class="form-control" value="${result.telegraph_url}" readonly id="telegraphUrl">
                            <button class="btn btn-outline-primary" type="button" onclick="copyToClipboard('telegraphUrl')">
                                <i class="fas fa-copy"></i>
                            </button>
                        </div>
                    </div>

                    <div class="mb-3">
                        <strong>Successfully Uploaded Images (${result.uploaded_images.length}):</strong>
                        <div class="row mt-2">
                            ${result.uploaded_images.slice(0, 12).map(url => `
                                <div class="col-md-2 col-sm-3 col-4 mb-2">
                                    <img src="${url}" class="img-fluid upload-preview" alt="Uploaded image">
                                </div>
                            `).join('')}
                            ${result.uploaded_images.length > 12 ? `
                                <div class="col-12">
                                    <small class="text-muted">And ${result.uploaded_images.length - 12} more images...</small>
                                </div>
                            ` : ''}
                        </div>
                    </div>

                    <div class="d-flex gap-2">
                        <a href="${result.telegraph_url}" target="_blank" class="btn btn-primary">
                            <i class="fas fa-external-link-alt me-2"></i>View Telegraph Post
                        </a>
                        <button type="button" class="btn btn-secondary" onclick="resetForm()">
                            <i class="fas fa-plus me-2"></i>Create Another Post
                        </button>
                    </div>
                </div>
            </div>
        `;

        resultSection.innerHTML = successHTML;
        resultSection.style.display = 'block';
    }

    function showError(message) {
        progressSection.style.display = 'none';
        errorText.textContent = message;
        errorSection.style.display = 'block';
        resultSection.style.display = 'none';
    }

    function hideMessages() {
        progressSection.style.display = 'none';
        errorSection.style.display = 'none';
        resultSection.style.display = 'none';
    }

    window.copyToClipboard = function(elementId) {
        const element = document.getElementById(elementId);
        element.select();
        element.setSelectionRange(0, 99999);
        document.execCommand('copy');
        
        // Show temporary feedback
        const button = element.nextElementSibling;
        const originalHTML = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check"></i>';
        button.classList.replace('btn-outline-primary', 'btn-success');
        
        setTimeout(() => {
            button.innerHTML = originalHTML;
            button.classList.replace('btn-success', 'btn-outline-primary');
        }, 2000);
    };

    window.resetForm = function() {
        uploadForm.reset();
        selectedFiles = [];
        updateFileList();
        hideMessages();
        submitBtn.disabled = false;
    };
});
