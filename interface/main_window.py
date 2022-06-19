import os
import sys
import tkinter as tk
import logging
from threading import Thread
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ping import ping
from utils.ping import ping_of_death

# Create UI class.
class UserInterface():
    """
    Class that serves as a the frontend for all of the programs user interactable functions.
    """
    def __init__(self) -> None:
        # Create class variables and objects.
        self.logger = logging.getLogger(__name__)
        self.window_is_open = True
        self.grid_size = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        self.font = "antiqueolive"
        self.window = None
        self.text_box  = None
        self.username_entry = None
        self.password_entry = None
        self.list = None
        self.ip_list = []

        # Open log file for displaying in console window.
        self.log_file = open("latest.log", "r", encoding="utf-8")

    def initialize_window(self) -> None:
        """
        Creates and populates all US windows and components.

        Parameters:
        -----------
            None

        Returns:
        --------
            Nothing
        """
        self.logger.info("Initializing window...")

        # Create new tk window.
        self.window = tk.Tk()
        # Set window closing actions.
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        # Set window title.
        self.window.title("Mostly Universal Switch Configurator")
        # Set window to the front of others.
        self.window.attributes("-topmost", True)
        self.window.update()
        self.window.attributes("-topmost", False)

        # Setup window grid layout.
        self.window.rowconfigure(self.grid_size, weight=1, minsize=50)
        self.window.columnconfigure(self.grid_size, weight=1, minsize=50)

        #######################################################################
        #               Create window components.
        #######################################################################
        # Create frame for title block.
        title_frame = tk.Frame(master=self.window, relief=tk.GROOVE, borderwidth=3)
        title_frame.grid(row=0, columnspan=10, sticky=tk.NSEW)
        title_frame.columnconfigure(0, weight=1)
        # Create frame for loading and config switch section.
        load_switch_config_frame = tk.Frame(master=self.window, relief=tk.GROOVE, borderwidth=3)
        load_switch_config_frame.grid(row=1, rowspan=8, columnspan=5, sticky=tk.NSEW)
        load_switch_config_frame.rowconfigure(self.grid_size, weight=1)
        load_switch_config_frame.columnconfigure(self.grid_size, weight=1)
        # Create frame for entering user login creds.
        creds_frame = tk.Frame(master=self.window, relief=tk.GROOVE, borderwidth=3)
        creds_frame.grid(row=9, columnspan=5, sticky=tk.NSEW)
        creds_frame.rowconfigure(self.grid_size, weight=1)
        creds_frame.columnconfigure(self.grid_size, weight=1)
        # Create frame for entering quick command.
        quick_push_frame = tk.Frame(master=self.window, relief=tk.GROOVE, borderwidth=3)
        quick_push_frame.grid(row=1, rowspan=5, column=5, columnspan=5, sticky=tk.NSEW)
        quick_push_frame.rowconfigure(self.grid_size, weight=1)
        quick_push_frame.columnconfigure(self.grid_size, weight=1)
        # Create frame for console output
        console_frame = tk.Frame(master=self.window, relief=tk.SUNKEN, borderwidth=15, background="black")
        console_frame.grid(row=6, rowspan=4, column=5, columnspan=5, sticky=tk.NSEW)
        console_frame.rowconfigure(self.grid_size, weight=1)
        console_frame.columnconfigure(self.grid_size, weight=1)
        
        # Populate title frame.
        greeting = tk.Label(master=title_frame, text="Welcome to the Switch Configurator!", font=(self.font, 18))
        greeting.grid()

        # Populate loading config frame.
        load_config_title = tk.Label(master=load_switch_config_frame, text="Comprehensive Configure", width=10, height=1, font=(self.font, 20))
        load_config_title.grid(row=0, columnspan=len(self.grid_size), sticky=tk.EW)
        self.text_box = tk.Text(master=load_switch_config_frame, width=10, height=5)
        self.text_box.grid(row=1, rowspan=9, columnspan=9, sticky=tk.NSEW)
        button = tk.Button(master=load_switch_config_frame, text="Pull Configs", foreground="black", background="white", command=self.read_configs_button_callback)
        button.grid(row=1, rowspan=9, column=9, sticky=tk.NSEW)

        # Populate login creds frame.
        creds_title = tk.Label(master=creds_frame, text="Login Credentials", font=(self.font, 18))
        creds_title.grid(row=0, column=0, sticky=tk.NSEW)
        username_label = tk.Label(master=creds_frame, text="Username:")
        username_label.grid(row=5, column=3, sticky=tk.NSEW)
        self.username_entry = tk.Entry(master=creds_frame, width=10)
        self.username_entry.grid(row=5, column=4, sticky=tk.NSEW)
        password_label = tk.Label(master=creds_frame, text="Password:")
        password_label.grid(row=5, column=5, sticky=tk.NSEW)
        self.password_entry = tk.Entry(master=creds_frame, show="*", width=10)
        self.password_entry.grid(row=5, column=6, sticky=tk.NSEW)

        # Populate console frame.
        self.list = tk.Listbox(master=console_frame, background="black", foreground="green", highlightcolor="green")
        self.list.grid(rowspan=10, columnspan=10, sticky=tk.NSEW)

    def read_configs_button_callback(self) -> None:
        """
        This function is triggered everytime the Read Configs button is pressed. The process for this button click triggers
        a ping to all given devices, a new ssh session for each devices, and a configuration read for each one.

        Parameters:
        -----------
            None
        
        Returns:
        --------
            Nothing
        """
        # Print status to console.
        self.logger.info("\n---------------------------------------------------------\nPulling switch configs now...\n---------------------------------------------------------")

        # Get text from textbox.
        text = self.text_box.get('1.0', tk.END).splitlines()
        # Ping each switch listed in the textbox to get a list containing their status.
        Thread(target=ping_of_death, args=(text, self.ip_list,)).start()
        # Open a new ssh session for each one.
        # Pull config.

    def update_window(self) -> None:
        """
        Update the windows UI components and values.

        Parameters:
        -----------
            None

        Returns:
        --------
            Nothing
        """
        # Update the console window with the log text.
        where = self.log_file.tell()
        line = self.log_file.readline()
        if not line:
            self.log_file.seek(where)
        else:
            self.list.insert(0, line)

        # Call window event loop.
        self.window.update()

    def close_window(self) -> None:
        """
        This method is called when the main window closes.
        """
        # Print info.
        self.logger.info("Main window exit action has been invoked. Performing closing actions.")

        # Set bool value.
        self.window_is_open = False
        # Close window.
        self.window.destroy()

    def get_is_window_open(self) -> bool:
        """
        Returns if the window is still open and running.

        Parameters:
        -----------
            None

        Returns:
        --------
            Nothing
        """
        return self.window_is_open
