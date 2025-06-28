import requests
import os
import logging
import time
import json


class ImgfotoService:

    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://imgfoto.host/api/1"
        self.logger = logging.getLogger(__name__)

    def upload_image(self, file_path, max_retries=5):
        """
        Upload an image to imgfoto.host and return the direct URL
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                upload_url = f"{self.base_url}/upload"

                with open(file_path, 'rb') as file:
                    files = {'source': file}
                    data = {'key': self.api_key}

                    self.logger.debug(
                        f"Uploading image to imgfoto.host (attempt {attempt + 1}): {file_path}"
                    )

                    # Progressive timeout increase
                    timeout = 45 + (attempt * 100)

                    # Use session for connection pooling
                    session = requests.Session()
                    session.headers.update(
                        {'User-Agent': 'Photo-Telegraph-Uploader/1.0'})

                    response = session.post(upload_url,
                                            files=files,
                                            data=data,
                                            timeout=timeout)

                    # Validate response format
                    content_type = response.headers.get('content-type',
                                                        '').lower()

                    if response.status_code != 200:
                        if response.status_code == 429:
                            raise Exception(
                                "Rate limit exceeded. Please wait before uploading more images."
                            )
                        elif response.status_code >= 500:
                            raise Exception(
                                f"Server error (HTTP {response.status_code}). Service may be temporarily unavailable."
                            )
                        else:
                            raise Exception(
                                f"HTTP {response.status_code}: Upload failed")

                    # Handle different content types
                    if 'text/html' in content_type:
                        raise Exception(
                            "Server returned HTML error page - possible API key issue or service maintenance"
                        )

                    if 'application/json' not in content_type and 'text/json' not in content_type:
                        self.logger.warning(
                            f"Unexpected content type: {content_type}")

                    try:
                        result = response.json()
                    except json.JSONDecodeError as e:
                        self.logger.error(
                            f"JSON decode error: {e}, Response: {response.text[:200]}"
                        )
                        raise Exception(
                            "Invalid response format from imgfoto.host API")

                    # Validate API response structure
                    if not isinstance(result, dict):
                        raise Exception(
                            "Invalid response structure from imgfoto.host")

                    if result.get('status_code') == 200:
                        image_data = result.get('image', {})
                        direct_url = image_data.get('url')

                        if direct_url:
                            self.logger.info(
                                f"Successfully uploaded: {direct_url}")
                            return direct_url
                        else:
                            raise Exception(
                                "No image URL in successful response")
                    else:
                        error_info = result.get('error', {})
                        if isinstance(error_info, dict):
                            error_msg = error_info.get('message',
                                                       'Unknown API error')
                        else:
                            error_msg = str(error_info)
                        raise Exception(f"API error: {error_msg}")

            except (requests.exceptions.Timeout,
                    requests.exceptions.ConnectionError) as e:
                last_exception = e
                error_type = "timeout" if isinstance(
                    e, requests.exceptions.Timeout) else "connection"

                if attempt < max_retries - 1:
                    wait_time = 30  # Cap at 30 seconds
                    self.logger.warning(
                        f"Upload {error_type} error on attempt {attempt + 1}, waiting {wait_time}s before retry..."
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception(
                        f"Upload failed due to {error_type} issues after {max_retries} attempts"
                    )

            except requests.exceptions.RequestException as e:
                last_exception = e
                self.logger.error(
                    f"Request error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)
                    continue
                else:
                    raise Exception(f"Network error: {str(e)}")

            except Exception as e:
                last_exception = e
                error_str = str(e)

                # Don't retry certain errors
                if any(phrase in error_str.lower() for phrase in
                       ['api key', 'rate limit', 'invalid response format']):
                    raise e

                if attempt < max_retries - 1:
                    self.logger.warning(
                        f"Error on attempt {attempt + 1}: {error_str}, retrying..."
                    )
                    time.sleep(2**attempt)
                    continue
                else:
                    raise e

        # Fallback error if we somehow get here
        if last_exception:
            raise Exception(f"Upload failed: {str(last_exception)}")
        else:
            raise Exception("Upload failed for unknown reasons")
