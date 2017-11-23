import requests
import base64

class Data_Filter:
    def __init__(self, data_type):
        if data_type == 'face':
            self.detect_object = self.detect_face
            self._detect_base_url = 'https://api.kairos.com/detect'

    def detect_face(self, image_file=None):
        """
        Detects face within the image file.
        """
        auth_headers = {
            'app_id': 'da4c5a41',
            'app_key': '885a7c641219db6baedc3c714aee6257'
        }
        payload = self._extract_base64_contents(image_file)
        response = requests.post(self._detect_base_url, json=payload, headers=auth_headers)
        json_response = response.json()
        return response.status_code == 200 and 'Errors' not in json_response

    def _extract_base64_contents(self, image_path):
        with open(image_path, 'rb') as fp:
            return {'image': base64.b64encode(fp.read()).decode('ascii')}

