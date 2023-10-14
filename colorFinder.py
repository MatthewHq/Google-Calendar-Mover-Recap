import math

def hex_to_rgb(hex_color):
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return r, g, b

def calculate_distance(color1, color2):
    r1, g1, b1 = color1
    r2, g2, b2 = color2
    return math.sqrt((r1 - r2)**2 + (g1 - g2)**2 + (b1 - b2)**2)

def find_closest_color(inputColor, colorList):
    inputRGB = hex_to_rgb(inputColor)
    closestColor = colorList[0]
    minDist = calculate_distance(inputRGB, hex_to_rgb(colorList[0]))

    for color in colorList[1:]:
        distance = calculate_distance(inputRGB, hex_to_rgb(color))
        if distance < minDist:
            minDist = distance
            closestColor = color

    return closestColor



# list_a = ['#a4bdfc','#7ae7bf','#dbadff','#ff887c','#fbd75b','#ffb878','#46d6db','#e1e1e1','#5484ed','#51b749','#dc2127']
# list_b=  ['#ac725e','#d06b64','#f83a22','#fa573c','#ff7537','#ffad46','#42d692','#16a765','#7bd148','#b3dc6c','#fbe983','#fad165','#92e1c0','#9fe1e7','#9fc6e7','#4986e7','#9a9cff','#b99aff','#c2c2c2','#cabdbf','#cca6ac','#f691b2','#cd74e6','#a47ae2']
# target_color = '#cca6ac'

# for b in list_b:
#     closest_color = find_closest_color(b, list_a)
#     print(f"---\n{b}\n{closest_color}\n---")