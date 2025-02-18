import os
import cv2
import numpy as np

# path to the Google Drive folder with images
path = "/Users/alex/movie_images/image_sequence_video_app/images"
os.chdir(path)

fps = 30
video_length_seconds = 7
total_frames = video_length_seconds * fps

# Counting the number of images in the directory
images = [img for img in os.listdir('.') if img.endswith((".jpg", ".jpeg", ".png"))]
num_of_images = len(images)
print("Number of Images:", num_of_images)

# Select a subset of images to use
selected_images = images[:min(len(images), total_frames // 2)]
num_selected_images = len(selected_images)

# Generate a list of frame allocations per selected image, increasing from 1 to 20 frames
frame_allocations = np.linspace(1, 80, num_selected_images, dtype=int) ** 1.5
frame_allocations = np.round(frame_allocations * total_frames / frame_allocations.sum()).astype(int)

class PrintifyService:
    def __init__(self, name):
        self.name = name
        
    def generate_video():
        video_name = 'mygeneratedvideo.mp4'
        
        # Set frame from the first image
        frame = cv2.imread(os.path.join(path, selected_images[0]))
        height, width, layers = frame.shape

        # Video writer to create .mp4 file
        video = cv2.VideoWriter(video_name, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

        # Appending images to video based on frame allocations
        for image, frame_count in zip(selected_images, frame_allocations):
            img = cv2.imread(os.path.join(path, image))
            for _ in range(frame_count):
                video.write(img)

        # Release the video file
        video.release()
        cv2.destroyAllWindows()
        print("Video generated successfully!")

