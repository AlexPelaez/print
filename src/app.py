from service.printify_service import PrintifyService
# from video_util import VideoUtil
# from open_ai_service import OpenAiService
import uuid
import os
import random
from multiprocessing import Pool as ProcessPool


product_id = '67a325e52405f94e2707d5c8'  # Replace with the product ID to duplicate
image_folder = "/Users/alex/git/print/working_images_vertical"  # Folder where images are stored

# def generate_image_product():
#     prompt = OpenAiService.generate_psychedelic_prompt()
#     description = OpenAiService.generate_product_description(prompt)
#     title = OpenAiService.generate_product_title(description)

#     image = OpenAiService.generate_image(prompt)

#     OpenAiService.download_image(image, f"~/gen_images/testing{uuid.uuid4()}.jpg")
#     OpenAiService.download_image(image, '~/gen_working/test.jpg')
#     image_folder = '~/gen_working/'

def run(image_name):
	printify_service = PrintifyService(name="MyPrintifyService")
	image_path = os.path.join(image_folder, image_name)

	# Check if the file is an image (optional: check file extensions if needed)
	if os.path.isfile(image_path) and image_name.lower().endswith(('.png', '.jpg', '.jpeg')):
		print(f"Processing image: {image_name}")
		# prompt = OpenAiService.generate_psychedelic_prompt()
		# description = OpenAiService.generate_product_description(prompt)
		# title = OpenAiService.generate_product_title(description)
		description = 'test'
		title = 'test'

		# Upload the new image to Printify
		image_id = printify_service.upload_image(image_path)

		if image_id:
			print(f"Image uploaded successfully with ID: {image_id}")

			# Duplicate product with the new image
			new_product_id = printify_service.duplicate_product(product_id, image_id, title, description)
			printify_service.get_printify_mockup(new_product_id)

			# Publish the product
			# printify_service.publish_product(new_product_id)

			# Delete the product
			printify_service.delete_product(new_product_id)
		else:
			print(f"Error uploading image '{image_name}'. Skipping.")
	else:
		print(f"Skipping non-image file: {image_name}")
	

def main():
	# generate_image_product()


	
	# video_util = VideoUtil(name="MyVideoUtil")

	desired_file_list = [file_name for file_name in os.listdir(image_folder) if file_name.endswith(".jpg")]
	with ProcessPool(processes=1) as pool:
		results = pool.map(run, desired_file_list)

	print(results)

	
	# Iterate through all images in the folder
	# for image_name in os.listdir(image_folder):
		





if __name__ == "__main__":
	main()
