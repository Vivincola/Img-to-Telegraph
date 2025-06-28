import requests
import json
import logging
import uuid

class TelegraphService:
    def __init__(self):
        self.base_url = "https://api.telegra.ph"
        self.access_token = None
        self.logger = logging.getLogger(__name__)
    
    def create_account(self):
        """
        Create a Telegraph account and store the access token
        """
        try:
            url = f"{self.base_url}/createAccount"
            
            # Generate a unique short name
            short_name = f"PhotoUploader{str(uuid.uuid4())[:8]}"
            
            data = {
                'short_name': short_name,
                'author_name': 'Photo Uploader',
                'author_url': ''
            }
            
            self.logger.debug("Creating Telegraph account")
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('ok'):
                    self.access_token = result.get('result', {}).get('access_token')
                    self.logger.debug(f"Successfully created Telegraph account: {self.access_token}")
                    return self.access_token
                else:
                    raise Exception(f"Telegraph API error: {result.get('error', 'Unknown error')}")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.Timeout:
            raise Exception("Telegraph account creation timeout - please try again")
        except requests.exceptions.ConnectionError:
            raise Exception("Connection error - please check your internet connection")
        except Exception as e:
            self.logger.error(f"Error creating Telegraph account: {str(e)}")
            raise e
    
    def create_post(self, title, author, content, image_urls):
        """
        Create a Telegraph post with the provided content and images
        """
        try:
            # Create account if we don't have an access token
            if not self.access_token:
                self.create_account()
            
            url = f"{self.base_url}/createPage"
            
            # Build content array with text and images
            content_array = []
            
            # Add initial content if provided
            if content.strip():
                content_array.append({
                    'tag': 'p',
                    'children': [content.strip()]
                })
            
            # Add images in the order they were uploaded
            for image_url in image_urls:
                content_array.append({
                    'tag': 'img',
                    'attrs': {
                        'src': image_url
                    }
                })
                # Add a line break after each image
                content_array.append({
                    'tag': 'br'
                })
            
            data = {
                'access_token': self.access_token,
                'title': title,
                'author_name': author,
                'content': json.dumps(content_array),
                'return_content': 'false'
            }
            
            self.logger.debug(f"Creating Telegraph post: {title}")
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('ok'):
                    page_data = result.get('result', {})
                    page_url = f"https://telegra.ph/{page_data.get('path')}"
                    self.logger.debug(f"Successfully created Telegraph post: {page_url}")
                    return page_url
                else:
                    raise Exception(f"Telegraph API error: {result.get('error', 'Unknown error')}")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.Timeout:
            raise Exception("Telegraph post creation timeout - please try again")
        except requests.exceptions.ConnectionError:
            raise Exception("Connection error - please check your internet connection")
        except Exception as e:
            self.logger.error(f"Error creating Telegraph post: {str(e)}")
            raise e
