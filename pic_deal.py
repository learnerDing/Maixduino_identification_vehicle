from PIL import Image

def compress_image(image_path):
    with open(image_path, 'rb') as file:
        image = Image.open(file)
        # 将image处理为320x240像素
        image = image.resize((320, 240), Image.ANTIALIAS)

        # 压缩图片
        image.save("compressed_image.jpg", "JPEG", quality=85)

        # 重新加载压缩后的图片
        compressed_image = Image.open("compressed_image.jpg")
        return compressed_image

def rgb565_to_image(image):
    rgb565_image = Image.new("RGB", image.size, (0, 0, 0))
    width, height = image.size
    for y in range(height):
        for x in range(width):
            r, g, b = image.getpixel((x, y))
            r = r >> 3
            g = g >> 2
            b = b >> 3
            rgb565_color = (r << 11) | (g << 5) | b
            # 将两个字节合并为一个整数值
            combined_color = (rgb565_color >> 8) << 8 | (rgb565_color & 0xFF)
            rgb565_image.putpixel((x, y), combined_color)
    return rgb565_image


def image_to_bytes(rgb565_image):
    width, height = rgb565_image.size
    byte_array = bytearray(width * height * 2)
    for y in range(height):
        for x in range(width):
            r, g, b = rgb565_image.getpixel((x, y))
            byte_array[2 * (x + y * width)] = r
            byte_array[2 * (x + y * width) + 1] = g
    return bytes(byte_array)
