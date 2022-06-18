# Import required packages.
from cgitb import text
from cmath import exp
from concurrent.futures.process import _system_limits_checked
import tkinter as tk
import logging

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
        # Set window size ratio.
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        self.window.geometry(f"550x400+{int(screen_width / 2 - 275)}+{int(screen_height / 2 - 125)}")
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
        text_box = tk.Text(master=load_switch_config_frame, width=10, height=5)
        button = tk.Button(master=load_switch_config_frame, text="Pull Configs", foreground="black", background="white")
        load_config_title.grid(row=0, columnspan=len(self.grid_size), sticky=tk.EW)
        text_box.grid(row=1, rowspan=9, columnspan=9, sticky=tk.NSEW)
        button.grid(row=1, rowspan=9, column=9, sticky=tk.NSEW)

        # Populate login creds frame.
        creds_title = tk.Label(master=creds_frame, text="Login Credentials", font=(self.font, 18))
        creds_title.grid(row=0, column=0, sticky=tk.NSEW)
        username_label = tk.Label(master=creds_frame, text="Username:")
        username_label.grid(row=5, column=3, sticky=tk.NSEW)
        username_entry = tk.Entry(master=creds_frame, width=10)
        username_entry.grid(row=5, column=4, sticky=tk.NSEW)
        password_label = tk.Label(master=creds_frame, text="Password:")
        password_label.grid(row=5, column=5, sticky=tk.NSEW)
        password_entry = tk.Entry(master=creds_frame, show="*", width=10)
        password_entry.grid(row=5, column=6, sticky=tk.NSEW)


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
        # Call window event loop.
        self.window.mainloop()

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
