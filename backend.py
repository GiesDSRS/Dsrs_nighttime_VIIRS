import os
import glob
import shutil
import json
import rasterio
from rasterio.windows import Window
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt 
from datetime import datetime
import subprocess


# Define paths
image_folder = "./night_time_images/"
output_folder = "Extracted_images"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

def extract_image_by_coordinates(input_file, output_file, lon, lat, width_meters, height_meters):
    with rasterio.open(input_file) as src:
        transform = src.transform
        col, row = ~transform * (lon, lat)

        half_width_pixels = width_meters / 500 / 2
        half_height_pixels = height_meters / 500 / 2

        if half_width_pixels <= 0 or half_height_pixels <= 0:
            raise ValueError("Window size is too small")

        window = Window(int(col - half_width_pixels), int(row - half_height_pixels),
                        int(width_meters / 500),
                        int(height_meters / 500))

        subset = src.read(window=window)
        subset_transform = rasterio.windows.transform(window, transform)
        subset_meta = src.meta.copy()

        subset_meta['width'] = window.width
        subset_meta['height'] = window.height
        subset_meta['transform'] = subset_transform

        with rasterio.open(output_file, 'w', **subset_meta) as dst:
            dst.write(subset)

def load_all_tiff_images(folder_path):
    images = []
    file_paths = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.tif'):
            file_path = os.path.join(folder_path, file_name)
            with rasterio.open(file_path) as src:
                image = src.read(1)
                images.append(image)
                file_paths.append(file_path)
    return images, file_paths

def compute_global_mean_std(images):
    all_pixels = np.concatenate([image.ravel() for image in images])
    global_mean = np.mean(all_pixels)
    global_std = np.std(all_pixels)
    return global_mean, global_std

def z_score_normalization(image, mean, std):
    norm_image = (image - mean) / std
    return norm_image

def save_tiff_image(image, file_path, reference_file):
    with rasterio.open(reference_file) as src:
        profile = src.profile

    with rasterio.open(file_path, 'w', **profile) as dst:
        dst.write(image, 1)

def calculate_average_pixel_intensity(image_path):
    img = Image.open(image_path)
    img_array = np.array(img)
    avg_intensity = np.mean(img_array)
    return avg_intensity


# Load inputs
# change the path to the actual path where user_data is created and saved 

def extract_all():
    with open('user_data.json') as f:
        params = json.load(f)

    latitude = params['latitude']
    longitude = params['longitude']
    length = params['length']
    breadth = params['breadth']
    from_date = datetime.strptime(params['from_date'], '%m-%Y')
    to_date = datetime.strptime(params['to_date'], '%m-%Y')

    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(output_folder)

    image_files = glob.glob(os.path.join(image_folder, "*.avg_rade9h.tif"))

    non_normalized_images = []
    for input_image in image_files:
        image_date_str = os.path.basename(input_image)[10:16]
        try:
            image_date = datetime.strptime(image_date_str, '%Y%m')
        except ValueError:
            continue  

        if from_date <= image_date <= to_date:
            output_image_file = os.path.join(output_folder, os.path.basename(input_image)[10:16] + "_extracted.tif")
            extract_image_by_coordinates(input_image, output_image_file, longitude, latitude,breadth,length)
            non_normalized_images.append(output_image_file)

    intensity = {}
    for filename in non_normalized_images:
        avg_intensity = calculate_average_pixel_intensity(filename)
        intensity[os.path.basename(filename)[0:6]] = avg_intensity  # Keyed by original filename

    # Plotting
    if intensity:
        sorted_dates = sorted(datetime.strptime(k, '%Y%m') for k in intensity.keys())
        sorted_values = [intensity[date.strftime('%Y%m')] for date in sorted_dates]
        formatted_dates = [date.strftime('%Y-%m') for date in sorted_dates]

        plt.figure(figsize=(12, 6))
        plt.plot(formatted_dates, sorted_values, linestyle='-', color='dodgerblue', marker='o')

        plt.title('Changes in Pixel Intensity Over Time', fontsize=16)
        plt.xlabel('Month', fontsize=14)
        plt.ylabel('Average Radiance (nW/cm²/sr)', fontsize=14)

        plt.xticks([date.strftime('%Y-%m') for date in sorted_dates if date.strftime('%m') == '01'], rotation=45, fontsize=12)

        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()

        plot_path = os.path.join(output_folder, "graph.png")
        plt.savefig(plot_path)
        plt.close()

        print("Plot saved as:", plot_path)
    else:
        print("No intensity data available for plotting.")

    images, _ = load_all_tiff_images(output_folder)

    global_mean, global_std = compute_global_mean_std(images)

    for file_path in non_normalized_images:
        with rasterio.open(file_path) as src:
            image = src.read(1)
            norm_image = z_score_normalization(image, global_mean, global_std)
            save_tiff_image(norm_image, file_path, file_path)

    for i, filename in enumerate(sorted(os.listdir(output_folder)), start=1):
        if filename.endswith(".tif"):
            new_filename = f"frame_{i:03d}.tif"
            os.rename(os.path.join(output_folder, filename), os.path.join(output_folder, new_filename))
    
    extracted_images_folder = "Extracted_images"
    video_output_file = os.path.join(extracted_images_folder, 'output.mp4')

    #convert_images_to_8bit(extracted_images_folder)
    #create_video_from_images(extracted_images_folder, video_output_file)


def convert_images_to_8bit(image_folder):
    """Convert TIFF images in the specified folder to 8-bit depth."""
    for file_name in os.listdir(image_folder):
        if file_name.endswith('.tif'):
            input_file = os.path.join(image_folder, file_name)
            output_file = os.path.join(image_folder, file_name)  # Overwrite the same file
            # Command to convert image to 8-bit using ImageMagick
            command = [
                'convert',
                input_file,
                '-depth', '8',
                output_file
            ]
            subprocess.run(command, check=True)
            print(f"Converted {input_file} to 8-bit.")

def create_video_from_images(image_folder, output_video_file, framerate=4, start_number=30):
    """Create a video from TIFF images in the specified folder."""
    # Define the path pattern for the input images
    image_pattern = os.path.join(image_folder, 'frame_%03d.tif')
    
    # Construct the ffmpeg command
    command = [
        'ffmpeg',
        '-framerate', str(framerate),
        '-start_number', str(start_number),
        '-i', image_pattern,
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        output_video_file
    ]
    

    subprocess.run(command, check=True)
    print(f"Video created successfully: {output_video_file}")



if __name__ == "__main__":
    extract_all()