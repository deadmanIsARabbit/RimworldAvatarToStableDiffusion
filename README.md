# RimworldAvatarToStableDiffusion
Configurable Python script and executable to connect to a (local) Stable Diffusion WebUi instance

## What does it do
This is a simple Python script based on the work of [Saiphe](https://steamcommunity.com/id/saipheblue) and [Pat](https://steamcommunity.com/profiles/76561198174973085) to pass the avatars created by the RimWorld Avatar Mod to a (local) Stable Diffusion instance and create higher resolution images. 

At this point I have taken all the work done by [Pat](https://steamcommunity.com/profiles/76561198174973085) and [Saiphe](https://steamcommunity.com/id/saipheblue) to make it a bit more configurable. So props go to both of them.

## Requirements
* A Stable Diffusion Instance
  * You can run a local one. (Regardless of which of the following two Stable Diffusion installations you run, always add  `--api` to the COMMANDLINE_ARGS in the `webui-user.bat`) 
  * nVidia Users can use [AUTOMATIC1111](https://github.com/AUTOMATIC1111/stable-diffusion-webui)s 
  * AMD Users should use the [lshqqytiger](https://github.com/lshqqytiger/stable-diffusion-webui-amdgpu) fork and follow [this](https://github.com/CS1o/Stable-Diffusion-Info/wiki/Webui-Installation-Guides#amd-forge-webui-with-zluda) guide
* Python 3
    * onnxruntime `pip install onnxruntime`
    * rembg `pip install rembg`
    * PIL `pip install pillow`
    * urlLib `pip install urllib`

## Installation
1. Simply download the executable and the config file from the releases.
2. Edit the config file to meet your desired Stable Diffusion processing settings.
3. Start RimWorld and go into the settings of the avatar mod. Put the full path of the executablein the last text field.

## Usage
The script is written in such a way that you do not have to interact with it if the configuration file is completely filled out. 
However, if you want to change parameters during runtime, you can leave out lines in the configuration, you will then be asked for the desired option when generating the image (except for the webui_server_url, because why)
