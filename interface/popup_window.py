import tkinter as tk

def text_popup(text) -> None:
    """
    This function opens a new read-only text editor window. This window simply displays the given text.

    Parameters:
    -----------
        text - The text to be displayed in the new window.

    Returns:
    --------
        Nothing
    """
    # Create new tk window.
    popup_window = tk.Tk()
    # Set window title.
    popup_window.title("Command Output")
    # Set window to the front of others.
    popup_window.attributes("-topmost", True)
    popup_window.update()
    popup_window.attributes("-topmost", False)
    # Set sizing weights.
    popup_window.grid_rowconfigure(0, weight=1)
    popup_window.grid_columnconfigure(0, weight=1)

    # Setup window grid layout.
    grid_size = list(range(10))
    popup_window.rowconfigure(grid_size, weight=1, minsize=60)
    popup_window.columnconfigure(grid_size, weight=1, minsize=70)
    # Populate upload config frame.
    text_box = tk.Text(master=popup_window, width=10, height=5)
    text_box.grid(row=0, rowspan=10, column=0, columnspan=10, sticky=tk.NSEW)
    # Add a Scrollbar.
    scroll=tk.Scrollbar(master=popup_window, orient='vertical', command=text_box.yview)
    scroll.grid(row=0, rowspan=10, column=10, sticky=tk.NS)
    # Link scroll value back to text box.
    text_box['yscrollcommand'] = scroll.set
    # Fill textbox with output text.
    text_box.insert(tk.INSERT, text)
    # Update window.
    popup_window.update()