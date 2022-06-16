# Import required packages.
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
        # TODO set window to open on top.
        # TODO set other window attribs like title, width, and height. look up others.

        # Create window components.
        greeting = tk.Label(text="Welcome to the Switch Configurator!")
        # Add window components.
        greeting.pack()

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
