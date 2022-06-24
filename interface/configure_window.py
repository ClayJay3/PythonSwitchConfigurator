import logging
import tkinter as tk
from threading import Thread
from typing import Tuple

from utils.open_connection import ssh_autodetect_switchlist_info


# Create Configure UI window class.
class ConfigureUI:
    """
    Class that serves as frontend for all of the individual switch configure.
    """
    def __init__(self) -> None:
        # Create class variables and objects.
        self.logger = logging.getLogger(__name__)
        self.window = None
        self.window_is_open = False
        self.window_is_initialized = False
        self.retrieving_devices = False
        self.grid_size = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        self.font = "antiqueolive"
        self.username = None
        self.password = None
        self.ip_list = []
        self.ssh_connections = []
        self.devices = []
        self.switch_selection = None
        self.drop_down = None

    def run(self, ips, username, password):
        """
        Call this function to start UI window in a new thread.
        """
        # Set ip list var.
        self.ip_list = ips
        # Set username and password var.
        self.username = username
        self.password = password
        # Set window is open.
        self.window_is_open = True

    def initialize_window(self) -> None:
        """
        Creates and populates all MainUI windows and components.

        Parameters:
        -----------
            ips - The list containing ip and hostname status of each devices.

        Returns:
        --------
            Nothing
        """
        # Print logger info.
        self.logger.info("Initializing configuration window...")

        # Create new tk window.
        self.window = tk.Tk()
        # Set window closing actions.
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        # Set window title.
        self.window.title("Switch Config")
        # Set window to the front of others.
        self.window.attributes("-topmost", True)
        self.window.update()
        self.window.attributes("-topmost", False)

        # Set window variables.
        self.switch_selection = tk.StringVar(self.window)
        self.switch_selection.set("No switch is selected")

        # Setup window grid layout.
        self.window.rowconfigure(self.grid_size, weight=1, minsize=60)
        self.window.columnconfigure(self.grid_size, weight=1, minsize=70)

        #######################################################################
        #               Create window components.
        #######################################################################
        # Create frame for selecting which switch to connect to.
        selector_frame = tk.Frame(master=self.window, relief=tk.GROOVE, borderwidth=3)
        selector_frame.grid(row=0, column=0, columnspan=5, sticky=tk.NSEW)
        selector_frame.rowconfigure(0, weight=1)
        selector_frame.columnconfigure(0, weight=1)
        # Create frame for the quick command buttons.
        command_button_frame = tk.LabelFrame(master=self.window, text="Quick Commands", relief=tk.GROOVE, borderwidth=3)
        command_button_frame.grid(row=0, column=5, columnspan=5, sticky=tk.NSEW)
        command_button_frame.rowconfigure(0, weight=1)
        command_button_frame.columnconfigure(self.grid_size, weight=1)
        # Create frame for interface configuration.
        interface_frame = tk.LabelFrame(master=self.window, text="Interface Config", relief=tk.GROOVE, borderwidth=3)
        interface_frame.grid(row=1, rowspan=9, column=0, columnspan=4, sticky=tk.NSEW)
        interface_frame.rowconfigure(0, weight=1)
        interface_frame.columnconfigure(0, weight=1)
        # Create frame for vlan configuration.
        vlan_frame = tk.LabelFrame(master=self.window, text="VLAN Config", relief=tk.GROOVE, borderwidth=3)
        vlan_frame.grid(row=1, rowspan=9, column=4, columnspan=3, sticky=tk.NSEW)
        vlan_frame.rowconfigure(0, weight=1)
        vlan_frame.columnconfigure(0, weight=1)
        # Create frame for uploading configuration.
        upload_frame = tk.LabelFrame(master=self.window, text="Upload Config", relief=tk.GROOVE, borderwidth=3)
        upload_frame.grid(row=1, rowspan=9, column=7, columnspan=3, sticky=tk.NSEW)
        upload_frame.rowconfigure(0, weight=1)
        upload_frame.columnconfigure(0, weight=1)

        # Populate selector frame.
        self.drop_down = tk.OptionMenu(selector_frame, self.switch_selection, *self.ip_list, command=self.drop_down_callback)
        self.drop_down.grid(row=0, column=0, columnspan=7, sticky=tk.NSEW)
        write_button = tk.Button(master=selector_frame,  text="WRITE", foreground="black", background="white", command=self.write_switch_config)
        write_button.grid(row=0, column=7, columnspan=3, sticky=tk.NSEW)

        # Populate quick command frame.
        int_stat_button = tk.Button(master=command_button_frame,  text="Interface Status", foreground="black", background="white", command=self.write_switch_config)
        int_stat_button.grid(row=0, column=0, columnspan=1, sticky=tk.NSEW)
        run_config_button = tk.Button(master=command_button_frame,  text="Show Run", foreground="black", background="white", command=self.write_switch_config)
        run_config_button.grid(row=0, column=1, columnspan=1, sticky=tk.NSEW)
        log_button = tk.Button(master=command_button_frame,  text="Show Log", foreground="black", background="white", command=self.write_switch_config)
        log_button.grid(row=0, column=2, sticky=tk.NSEW)
        test_link_button = tk.Button(master=command_button_frame,  text="Test Port Link Quality", foreground="black", background="white", command=self.write_switch_config)
        test_link_button.grid(row=0, column=3, columnspan=1, sticky=tk.NSEW)
        show_int_err_button = tk.Button(master=command_button_frame,  text="Show Interface Errors", foreground="black", background="white", command=self.write_switch_config)
        show_int_err_button.grid(row=0, column=4, columnspan=1, sticky=tk.NSEW)
        clr_int_err_button = tk.Button(master=command_button_frame,  text="Clear Interface Errors", foreground="black", background="white", command=self.write_switch_config)
        clr_int_err_button.grid(row=0, column=5, columnspan=1, sticky=tk.NSEW)
        port_channel_button = tk.Button(master=command_button_frame,  text="Create Port Channel", foreground="black", background="white", command=self.write_switch_config)
        port_channel_button.grid(row=0, column=6, columnspan=1, sticky=tk.NSEW)


        # Populate upload config frame.
        text_box = tk.Text(master=upload_frame, width=10, height=5)
        text_box.grid(row=0, rowspan=9, column=0, columnspan=10, sticky=tk.NSEW)
        write_button = tk.Button(master=upload_frame,  text="Upload Config", foreground="black", background="white", command=self.write_switch_config)
        write_button.grid(row=9, column=0, columnspan=10, sticky=tk.NSEW)

        # Set window initialized flag.
        self.window_is_initialized = True

    def drop_down_callback(self, choice):
        """
        This method is called everytime a new item is selected in the dropdown menu.

        Parameters:
        -----------
            choice - This is given to us by the OptionMenu class. Not very usefull.

        Returns:
        --------
            Nothing
        """
        # Create instance variables.
        current_selected_model = None

        # Store choice.
        choice = self.switch_selection.get()
        # Split choice ip and hostname string up.
        choices = choice.split()
        selected_ip_addr = choices[0]
        selected_hostname = choices[1]

        # Open ssh connection with switch.

    def write_switch_config(self):
        """
        This method is called everytime the write button is pressed.

        Parameters:
        -----------
            None

        Returns:
        --------
            Nothing
        """
        # Write the switch config.
        pass
        
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
        # Wait until we get ip info, then initialize window.
        if not self.window_is_initialized and len(self.ip_list) > 0:# and not all(ip is None for ip in self.ip_list) and not all(ip[0] is False for ip in self.ip_list):
            # If the list does not contain tuples that store if the ping was successful then move on.
            if isinstance(self.ip_list[0], Tuple):
                # Remove all ips that are unreachable.
                ips = []
                for addr in self.ip_list:
                    if addr is not None and addr[0] is True:
                        ips.append(f"{addr[1]} {addr[2]}")

                # Print log info.
                if len(self.ip_list) - len(ips) > 0:
                    self.logger.info(f"Throwing out {len(self.ip_list) - len(ips)} of {len(self.ip_list)} IPs because they are unreachable.")
                # Assign new ip list withing None and False ips.
                self.ip_list = ips

            if len(self.ip_list) <= 0:
                # Print a log warning since we don't have any good ips.
                self.logger.warning("Switch config window did not open because no valid or reachable IPs were given.")
                # Close window.
                self.close_window()
            else:
                if not self.retrieving_devices:
                    # Loop through and grab just the IPs of the devices.
                    addresses = []
                    for addr in self.ip_list:
                        # Split the string containing ip and hostname.
                        temp = addr.split(" ")[0]
                        # Add only ip to the list.
                        addresses.append(temp)
                    
                    # Now that we have a good list of IPs, get device info about each one.
                    Thread(target=ssh_autodetect_switchlist_info, args=(self.username, self.password, addresses, self.devices)).start()

                    # Set toggle.
                    self.retrieving_devices = True

                # Wait until devices list has been updated.
                if (len(self.devices) > 0):
                    # Update hostnames.
                    for i, addr in enumerate(self.ip_list):
                        # Split ip string.
                        addr = addr.split(" ")
                        # Copy devices hostname to ip list.
                        device = self.devices[i]
                        if device is not None and len(device) > 0:
                            hostname = device["hostname"]
                            device = f"{addr[0]} {hostname}"
                            self.ip_list[i] = device

                    # Initialize window components.
                    self.initialize_window()

        # Only update window components if window is initialized.
        if self.window_is_initialized:
            # Call window event loop.
            self.window.update()

    def close_window(self) -> None:
        """
        This method is called when the configure window closes.
        """
        # Set bool value.
        self.window_is_open = False
        self.retrieving_devices = False
        # Clear arrays.
        self.ip_list.clear()
        self.devices.clear()
        # Close window.
        if self.window_is_initialized:
            # Print info.
            self.logger.info("Configure window exit action has been invoked. Performing closing actions.")
            # Set toggle.
            self.window_is_initialized = False
            # Destroy window.
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

    def get_is_window_initialized(self) -> bool:
        """
        Returns if the window has been initialized

        Parameters:
        -----------
            None

        Returns:
        --------
            Nothing
        """
        return self.window_is_initialized
