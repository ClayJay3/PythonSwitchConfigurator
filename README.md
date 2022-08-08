# PythonSwitchConfigurator
It's universal, but probably only works for cisco switches. This project is an attempt to create a convenient GUI for the simple configuration of network switches. It can also export network maps through the auto discover feature.
![main](https://user-images.githubusercontent.com/26121134/183433953-9598a36e-403a-4e54-bbb5-ea6343cb4dcf.PNG)
![config](https://user-images.githubusercontent.com/26121134/183433978-dff9b10a-c5df-4524-9f28-439378d851be.png)
![map](https://user-images.githubusercontent.com/26121134/183434476-88a4cb9c-7d72-4736-884f-e2333090d7e3.PNG)
![mapinfo](https://user-images.githubusercontent.com/26121134/183434021-c08c2dfa-0dbc-47bc-a8b3-e8348ee57afe.png)

```diff
-RUN WITH CAUTION. YOU CAN EASILY MESS UP A SWITCH'S CONFIG WITH THIS PROGRAM.-
```

## Install
This python program has been compiled with pyinstaller, which turns python code into a .exe file. It includes all dependencies and a python 3.8.10 installation in the executable, so no third-party application need to be installed.
  1) Download the latest release.
      - onefile.zip offers a more simplistic application executable, but runs at a slower speed. This is because the whole application and its dependencies are compiled
        into a single file.
      - onefolder.zip offers faster execution, but the application directory is more cluttered.
  2) Copy a shortcut to the desktop and open the program.

## Compile
If your wanting to make code changes or just want the latest build, you'll need to setup the pip environment and use pyinstaller to recompile the executable.
### Environment Setup and Build
  1) Clone/download and unzip the project 
  2) Install the pip environment
      - Navigate to the project directory
      - Install the pip environment ```pipenv install```
      - Enter the pip environment ```pipenv shell```
  3) Run [PyInstaller](https://pyinstaller.org/en/stable/) using the command-line or by running the included script.
      - Click on the settings drop-down and import the pyinstaller.json file located in this project's root directory. This will import all the necessary settings for           compiling.
      - Select whether you want to build the program to onefile or onefolder and choose an output directory.
      - Click "convert .py to .exe"
      - Once the program has finished compiling, copy the logging_config.yaml file into the output directory.
      
### More Info
All actions, warnings, and errors are saved to a timestamped logs folder in the root directory of the appliction. If the program crashes or does something unexpected, please open a new issue here on github and include the log in the issue.

When using the Auto Discover feature on the main application window, you are asked if you want to save the discovered switch data. If you select yes, then the data will be saved to an exports folder in the project root directory.
