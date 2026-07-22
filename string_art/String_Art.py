import cv2
import numpy as np
import os
import math
import random

def get_circle_points(center, radius, nail_count):
    """
    Returns the positions of nails placed equally along the circumference of a circle.
    Each element is a tuple (x, y).
    """
    points = []
    for i in range(nail_count):
        theta = 2 * math.pi * i / nail_count
        x = int(center[0] + radius * math.cos(theta))
        y = int(center[1] + radius * math.sin(theta))
        points.append((x, y))
    return points

def sample_line_intensity(img, pt1, pt2):
    """
    Samples pixel intensities along the line from pt1 to pt2.
    Uses numpy.linspace to generate integer coordinates along the line.
    """
    distance = int(np.hypot(pt2[0] - pt1[0], pt2[1] - pt1[1]))
    if distance == 0:
        return int(img[pt1[1], pt1[0]])
    
    x_values = np.linspace(pt1[0], pt2[0], num=distance, dtype=int)
    y_values = np.linspace(pt1[1], pt2[1], num=distance, dtype=int)
    intensity_sum = int(np.sum(img[y_values, x_values]))
    return intensity_sum

def update_guiding_image(img, pt1, pt2, subtract_amount=50):
    """
    Subtracts a fixed amount from the pixels along the line between pt1 and pt2.
    Clipping is applied so that values do not fall below zero.
    """
    distance = int(np.hypot(pt2[0] - pt1[0], pt2[1] - pt1[1]))
    if distance == 0:
        img[pt1[1], pt1[0]] = max(0, img[pt1[1], pt1[0]] - subtract_amount)
        return

    x_values = np.linspace(pt1[0], pt2[0], num=distance, dtype=int)
    y_values = np.linspace(pt1[1], pt2[1], num=distance, dtype=int)
    for x, y in zip(x_values, y_values):
        img[y, x] = max(0, img[y, x] - subtract_amount)

def write_svg(svg_path, width, height, svg_lines):
    """
    Writes an SVG file with the given width and height and a list of line segments.
    Each element in svg_lines should be a tuple: ((x1, y1), (x2, y2)).
    """
    header = f'<?xml version="1.0" standalone="no"?>\n'
    header += f'<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"\n'
    header += f' "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n'
    header += f'<svg width="{width}px" height="{height}px" version="1.1" xmlns="http://www.w3.org/2000/svg">\n'
    
    # Group all lines in one group with stroke settings
    body = '  <g stroke="black" stroke-width="1" fill="none">\n'
    for (x1, y1), (x2, y2) in svg_lines:
        body += f'    <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" />\n'
    body += '  </g>\n'
    footer = '</svg>\n'
    
    with open(svg_path, "w") as f:
        f.write(header + body + footer)

