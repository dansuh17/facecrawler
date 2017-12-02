import cv2
import sys

class DataFilter:
    """
    Data filter class used for filtering crawled image by its content.
    """
    def __init__(self, data_type):
        if data_type == 'face':
            self.detect_object = self.detect_face
            # file used by openCV for detecting faces
            self.casc_path = "haarcascade_frontalface_default.xml"

    def detect_face(self, image_file=None):
        """
        Detects face within the image file.
        """
        # Create the haar cascade
        faceCascade = cv2.CascadeClassifier(self.casc_path)

        # Read the image
        gray = cv2.imread(image_file, 0)

        # Detect faces in the image
        faces = faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
            # flags = cv2.CV_HAAR_SCALE_IMAGE
        )
        if len(faces) > 0:
            return True
        return False
