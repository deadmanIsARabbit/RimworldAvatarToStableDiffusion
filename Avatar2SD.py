#!/usr/bin/env python3

import os, sys

import urllib.request
import urllib.parse
import json
from configparser import ConfigParser
#from rembg import remove


#Read the config file

def readConfig():
    home_dir = os.path.expanduser("~")
    win_path = home_dir + "\\AppData\\LocalLow\\Ludeon Studios\\RimWorld by Ludeon Studios\\avatar\\Avatar2SD.ini"
    linux_path = home_dir + "/.config/unity3d/Ludeon Studios/RimWorld by Ludeon Studios/avatar/Avatar2SD.ini"
    if os.path.exists(linux_path):
        cfg = linux_path
    elif os.path.exists(win_path):
        cfg = win_path
    else:
        print("Config file not found")
        exit
    config = ConfigParser()
    print(cfg)
    config.read(cfg)
    return config

def getOptionOrInput(option, returntype, help):
    if option in config['DEFAULT']:
        return returntype(config['DEFAULT'][option])
    else: 
        print("There is no default value set for " + option)
        print("Hint:")
        print(help)
        option_value = input("Enter a value for "+ option+ " as "+ str(returntype))
        return returntype(option_value)

#WebUI relevant functions
def trim(im):
    bg = Image.new(im.mode, im.size, im.getpixel((0,0)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)

def encode_file_to_base64(path):
    with open(path, 'rb') as file:
        return b64encode(file.read()).decode('utf-8')

def decode_and_save_base64(base64_str, save_path):
    try:
        decoded_data = b64decode(base64_str)
        with open(save_path, "wb") as file:
            file.write(decoded_data)
        #Open image
        image_input = Image.open(save_path)
        #Saves copied image into backup folder. Backup image gets replaced 
        #by the next portrait generation of the colonist, so be careful
        copy_image_input = image_input.copy()
        backup_path = save_path.replace("avatar", "avatar\\BackupImages")
        backup_dir = os.path.dirname(os.path.abspath(backup_path))
        if not os.path.exists(backup_dir):
             os.makedirs(backup_dir)
        copy_image_input.save(backup_path)
        #Add white border
        image_input = ImageOps.expand(image_input,border=int(opt_border_width),fill=eval(opt_fill_color))
        #Removes background
        output = remove(image_input)
        #Removes white border that .expand() added
        output = trim(output)
        #Saves final output image
        output.save(save_path+".tmp.png")
        os.replace(save_path+".tmp.png", save_path)
        print("Image saved successfully:", save_path)
    except Exception as e:
        print("Error saving image:", e)
        print(format_exc())
 
def call_api(api_endpoint, **payload):
    data = dumps(payload).encode('utf-8')
    request = urllib.request.Request(
        f'{server_address}/{api_endpoint}',
        headers={'Content-Type': 'application/json'},
        data=data,
    )
    response = urllib.request.urlopen(request)
    return loads(response.read().decode('utf-8'))

def get_data_from_api(api_endpoint):
    response = urllib.request.urlopen( f'{server_address}/{api_endpoint}')
    return load(response) 

def get_Models():
    models = get_data_from_api('sdapi/v1/sd-models')
    selection_list = []
    for val in models:
        selection_list.append(val)
    return selection_list

def select_Model(array):
    print("Choose Your Model:")
    for  index, val in enumerate(array):
        print("Press "+str(index)+" for "+ str(val['title']))
    selected = int(input("Enter an integer: "))
    return array[selected]['model_name']

def call_img2img_api(init_image_path, prompt):
    #This is my(Pat) altered prompt from Saiphe's work, (no background:1:1) encourages a white background I believe, which works well with
    #adding the white border and rembg(ing) the image (The automatic background remover library this code uses)
    #The reason for the white border adder, is the rembg would often remove sholders in inconsistent ways, most often when colonist has
    #long hair that would separate a should from the rest of the body in the image
    if opt_prompt_delimiter in prompt:
        pos_prompt = prompt.split(opt_prompt_delimiter)[0]
        neg_prompt = prompt.split(opt_prompt_delimiter)[1]
    else:
        pos_prompt = prompt
        neg_prompt = ''
    final_pos_prompt = opt_positive_prompt + " " + pos_prompt
    final_neg_prompt = opt_negative_prompt + " " + neg_prompt 
    if 'model_name' in config['DEFAULT']:
        model = config['DEFAULT']['model_name']
    else: 
        #Get the available models
        models = get_Models()
        model = select_Model(models)
    #override_settings: I used model aamXLAnimeMix_v10 from civitai for testing
    print('We are using this prompt: ' + final_pos_prompt)
    print('With this negative prompt: ' + final_neg_prompt)
    print('And this model:' + model)
    payload = {
        "prompt": final_pos_prompt,
        "negative_prompt": final_neg_prompt,
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
    sys.exit(0)

#ComfyUI relevant functions

# ---------------------------------------------------------------------------------------------------------------------
# Establish Connection

def open_websocket_connection():

  client_id=str(uuid.uuid4())
  ws = websocket.WebSocket()
  ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
  print("Verbunden mit", server_address)
  return ws, server_address, client_id

# ---------------------------------------------------------------------------------------------------------------------
# Basic API calls

def queue_prompt(prompt, client_id, server_address):
  p = {"prompt": prompt, "client_id": client_id}
  headers = {'Content-Type': 'application/json'}
  data = json.dumps(p).encode('utf-8')
  req =  urllib.request.Request("http://{}/prompt".format(server_address), data=data, headers=headers)
  return json.loads(urllib.request.urlopen(req).read())



def get_history(prompt_id, server_address):
  with urllib.request.urlopen("http://{}/history/{}".format(server_address, prompt_id)) as response:
      return json.loads(response.read())

def get_image(filename, subfolder, folder_type, server_address):
  data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
  url_values = urllib.parse.urlencode(data)
  with urllib.request.urlopen("http://{}/view?{}".format(server_address, url_values)) as response:
      return response.read()

def upload_image(input_path, name, server_address, image_type="input", overwrite=False):
  with open(input_path, 'rb') as file:
    multipart_data = MultipartEncoder(
      fields= {
        'image': (name, file, 'image/png'),
        'type': image_type,
        'overwrite': str(overwrite).lower()
      }
    )

    data = multipart_data
    headers = { 'Content-Type': multipart_data.content_type }
    request = urllib.request.Request("http://{}/upload/image".format(server_address), data=data, headers=headers)
    with urllib.request.urlopen(request) as response:
      return response.read()

# -------------------------------------------------------------------------------------------------------
# API helper

def generate_image_by_prompt_and_image(prompt, output_path, input_path, filename, save_previews=False):
  try:
    ws, server_address, client_id = open_websocket_connection()
    upload_image(input_path, filename, server_address, "input", True)
    print(prompt)
    prompt_id = queue_prompt(prompt, client_id, server_address)['prompt_id']
    track_progress(prompt, ws, prompt_id)
    images = get_images(prompt_id, server_address, save_previews)

    save_image(images, output_path, save_previews)
  finally:
    ws.close()

def save_image(images, output_path, save_previews):
    for itm in images:
        try:
            image = Image.open(io.BytesIO(itm['image_data']))
            if os.path.exists(output_path):
                os.remove(output_path)
            image.save(output_path)
        except Exception as e:
            print(f"Failed to save image {itm['file_name']}: {e}")

def track_progress(prompt, ws, prompt_id):
  node_ids = list(prompt.keys())
  finished_nodes = []

  while True:
      out = ws.recv()
      if isinstance(out, str):
          message = json.loads(out)
          if message['type'] == 'progress':
              data = message['data']
              current_step = data['value']
              print('In K-Sampler -> Step: ', current_step, ' of: ', data['max'])
          if message['type'] == 'execution_cached':
              data = message['data']
              for itm in data['nodes']:
                  if itm not in finished_nodes:
                      finished_nodes.append(itm)
                      print('Progess: ', len(finished_nodes), '/', len(node_ids), ' Tasks done')
          if message['type'] == 'executing':
              data = message['data']
              if data['node'] not in finished_nodes:
                  finished_nodes.append(data['node'])
                  print('Progess: ', len(finished_nodes), '/', len(node_ids), ' Tasks done')


              if data['node'] is None and data['prompt_id'] == prompt_id:
                  break #Execution is done
      else:
          continue
  return

def get_images(prompt_id, server_address, allow_preview = False):
  output_images = []

  history = get_history(prompt_id, server_address)[prompt_id]
  for node_id in history['outputs']:
      node_output = history['outputs'][node_id]
      output_data = {}
      if 'images' in node_output:
          for image in node_output['images']:
              if allow_preview and image['type'] == 'temp':
                  preview_data = get_image(image['filename'], image['subfolder'], image['type'], server_address)
                  output_data['image_data'] = preview_data
              if image['type'] == 'output':
                  image_data = get_image(image['filename'], image['subfolder'], image['type'], server_address)
                  output_data['image_data'] = image_data
      output_data['file_name'] = image['filename']
      output_data['type'] = image['type']
      output_images.append(output_data)

  return output_images

def load_workflow(workflow_path):
  try:
    with open(workflow_path, 'r') as file:
        workflow = json.load(file)
        return json.dumps(workflow)
  except FileNotFoundError:
      print(f"The file {workflow_path} was not found.")
      return None
  except json.JSONDecodeError:
      print(f"The file {workflow_path} contains invalid JSON.")
      return None

# ---------------------------------------------------------------------------------------------------------------
# Call API

def prompt_image_to_image(workflow, input_path, positve_prompt, negative_prompt='', save_previews=False):

  prompt = json.loads(workflow)
  id_to_class_type = {id: details['class_type'] for id, details in prompt.items()}
  k_sampler = [key for key, value in id_to_class_type.items() if value == 'KSampler'][0]
  prompt.get(k_sampler)['inputs']['seed'] = random.randint(10**14, 10**15 - 1)
  postive_input_id = prompt.get(k_sampler)['inputs']['positive'][0]
  prompt.get(postive_input_id)['inputs']['text'] = positve_prompt

  if negative_prompt != '':
    negative_input_id = prompt.get(k_sampler)['inputs']['negative'][0]
    prompt.get(negative_input_id)['inputs']['text'] = negative_prompt

  image_loader = [key for key, value in id_to_class_type.items() if value == 'LoadImage'][0]
  filename = os.path.basename(input_path)
  prompt.get(image_loader)['inputs']['image'] = filename

  generate_image_by_prompt_and_image(prompt, save_path, input_path, filename,  save_previews=False)


def split_prompt(prompt):
    if opt_prompt_delimiter in prompt:
        pos_prompt = prompt.split(opt_prompt_delimiter)[0]
        neg_prompt = prompt.split(opt_prompt_delimiter)[1]
    else:
        pos_prompt = prompt
        neg_prompt = ''

    final_prompt = []
    final_prompt.append(opt_negative_prompt + " " + neg_prompt )
    final_prompt.append(opt_positive_prompt + " " + pos_prompt)
    return final_prompt

def generate_backup():
    base_dir = Path(os.path.dirname(image_path))
    backup_dir = base_dir / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    tmp_img_name = str(datetime.datetime.now().strftime('%y%m%d%H%M%S')) + str(img_name)
    backup_dst = backup_dir / tmp_img_name
    shutil.copyfile(image_path, backup_dst)
    if opt_save_prompt == True:
        txt_name = str(img_name).split(".")[0] + ".txt"
        txt_path = base_dir / txt_name
        tmp_txt_name = tmp_img_name.split(".")[0] + ".txt"
        backup_dst = backup_dir / tmp_txt_name
        if os.path.exists(txt_path):
            shutil.copyfile(txt_path, backup_dst)
            
def save_prompt():
    base_dir = Path(os.path.dirname(image_path))
    txt_name = str(img_name).split(".")[0] + ".txt"
    txt_path =  txt_path = base_dir / txt_name
    with open(txt_path, mode="wt") as f:
        f.write(final_prompt[1] +opt_prompt_delimiter+ final_prompt[0] )
        f.flush()
        f.close
#Main Function
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python Avatar2SD.py <image_path> <prompt>")
        sys.exit(1)
    image_path = sys.argv[1]
    prompt = sys.argv[2]
    config = readConfig()
    server_address = config['DEFAULT']['server_address']
    #Get all options except server_address
    opt_provider = getOptionOrInput('provider', str, 'Choose either WebUI oder ComfyUI')
    opt_positive_prompt =  getOptionOrInput('positive_prompt', str, 'Prompt to be appended before the input prompt from RimWorlds Avatar Mod')
    opt_negative_prompt = getOptionOrInput('negative_prompt', str, 'Negative Prompts are a unique approach to guide AI by specifying what the user does not want to see, without any extra input')
    opt_prompt_delimiter = getOptionOrInput('prompt_delimiter', str, 'Define a delimiter to split the interactive prompt input from within the game into an addition postive and negative prompt')
    opt_backup = getOptionOrInput('create_backup', bool, 'Create Backup of images and prompts(later if enabled)?')
    opt_save_prompt = getOptionOrInput('save_prompt', bool, 'Save prompt to text?')
    if opt_provider == 'WebUI':
        from PIL import Image, ImageOps, ImageChops
        from traceback import format_exc
        from base64 import b64encode, b64decode  
        opt_fill_color = getOptionOrInput('fill_color', str, 'Fill Color for the background of the image as comma seperated RGB')
        opt_border_width = getOptionOrInput('border_width', int, 'The number of pixel to be removed from the image border')
        opt_seed = getOptionOrInput('seed', int, 'Seed to be used. -1 shall be random. I guess.')
        opt_steps = getOptionOrInput('steps', int, 'Sampling Steps. How many times to improve the generated image iteratively. higher values take longer#very low values can produce bad results')
        opt_denoising_strength = getOptionOrInput('denoising_strength', float, 'Determines how little respect the algorithm should have for image`s content. At 0, nothing will change, and at 1 you`ll get an unrelated image. With values below 1.0, processing will take less steps than the Sampling Steps specifies')
        opt_n_iter = getOptionOrInput('n_iter', int, 'Number of denoising iterations')
        opt_width = getOptionOrInput('width', int, 'SD image width in px')
        opt_height = getOptionOrInput('height', int, 'SD image height in px')
        opt_batch_size = getOptionOrInput('batch_size', int, 'How many image to create in a single batch')
        opt_sampler_name = getOptionOrInput('sampler_name', str, 'Algorithm to use to produce the image')
    else: 
        from pathlib import Path
        import shutil
        import datetime
        import io
        import uuid
        from requests_toolbelt import MultipartEncoder
        import random
        import websocket
        from PIL import Image, ImageOps, ImageChops
        opt_workflow_path = getOptionOrInput('workflow_path', str, 'Path of the Workflow to be used by ComfyUI (including filename)')

    if opt_provider == 'WebUI':
        call_img2img_api(image_path, prompt)
    else: 
        final_prompt = split_prompt(sys.argv[2])
        image_path = Path(sys.argv[1])
        img_name = os.path.basename(image_path)
        global save_path
        save_path = image_path
        print(type(opt_save_prompt))
        if opt_backup == True:
            generate_backup()
        if opt_save_prompt == True:
            save_prompt()
        workflow = load_workflow(Path(opt_workflow_path))
        prompt_image_to_image(workflow, image_path, final_prompt[1], final_prompt[0], save_previews=False)
        # sys.exit(0) 