def main():
    # Ask the user for the folder path where images are stored.
    base_folder = input("Enter the folder path where your image is stored: ").strip()
    
    # Ask for the image name (without .jpg extension).
    image_name = input("Enter the image name (without the .jpg extension): ").strip()
    image_path = os.path.join(base_folder, image_name + ".jpg")
    
    # Load the input image as grayscale.
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print("Could not load image. Please check the image path and try again.")
        return

    # Ask for the scale factor for upscaling.
    try:
        scale_factor = float(input("Enter the scale factor (e.g., 2 for double size): "))
    except ValueError:
        print("Invalid value for scale factor. Defaulting to 2.")
        scale_factor = 2.0

    # Upscale the image.
    img = cv2.resize(img, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_LINEAR)
    
    # Create a guiding image (inverted) to direct string placement.
    guiding_img = 255 - img

    # Ask for the number of lines to generate.
    try:
        lines_count = int(input("Enter the number of lines to generate: "))
    except ValueError:
        print("Invalid number of lines!")
        return

    # Ask for the number of nails.
    try:
        nail_count = int(input("Enter the number of nails to use: "))
    except ValueError:
        print("Invalid number of nails!")
        return

    # Ask for the desired physical diameter of the circle in centimeters.
    try:
        desired_diameter_cm = float(input("Enter the desired circle diameter in centimeters: "))
    except ValueError:
        print("Invalid diameter value!")
        return

    # Get image dimensions from the resized image and create a white canvas.
    height, width = img.shape
    canvas = np.full((height, width, 3), 255, dtype=np.uint8)

    # Define the circle (centered in the image with a margin).
    center = (width // 2, height // 2)
    radius_pixels = min(center[0], center[1]) - 10
    nail_points = get_circle_points(center, radius_pixels, nail_count)

    # Calculate conversion factor from pixels to centimeters.
    conversion_factor = desired_diameter_cm / (2 * radius_pixels)

    # Create the output folder inside the provided base folder if it does not exist.
    output_folder = os.path.join(base_folder, "output")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Prepare a list for nail sequence (one nail index per line) and for SVG line segments.
    nails_sequence = []
    svg_lines = []

    # Start with the initial nail.
    current_index = 0
    nails_sequence.append(current_index)
    
    cumulative_length_cm = 0  # total thread length in cm

    # Generate the string art.
    for line_num in range(1, lines_count + 1):
        best_index = None
        best_score = -1
        
        # Evaluate candidate connections.
        for i, target_pt in enumerate(nail_points):
            if i == current_index:
                continue
            intensity_sum = sample_line_intensity(guiding_img, nail_points[current_index], target_pt)
            # Calculate chord length.
            dx = target_pt[0] - nail_points[current_index][0]
            dy = target_pt[1] - nail_points[current_index][1]
            chord_pixels = math.hypot(dx, dy)
            if chord_pixels == 0:
                continue
            # New scoring: divide the intensity by the chord length.
            score = intensity_sum / chord_pixels

            if score > best_score:
                best_score = score
                best_index = i

        # Fallback: if candidate score is not positive, choose randomly.
        if best_score <= 0:
            candidates = [i for i in range(len(nail_points)) if i != current_index]
            best_index = random.choice(candidates)
        
        # Log the nail index.
        nails_sequence.append(best_index)
        
        # Record the line segment for the SVG (using current_point and best_index).
        svg_lines.append((nail_points[current_index], nail_points[best_index]))
        
        # Draw the selected line on the canvas.
        cv2.line(canvas, nail_points[current_index], nail_points[best_index], (0, 0, 0), 1)
        
        # Calculate chord length, convert to cm, and accumulate.
        chord_pixels = math.hypot(nail_points[best_index][0] - nail_points[current_index][0],
                                  nail_points[best_index][1] - nail_points[current_index][1])
        chord_length_cm = chord_pixels * conversion_factor
        cumulative_length_cm += chord_length_cm
        
        # Update the guiding image.
        update_guiding_image(guiding_img, nail_points[current_index], nail_points[best_index], subtract_amount=50)
        current_index = best_index

        # Console progress.
        progress = (line_num / lines_count) * 100
        print(f"Progress: {progress:.2f}%")
        
        # Save a PNG snapshot every 50 lines.
        if line_num % 50 == 0 or line_num == lines_count:
            output_path = os.path.join(output_folder, f"string_art_{line_num}.png")
            cv2.imwrite(output_path, canvas)

    # Thread length info.
    total_length_m = cumulative_length_cm / 100   # convert to meters
    length_info = f"Total thread length needed: {cumulative_length_cm:.2f} cm (~{total_length_m:.2f} m)\n"
    
    # Write log file: one nail number per line, then thread length.
    log_file_path = os.path.join(output_folder, "string_art_info.txt")
    with open(log_file_path, "w") as f:
        f.write("String Art Nail Sequence:\n")
        f.write("=========================\n")
        for nail in nails_sequence:
            f.write(f"{nail}\n")
        f.write("\n")
        f.write(length_info)
    
    # Write the SVG file with all line segments.
    svg_path = os.path.join(output_folder, "string_art.svg")
    write_svg(svg_path, width, height, svg_lines)
    
    print("String art generation complete!")
    print(length_info)
    print("Check the output folder for PNG images, string_art_info.txt, and string_art.svg.")

if __name__ == "__main__":
    main()
