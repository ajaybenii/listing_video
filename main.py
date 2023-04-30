import os
import openai
import math
import cv2
import pyttsx3
import requests

import numpy as np
import moviepy.editor as mp

from typing import List
from PIL import Image
from gtts import gTTS
from fastapi import FastAPI
from englisttohindi.englisttohindi import EngtoHindi

from first import first_image
from last import last_img
from image_to_text import predict_step
from dotenv import load_dotenv

from io import BytesIO
from typing import Optional
from urllib.parse import urlparse
from PIL import Image
from pydantic import BaseModel

from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
from fastapi.param_functions import Query
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="Video genration",
    description="classify images into different categories")

load_dotenv()
openai.api_key = os.getenv('openai.api_key')

# Constants
AUDIO_FILE_NAME = "audio.mp3"
AMBIENT_SOUND_FILE_NAME = "ambient.mp3"
MERGED_AUDIO_FILE_NAME = "merged.mp3"
AMBIENT_FADEOUT_DURATION = 2 # seconds
INTRO_CLIP_DURATION = 5 # seconds
OUTPUT_SIZE = (1200, 800)
CODEC = "libx264"
FPS = 24
VOICEOVER_LANGUAGE='en'

#input images
img_list=[]
default_img_path = "agent_default_image.jpg"

# Initialize the engine
engine = pyttsx3.init()

@app.get("/")
async def root():
    return "Api is working"


class Item(BaseModel):
    image_url: List[str]
    agent_img: Optional[str]
    first_cover_image:str
    last_cover_image:str
    listing_type:str
    property_location:str
    agency_logo: Optional[str]
    agent_name:str
    agent_designation:str
    contact_no:str
    property_type:str
    price:str
    yearly_monthly:str
    email_address:str
    bedroom:str
    bathroom:str
    area:str

