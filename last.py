import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


def last_img(last_cover_image,agent_img,agency_logo,agent_name,agent_designation,contact_no,email_address):    

    # Create new image with same dimensions as input image
    new_image = Image.new("RGBA", last_cover_image.size, (0, 0, 0, 0))

    # Define color and opacity of rectangle to paste onto new image
    rectangle_color = (0, 0, 0, 150) # red with 50% opacity

    # Paste colored rectangle onto new image
    draw = ImageDraw.Draw(new_image)
    draw.rectangle([(0, 140), ((1200,660))], fill=rectangle_color)

    
    text_color = (255, 255, 255) # white text color
    font = ImageFont.truetype("arialbd.ttf", 36) # define font and font size
    font2 = ImageFont.truetype("arialbd.ttf", 24)
    # Paste text onto new image
    draw.text((80, 415),agent_name, fill=text_color, font=font)
    draw.text((80, 460),agent_designation, fill=text_color, font=font2)

    draw.text((110, 560),contact_no, fill=text_color, font=font)
    draw.text((110, 610),email_address, fill=text_color, font=font2)
    # Blend new image with input image using alpha composite
    output_image = Image.alpha_composite(last_cover_image.convert("RGBA"), new_image)

    response_logo = requests.get(agency_logo)
    agency_logo = Image.open(BytesIO(response_logo.content)).convert("RGBA").resize((300,300))
    output_image.paste(agency_logo, (750, 245), mask=agency_logo)

    logo = Image.open("smartagent.png").resize((180,50))
    output_image.paste(logo, (1010, 2), mask=logo)

    mobile_logo = Image.open("mobile_logo.png").resize((27,27)).convert("RGBA")
    output_image.paste(mobile_logo, (70, 566), mask=mobile_logo)

    email_logo = Image.open("email_logo.png").resize((27,27)).convert("RGBA")
    output_image.paste(email_logo, (70, 610), mask=email_logo)


    if agent_img == "string":

        agent_img = Image.open("agent_default_image.jpg").convert("RGBA").resize((210,210))
   
    else:   

        response_agent = requests.get(agent_img)
        agent_img = Image.open(BytesIO(response_agent.content)).convert("RGBA").resize(((210,210)))

    # Create a mask for the circular image
    mask = Image.new('L', agent_img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + agent_img.size, fill=255)

    # Apply the mask to the circular image
    agent_img.putalpha(mask)

    # Paste the circular image into the square image
    output_image.paste(agent_img, ((100,170)), agent_img)

    # Save output image
    output_image.save("last_img.png")
    # output_image.show()
    result = "last_img.png"

    return result
