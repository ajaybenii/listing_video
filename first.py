from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO



def first_image(first_cover_image,listing_type,agency_logo,property_type,price,yearly_monthly,property_location):
    
    # Create new image with same dimensions as input image
    new_image = Image.new("RGBA", first_cover_image.size, (0, 0, 0, 0))

    # Define color and opacity of rectangle to paste onto new image
    rectangle_color = (0, 0, 0, 150) # red with 50% opacity

    # Paste colored rectangle onto new image
    draw = ImageDraw.Draw(new_image)
    draw.rectangle([(0, 140), ((1200,660))], fill=rectangle_color)


    text_color = (255, 255, 255) # white text color
    font = ImageFont.truetype("arialbd.ttf", 50)
    fontt = ImageFont.truetype("arialbd.ttf", 70)
    font1 = ImageFont.truetype("arial.ttf", 45) # define font and font size
    font2 = ImageFont.truetype("arial.ttf", 27)

    # Paste text onto new image
    draw.text((400, 180),listing_type, fill=text_color, font=fontt)
    draw.text((400, 260),property_type, fill=text_color, font=font1)
    draw.text((400, 460),("AED "+price), fill=text_color, font=font)
    

    if listing_type == "For rent":
        draw.text((400, 515),yearly_monthly, fill=text_color, font=font2)
        draw.text((430, 600),property_location, fill=text_color, font=font2)
        output_image = Image.alpha_composite(first_cover_image.convert("RGBA"), new_image)
        logo = Image.open("location.png").resize((20,20)).convert("L")
        output_image.paste(logo, (400, 605), mask=logo)

    else:
        draw.text((430, 525),property_location, fill=text_color, font=font2)
        output_image = Image.alpha_composite(first_cover_image.convert("RGBA"), new_image)
        logo = Image.open("location.png").resize((20,20)).convert("RGBA")
        output_image.paste(logo, (400, 530), mask=logo)
    # agent_logo2 = Image.open(agent_logo1).convert("RGB").resize((200,200))
    # output_image.show()
    # print("url = ",agency_logo)
    response_logo = requests.get(agency_logo)
    agency_logo = Image.open(BytesIO(response_logo.content)).convert("RGBA").resize((200,200))
    output_image.paste(agency_logo, (100, 45), mask=agency_logo)

    logo = Image.open("smartagent.png").resize((180,50))
    output_image.paste(logo, (1010, 2), mask=logo)

    # logo = Image.open("location.png").resize((20,20)).convert("L")
    # output_image.paste(logo, (400, 605), mask=logo)

    # Save output image
    output_image.save("output_image.png")
    result = "output_image.png"
    
    return result