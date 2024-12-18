from datetime import datetime
import urllib.request
import base64
import json
import time
import sys
import os
import configparser
from rembg import remove
from PIL import Image, ImageOps, ImageChops
from operator import itemgetter

#Read the config file
config = configparser.ConfigParser()
config.read('Avatar2SD.ini')
webui_server_url = config['DEFAULT']['webui_server_url']
def getOptionOrInput(option, type, help):
    if option in config['DEFAULT']:
        return config['DEFAULT'][option]
    else: 
        print("There is no default value set for " + option)
        print("Hint:")
        print(help)
        option_value = input("Enter the "+ option+ " as "+ str(type))
        return option_value

#Get all options except webui_server_url
opt_fill_color = getOptionOrInput('fill_color', eval, 'Fill Color for the background of the image as comma seperated RGB')
opt_border_width = getOptionOrInput('border_width', int, 'The number of pixel to be removed from the image border')
opt_best_prompt =  getOptionOrInput('best_prompt', str, 'Prompt to be appended before the input prompt from RimWorlds Avatar Mod')
opt_seed = getOptionOrInput('seed', int, 'Seed to be used. -1 shall be random. I guess.')
opt_steps = getOptionOrInput('steps', int, 'Sampling Steps. How many times to improve the generated image iteratively. higher values take longer#very low values can produce bad results')
opt_denoising_strength = getOptionOrInput('denoising_strength', float, 'Determines how little respect the algorithm should have for image`s content. At 0, nothing will change, and at 1 you`ll get an unrelated image. With values below 1.0, processing will take less steps than the Sampling Steps specifies.')
opt_n_iter = getOptionOrInput('n_iter', int, 'Number of denoising iterations')
opt_width = getOptionOrInput('width', int, 'SD image width in px')
opt_height = getOptionOrInput('height', int, 'SD image height in px')
opt_batch_size = getOptionOrInput('batch_size', int, 'How many image to create in a single batch')
opt_sampler_name = getOptionOrInput('sampler_name', str, 'Algorithm to use to produce the image')

def trim(im):
    bg = Image.new(im.mode, im.size, im.getpixel((0,0)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)
 
def timestamp():
    return datetime.fromtimestamp(time.time()).strftime("%Y%m%d-%H%M%S")
 
def encode_file_to_base64(path):
    with open(path, 'rb') as file:
        return base64.b64encode(file.read()).decode('utf-8')

def decode_and_save_base64(base64_str, save_path):
    try:
        decoded_data = base64.b64decode(base64_str)
        with open(save_path, "wb") as file:
            file.write(decoded_data)
        #Open image
        image_input = Image.open(save_path)
        #Saves copied image into backup folder. Backup image gets replaced 
        #by the next portrait generation of the colonist, so be careful
        copy_image_input = image_input.copy()
        backup_path = save_path.replace("avatar", "avatar\\BackupImages")
        copy_image_input.save(backup_path)
        #Fill is white
        fill_color = opt_fill_color
        #Add white border
        image_input = ImageOps.expand(image_input,border=opt_border_width,fill=fill_color)
        #Removes background
        output = remove(image_input)
        #Removes white border that .expand() added
        output = trim(output)
        #Saves final output image
        output.save(save_path)
        print("Image saved successfully:", save_path)
    except Exception as e:
        print("Error saving image:", e)
 
def call_api(api_endpoint, **payload):
    data = json.dumps(payload).encode('utf-8')
    request = urllib.request.Request(
        f'{webui_server_url}/{api_endpoint}',
        headers={'Content-Type': 'application/json'},
        data=data,
    )
    response = urllib.request.urlopen(request)
    return json.loads(response.read().decode('utf-8'))

def get_data_from_api(api_endpoint):
    response = urllib.request.urlopen( f'{webui_server_url}/{api_endpoint}')
    data = json.load(response)   
    return data 

def get_Models():
    models = get_data_from_api('sdapi/v1/sd-models')
    selection_list = []
    selection_index = 1 
    for val in models:
        #print(val)
        selection_list.insert(selection_index, val)
        selection_index = selection_index + 1
    return selection_list

def select_Model(array):
    print("Choose Your Model:")
    for  index, val in enumerate(array):
        print("Press "+str(index)+" for "+val['title'])
    selected = int(input("Enter an integer: "))
    return array[selected]['model_name']

def call_img2img_api(init_image_path, prompt):
    #This is my altered prompt from Saiphe's work, (no background:1:1) encourages a white background I believe, which works well with
    #adding the white border and rembg(ing) the image (The automatic background remover library this code uses)
    #The reason for the white border adder, is the rembg would often remove sholders in inconsistent ways, most often when colonist has
    #long hair that would separate a should from the rest of the body in the image
    final_prompt = opt_best_prompt + " " + prompt
    if 'model_name' in config['DEFAULT']:
        model = config['DEFAULT']['model_name']
    else: 
        #Get the available models
        models = get_Models()
        model = select_Model(models)
    #override_settings: I used model aamXLAnimeMix_v10 from civitai for testing
    payload = {
        "prompt": final_prompt,
        "seed": opt_seed,
        "steps": opt_steps,
        "width": opt_width,
        "height": opt_height,
        "denoising_strength": opt_denoising_strength,
        "n_iter": opt_n_iter,
        "init_images": [encode_file_to_base64(init_image_path)],
        "batch_size": opt_batch_size,
        "sampler_name": opt_sampler_name,
        "override_settings": {
             'sd_model_checkpoint': model,# Enter your model name if you wish to change from default
         },
    }
    response = call_api('sdapi/v1/img2img', **payload)
    generated_image = response.get('images')[0]
    decode_and_save_base64(generated_image, init_image_path)
    #rembg()
    sys.exit()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python script.py <image_path> <prompt>")
        sys.exit(1)
 
    image_path = sys.argv[1]
    prompt = sys.argv[2]
 
    call_img2img_api(image_path, prompt)