# import logging
import cv2
from django.http import StreamingHttpResponse
from django.views.decorators import gzip
import mediapipe as mp
# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# Set up logger
# logger = logging.getLogger(__name__)

# Function for MediaPipe detection
def mediapipe_detection(image, model):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image.flags.writeable = False
    results = model.process(image)
    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    return image, results

# Function to draw landmarks and send pose info
def draw_styled_landmarks(image, results):
    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                              mp_drawing.DrawingSpec(color=(255, 165, 0), thickness=2, circle_radius=1), 
                              mp_drawing.DrawingSpec(color=(255, 165, 0), thickness=2, circle_radius=1))
    pose_info = {
        'type': 'pose_info',
        'landmarks': [
            {
                'x': lm.x,
                'y': lm.y,
                'z': lm.z,
                'visibility': lm.visibility
            }
            for lm in results.pose_landmarks.landmark
        ] if results.pose_landmarks else []
    }
    # logger.debug(f"Pose info: {pose_info}")

    # channel_layer = get_channel_layer()
    # async_to_sync(channel_layer.group_send)(
    #     'live_detection',
    #     {
    #         'type': 'send_pose_info',
    #         'info': pose_info
    #     }
    # )

  
# Generator function to yield video frames
def generate_frames():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)  # Width
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 640)  # Height
    
    with mp.solutions.pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Make detections
            image, results = mediapipe_detection(frame, pose)
            
            # Draw landmarks and send pose info
            draw_styled_landmarks(image, results)
            
            # # Resize image to 100% width and height
            # height, width, _ = image.shape
            # target_width = int(width * 1.0)  # 100% width
            # target_height = int(height * 2.3)  # 100% height
            # image = cv2.resize(image, (target_width, target_height))
            
            # # Convert image to JPEG format
            _, jpeg = cv2.imencode('.jpg', image)
            frame_bytes = jpeg.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()

# View function to stream video feed
@gzip.gzip_page
def liveDetection(request):
    try:
        return StreamingHttpResponse(generate_frames(), content_type="multipart/x-mixed-replace;boundary=frame")
    except Exception as e:
        # logger.error(f"An error occurred: {str(e)}")
        return None  # or handle the error in a suitable way