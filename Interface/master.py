# Import required packages.
import tkinter as tk
import logging

# Create UI class.
class UserInterface():
    def __init__(self) -> None:
        pass

    def Initialize_Window(self) -> None:
        print("Initializing window...")

        # Create new tk window.
        window = tk.Tk()

        # Create window components.
        greeting = tk.Label(text="Welcome to the Switch Configurator!")
        # Add window components.
        greeting.pack()
