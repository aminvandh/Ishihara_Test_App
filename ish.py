import math
import random
import io
import svgwrite
from PIL import Image, ImageDraw, ImageFont

try:
    from scipy.spatial import cKDTree as KDTree
    import numpy as np
    IMPORTED_SCIPY = True
except ImportError:
    IMPORTED_SCIPY = False

BACKGROUND = (255, 255, 255)
TOTAL_CIRCLES = 1500

color = lambda c: ((c >> 16) & 255, (c >> 8) & 255, c & 255)

COLORS_ON = [
    color(0xF9BB82), color(0xEBA170), color(0xFCCD84)
]
COLORS_OFF = [
    color(0x9CA594), color(0xACB4A5), color(0xBBB964),
    color(0xD7DAAA), color(0xE5D57D), color(0xD1D6AF)
]


def generate_circle(image_width, image_height, min_diameter, max_diameter):
    radius = random.triangular(min_diameter, max_diameter,
                               max_diameter * 0.8 + min_diameter * 0.2) / 2

    angle = random.uniform(0, math.pi * 2)
    distance_from_center = random.uniform(0, image_width * 0.48 - radius)
    x = image_width  * 0.5 + math.cos(angle) * distance_from_center
    y = image_height * 0.5 + math.sin(angle) * distance_from_center

    return x, y, radius


def overlaps_motive(image, circle):
    x, y, r = circle
    points_x = [x, x, x, x-r, x+r, x-r*0.93, x-r*0.93, x+r*0.93, x+r*0.93]
    points_y = [y, y-r, y+r, y, y, y+r*0.93, y-r*0.93, y+r*0.93, y-r*0.93]

    for xy in zip(points_x, points_y):
        if image.getpixel(xy)[:3] != BACKGROUND:
            return True

    return False


def circle_intersection(circle1, circle2):
    x1, y1, r1 = circle1
    x2, y2, r2 = circle2
    return (x2 - x1)**2 + (y2 - y1)**2 < (r2 + r1)**2


def circle_draw(draw_image, image, circle):
    fill_colors = COLORS_ON if overlaps_motive(image, circle) else COLORS_OFF
    fill_color = random.choice(fill_colors)

    x, y, r = circle
    draw_image.ellipse((x - r, y - r, x + r, y + r),
                       fill=fill_color,
                       outline=fill_color)

def save_svg(circles, image, width, height):
    filename = 'result.svg'
    dwg = svgwrite.Drawing(filename, size=(width, height), profile='tiny')

    for x, y, r in circles:
        fill_colors = COLORS_ON if overlaps_motive(image, (x, y, r)) else COLORS_OFF
        fill_color = random.choice(fill_colors)

        dwg.add(dwg.ellipse(center=(x, y), r=(r, r), fill=svgwrite.rgb(fill_color[0], fill_color[1], fill_color[2])))

    text = image.info.get('Description', '')
    if text:
        dwg.add(dwg.text(text, insert=(width * 0.1, height * 0.9), fill=svgwrite.rgb(0, 0, 0)))

    dwg.save()


def create_text_image(text):
    image_size = (800, 800)
    font_size = 600

    image = Image.new("RGB", image_size, color="white")

    font = ImageFont.truetype("arial.ttf", font_size)
    left, upper, right, lower = font.getbbox(text)
    text_width = right - left
    text_height = lower - upper

    while text_width > image_size[0] or text_height > image_size[1]:
        font_size -= 5
        font = ImageFont.truetype("arial.ttf", font_size)
        left, upper, right, lower = font.getbbox(text)
        text_width = right - left
        text_height = lower - upper

    text_x = (image_size[0] - text_width) // 2
    text_y = (image_size[1] - text_height) // 2

    draw = ImageDraw.Draw(image)
    draw.text((text_x, text_y), text, fill="black", font=font)

    image_binary = io.BytesIO()
    image.save(image_binary, format='PNG')
    image_binary.seek(0)  # Move the cursor to the beginning of the binary data
    return image_binary

def main():
    input_text: str = input('Enter a text with 4 str: ')[:4]
    image_binary = create_text_image(input_text)
    image = Image.open(image_binary)
    image2 = Image.new('RGB', image.size, BACKGROUND)
    draw_image = ImageDraw.Draw(image2)

    width, height = image.size

    min_diameter = (width + height) / 200
    max_diameter = (width + height) / 75

    circle = generate_circle(width, height, min_diameter, max_diameter)
    circles = [circle]

    circle_draw(draw_image, image, circle)

    try:
        for i in range(TOTAL_CIRCLES):
            tries = 0
            if IMPORTED_SCIPY:
                kdtree = KDTree([(x, y) for (x, y, _) in circles])
                while True:
                    circle = generate_circle(width, height, min_diameter, max_diameter)
                    elements, indexes = kdtree.query([(circle[0], circle[1])], k=12)
                    for element, index in zip(elements[0], indexes[0]):
                        if not np.isinf(element) and circle_intersection(circle, circles[index]):
                            break
                    else:
                        break
                    tries += 1
            else:
                while any(circle_intersection(circle, circle2) for circle2 in circles):
                    tries += 1
                    circle = generate_circle(width, height, min_diameter, max_diameter)

            circles.append(circle)
            circle_draw(draw_image, image, circle)
            save_svg(circles, image, width, height)

    except (KeyboardInterrupt, SystemExit):
        pass

    image2.show()

if __name__ == '__main__':
    main()