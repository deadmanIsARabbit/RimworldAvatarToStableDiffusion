# RimworldAvatarToStableDiffusion
Configurable Python script and executable to connect to a (local) Stable Diffusion WebUi instance

## What does it do
This is a simple Python script based on the work of [Saiphe](https://steamcommunity.com/id/saipheblue) and [Pat](https://steamcommunity.com/profiles/76561198174973085) to pass the avatars created by  [bolphens RimWorld Avatar Mod](https://steamcommunity.com/profiles/76561199575793319/myworkshopfiles/?appid=294100) to a (local) Stable Diffusion instance and create higher resolution images. 

At this point I have taken all the work done by [Pat](https://steamcommunity.com/profiles/76561198174973085) and [Saiphe](https://steamcommunity.com/id/saipheblue) to make it a bit more configurable. So props go to both of them and [bolphen](https://steamcommunity.com/profiles/76561199575793319) for this awesome mod. 

## Requirements
* A Stable Diffusion Instance
  * You can run a local one. (Regardless of which of the following two Stable Diffusion installations you run, always add  `--api` to the COMMANDLINE_ARGS in the `webui-user.bat`) 
  * nVidia Users can use [AUTOMATIC1111](https://github.com/AUTOMATIC1111/stable-diffusion-webui)s 
  * AMD Users should use the [lshqqytiger](https://github.com/lshqqytiger/stable-diffusion-webui-amdgpu) fork and follow [this](https://github.com/CS1o/Stable-Diffusion-Info/wiki/Webui-Installation-Guides#amd-forge-webui-with-zluda) guide
* Rimworld
* [bolphens Avatar Mod](https://steamcommunity.com/sharedfiles/filedetails/?id=3111373293)
* Python 3 (to build the executable yourself or to run the python script directly)
    * onnxruntime `pip install onnxruntime`
    * rembg `pip install rembg`
    * PIL `pip install pillow`
    * urlLib `pip install urllib`

## Installation
1. Simply download the executable and the config file from the releases.
2. Edit the config file to meet your desired Stable Diffusion processing settings.
3. Start RimWorld and go into the settings of the [avatar mod](https://steamcommunity.com/sharedfiles/filedetails/?id=3111373293). Put the full path of the executable in the last text field.

## Usage
The script is written in such a way that you do not have to interact with it if the configuration file is completely filled out. 
However, if you want to change parameters during runtime, you can comment out parameters in the configuration, you will then be asked for the desired option when generating the image (except for the webui_server_url, because why)

## Build
If you want to build this yourself simply run
`pyinstaller --noconfirm --onefile --console  "Avatar2SD.py"` from the directory containing the  `Avatar2SD.py`