@app.post("/genrate_video")
# async def get_video(cover_image:Optional[str],agent_logo: Optional[str],agent_name:Optional[str],consultancy_name:Optional[str],contact_no:Optional[str],property_type:Optional[str],project:str,price_property:Optional[str],yearly_monthly:Optional[str],email_address:Optional[str],locality:Optional[str],bedroom:Optional[str],bathroom:Optional[str],area:Optional[str],agent_img: str=None):
async def get_video(item:Item,voice:bool=False):

    n = 0
    x=1

    for i in range (len(item.image_url)):

        response = requests.get(item.image_url[n])
        cover_image = Image.open(BytesIO(response.content)).convert("RGB").resize((1200,800)).save(f"{x}.jpg")

        img_list.append(str(f"{x}.jpg"))

        n+=1
        x+=1

    response = requests.get(item.first_cover_image)
    first_cover_image = Image.open(BytesIO(response.content)).convert("RGB").resize((OUTPUT_SIZE))
    

    response = requests.get(item.last_cover_image)
    last_cover_image = Image.open(BytesIO(response.content)).convert("RGB").resize((OUTPUT_SIZE))
    

    class ListingVideoGenerator:
        '''
        Generates a video for a listing
        '''

        def __init__(self, listing_data: dict):
            self.listing_data = listing_data
            self.num_images = len(listing_data['images'])
            self.video_output_size = OUTPUT_SIZE
            self.fps = FPS


        def _get_captions(self):
            #TODO: Make changes to predict_step to accept a list of URLs
            captions = predict_step(self.listing_data['images'])
            return captions


        def _get_voiceover_text(self, captions: List[str]):
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Pretend you are real-estate salesman and you are showing property to a customer. You only speak in short 3-4 liner sentences which are concise, pleasant and informative for the customer so that he/she gets inspired to get the property. You don't use unnecessary adjectives. You don't mention the following objects such as beds, painting, desk, stove, sink, mirror. you are given a description of the room that you are currently showing in plain text. Can you summarise the following descriptions in an elegant way in your inspirational style in a short paragraph. Make sure the sequence of the descriptions are maintained in your summary. Here are the descriptions of different parts of the property:"},
                    {"role": "user", "content": f'{" ".join(captions)}' },
                ]
            )
            return response.choices[0]['message']['content']


        def _create_voiceover_audio(self, voiceover_text):
            # # Input text to convert to speech
            # # text = "Welcome to this stunning property, where you'll find an expansive living area featuring a statement wall to reflect your personal style. Moving along, the well-appointed bathroom offers both functionality and elegance. The spacious room with an impressive window and charming wooden flooring ensures a delightful ambience. Finally, the modern kitchen comes equipped with a top-of-the-line oven, perfect for all your culinary adventures. This exceptional home is sure to inspire you to make it your own."
            
            # # voiceover_text = EngtoHindi(voiceover_text).convert
            # # print("Hindi Text: ", voiceover_text)
            if voice == "True":
                tts = gTTS(text=voiceover_text, tld="com")
                tts.save(AUDIO_FILE_NAME)

                # # pass
                # Set properties
            else:
                engine.setProperty('rate', 150)  # Speed percent (can go over 100)
                engine.setProperty('volume', 0.9)  # Volume 0-1

                # Convert text to speech
                # text = "Hello, Looking for a safe and affordable locality to rent an apartment with your family in Mumbai.."
                engine.setProperty('voice', 'english-us') # Set male voice
                engine.save_to_file(voiceover_text, AUDIO_FILE_NAME)
                engine.runAndWait()

        def _process_image(self, img_path):
            print(f"Processing: {img_path}")
            img = Image.open(img_path)
            img = img.convert('RGB')  # Convert to RGB format
            img = img.resize(self.video_output_size, Image.ANTIALIAS)  # Resize the image
            return np.array(img)


        def _process_audio_clips(self):
            # Load audio files
            audio_clip = mp.AudioFileClip(AUDIO_FILE_NAME)

            #Increase the volume of the second clip
            audio_clip = audio_clip.volumex(2.0)

            # Fade out the ambient clip and merge it with the first clip
            ambient_clip = mp.AudioFileClip(AMBIENT_SOUND_FILE_NAME)
            ambient_clip = ambient_clip.fx(mp.vfx.loop, duration=INTRO_CLIP_DURATION)
            ambient_clip = ambient_clip.audio_fadeout(AMBIENT_FADEOUT_DURATION)

            merged_audio_clip = mp.concatenate_audioclips([ambient_clip, audio_clip])

            # Write the final audio file
            merged_audio_clip.write_audiofile(MERGED_AUDIO_FILE_NAME)

        
        def _generate_image_clips(self, images, clip_duration):
            print(f'Generating image clips of clip duration: {clip_duration}')

            #TODO: Look into using ImageSequenceClip with fade in and fade out
            image_clips = []

            # Add the cover image
            cover_image_clip = mp.ImageClip(first_image(first_cover_image,item.listing_type,item.agency_logo,item.property_type,item.price,item.yearly_monthly,item.property_location), duration=INTRO_CLIP_DURATION)
            image_clips.append(cover_image_clip)

            zoom_range = np.linspace(1, 2, 400)

            for index, img_path in enumerate(images):
                image_clip = mp.ImageClip(self._process_image(img_path))

                # Loop through the zoom range and create the frames
                frames = []
                for zoom in zoom_range:
                    # Define the transformation matrix
                    M = cv2.getRotationMatrix2D((image_clip.size[0]/2, image_clip.size[1]/2), 0, zoom)
                    
                    # Apply the transformation to the image
                    zoomed_img = cv2.warpAffine(np.array(image_clip.img), M, OUTPUT_SIZE)
                    
                    # Append the zoomed image to the list of frames
                    frames.append(zoomed_img)

                # Create a video clip from the frames with a duration of image_duration seconds
                if index % 2 == 0:
                    zoomed_image_clip = mp.ImageSequenceClip(frames, fps=25).set_duration(math.ceil(clip_duration))
                else:
                    zoomed_image_clip = mp.ImageSequenceClip(frames, fps=25).set_duration(math.floor(clip_duration))

                # Creating the text clip and color clip
                text_clip = mp.TextClip(
                    txt=f"AED {item.price} \n {item.property_location} , {item.bedroom} Beds, {item.bathroom} Baths with area {item.area} sqft",
                    size=(.7*image_clip.size[0], 0.09*image_clip.size[1]),
                    font="./Roboto-Medium.ttf",
                    color="white"
                )
                text_clip = text_clip.set_position('center')

                # Color clip with some padding on top of the text clip
                im_width, im_height = text_clip.size
                color_clip = mp.ColorClip(size=(int(im_width*1.1), int(im_height*1.4)),
                        color=(0, 0, 0))
                
                color_clip = color_clip.set_opacity(0.6)
                clip_to_overlay = mp.CompositeVideoClip([color_clip, text_clip])
                clip_to_overlay = clip_to_overlay.set_position('bottom')

                # Paste logo on every image
                logo_img = Image.open("smartagent.png").resize((180,48))
                logo_img.save("logo.png")
                logo = mp.ImageClip("logo.png").set_position((1010,2))

                # Overlaying the text clip on the image clip
                image_text_clip = mp.CompositeVideoClip([zoomed_image_clip, clip_to_overlay,logo])

                # Setting the duration of the image clip
                image_text_clip = image_text_clip.set_duration(clip_duration)
                image_clips.append(image_text_clip)

            last_image_clip = mp.ImageClip(last_img(last_cover_image,item.agent_img,item.agency_logo,item.agent_name,item.agent_designation,item.contact_no,item.email_address),duration=INTRO_CLIP_DURATION)


            last_image_clip = last_image_clip.fx(mp.vfx.fadein, duration=INTRO_CLIP_DURATION*0.4)
            image_clips.append(last_image_clip)
            return mp.concatenate_videoclips(image_clips)

        
        def create_video(self):
            
            # 1. Generate Captions
            print("Generating Captions...")
            captions = self._get_captions()
            print("Captions: ", captions)

            # 2. Generate Voiceover from captions
            print("Generating Voiceover...")
            voiceover_text = self._get_voiceover_text(captions)
            print("Voiceover text: ", voiceover_text)
            
            # 3. Create Audio from voiceover text
            print("Creating Voiceover Audio...")
            self._create_voiceover_audio(voiceover_text)

            # 4. Process and merge voiceover audio with ambient audio
            print("Processing Audio...")
            self._process_audio_clips()

            # 5. Generate video from images
            print("Generating Video...")
            audio_clip_duration = mp.AudioFileClip(AUDIO_FILE_NAME).duration
            video_clip = self._generate_image_clips(
                
                # cover_image=self.listing_data['intro_image'],
                # last_image=self.listing_data['last_image'],
                images=self.listing_data['images'],
                clip_duration=(audio_clip_duration/self.num_images)
            )

            # 6. Add audio to video
            print("Adding Audio to Video...")
            video_clip = video_clip.set_audio(mp.AudioFileClip(MERGED_AUDIO_FILE_NAME))

            # 7. Write video to file
            print("Writing Video to File...")
            video_clip.write_videofile("output_video.mp4", codec=CODEC, fps=self.fps)
    
    sample_listing_data = {
                                "intro_image": "background.jpg",
                                "last_image": "background.jpg",
                                "images": img_list
                            }

    listing_video_generator = ListingVideoGenerator(sample_listing_data)
    listing_video_generator.create_video()


    # Open the video file and read its contents
    with open("output_video.mp4", mode="rb") as file:
        video = file.read()

    # Create a response with the video data and the "video/mp4" media type
    response = Response(content=video, media_type="video/mp4")

    # Set the Content-Disposition header to "attachment" to force a download dialog
    response.headers["Content-Disposition"] = "attachment"

    # Return the response
    return response

