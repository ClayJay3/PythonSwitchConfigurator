import re
import logging
import time
import netmiko
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from threading import Thread
from typing import List, Tuple

from interface.popup_window import ListPopup, MultipleListPopup, text_popup
from utils.open_connection import get_config_info, ssh_autodetect_switchlist_info, ssh


# Create Configure UI window class.
class ConfigureUI:
    """
    Class that serves as frontend for all of the individual switch configure.
    """
    def __init__(self) -> None:
        # Create class variables, objects, and constants.
        self.logger = logging.getLogger(__name__)
        self.window = None
        self.window_is_open = False
        self.window_is_initialized = False
        self.is_enabled = False
        self.retrieving_devices = False
        self.grid_size = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        self.font = "antiqueolive"

        # Window Frames.
        self.selector_frame = None
        self.command_button_frame = None
        self.interface_frame = None
        self.vlan_frame = None
        self.upload_frame = None

        # Window 
        self.username = None
        self.password = None
        self.ip_list = []
        self.ssh_connections = []
        self.devices = []
        self.switch_selection = None
        self.drop_down = None
        self.interfaces_list = []
        self.interface_selection = None
        self.interface_drop_down = None
        self.vlans_list = []
        self.vlan_selection = None
        self.vlan_drop_down = None
        self.text_box = None

        # This serves as a temp var used by many things, anytime a popup window that is destroyable is made, it's stored here.
        self.popup = None

    def run(self, ips, username, password) -> None:
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
        self.interface_selection = tk.StringVar(self.window)
        self.interface_selection.set("No interface is selected")
        self.vlan_selection = tk.StringVar(self.window)
        self.vlan_selection.set("No vlan is selected")

        # Setup window grid layout.
        self.window.rowconfigure(self.grid_size, weight=1, minsize=60)
        self.window.columnconfigure(self.grid_size, weight=1, minsize=70)

        #######################################################################
        #               Create window components.
        #######################################################################
        # Create frame for selecting which switch to connect to.
        self.selector_frame = tk.Frame(master=self.window, relief=tk.GROOVE, borderwidth=3)
        self.selector_frame.grid(row=0, column=0, columnspan=5, sticky=tk.NSEW)
        self.selector_frame.rowconfigure(0, weight=1)
        self.selector_frame.columnconfigure(0, weight=1)
        # Create frame for the quick command buttons.
        self.command_button_frame = tk.LabelFrame(master=self.window, text="Quick Commands", relief=tk.GROOVE, borderwidth=3)
        self.command_button_frame.grid(row=0, column=5, columnspan=5, sticky=tk.NSEW)
        self.command_button_frame.rowconfigure(0, weight=1)
        self.command_button_frame.columnconfigure(self.grid_size, weight=1)
        # Create frame for interface configuration.
        self.interface_frame = tk.LabelFrame(master=self.window, text="Interface Config", relief=tk.GROOVE, borderwidth=3)
        self.interface_frame.grid(row=1, rowspan=9, column=0, columnspan=4, sticky=tk.NSEW)
        self.interface_frame.rowconfigure(self.grid_size, weight=1)
        self.interface_frame.columnconfigure(self.grid_size, weight=1)
        # Create frame for vlan configuration.
        self.vlan_frame = tk.LabelFrame(master=self.window, text="VLAN Config", relief=tk.GROOVE, borderwidth=3)
        self.vlan_frame.grid(row=1, rowspan=9, column=4, columnspan=3, sticky=tk.NSEW)
        self.vlan_frame.rowconfigure(self.grid_size, weight=1)
        self.vlan_frame.columnconfigure(self.grid_size, weight=1)
        # Create frame for uploading configuration.
        self.upload_frame = tk.LabelFrame(master=self.window, text="Upload Config", relief=tk.GROOVE, borderwidth=3)
        self.upload_frame.grid(row=1, rowspan=9, column=7, columnspan=3, sticky=tk.NSEW)
        self.upload_frame.rowconfigure(0, weight=1)
        self.upload_frame.columnconfigure(0, weight=1)

        # Populate selector frame.
        self.drop_down = ttk.Combobox(master=self.selector_frame, textvariable=self.switch_selection, values=self.ip_list)
        self.drop_down.bind('<<ComboboxSelected>>', self.drop_down_callback)        # Set callback binding for combobox cause it's odd.
        self.drop_down.grid(row=0, column=0, columnspan=7, sticky=tk.NSEW)
        write_button = tk.Button(master=self.selector_frame,  text="WRITE", foreground="black", background="white", command=self.write_config_callback)
        write_button.grid(row=0, column=7, columnspan=3, sticky=tk.NSEW)

        # Populate quick command frame.
        int_stat_button = tk.Button(master=self.command_button_frame,  text="Interface Status", foreground="black", background="white", command=self.interface_status_callback)
        int_stat_button.grid(row=0, column=0, columnspan=1, sticky=tk.NSEW)
        log_button = tk.Button(master=self.command_button_frame,  text="Show Log", foreground="black", background="white", command=self.show_log_callback)
        log_button.grid(row=0, column=1, sticky=tk.NSEW)
        test_link_button = tk.Button(master=self.command_button_frame,  text="Test Port Link Quality", foreground="black", background="white", command=self.test_port_link_callback)
        test_link_button.grid(row=0, column=2, columnspan=1, sticky=tk.NSEW)
        show_int_err_button = tk.Button(master=self.command_button_frame,  text="Show Interface Errors", foreground="black", background="white", command=self.show_interface_errors_callback)
        show_int_err_button.grid(row=0, column=3, columnspan=1, sticky=tk.NSEW)
        clr_int_err_button = tk.Button(master=self.command_button_frame,  text="Clear Interface Errors", foreground="black", background="white", command=self.clear_interface_errors_callback)
        clr_int_err_button.grid(row=0, column=4, columnspan=1, sticky=tk.NSEW)
        port_channel_button = tk.Button(master=self.command_button_frame,  text="Create Port Channel", foreground="black", background="white", command=self.port_channel_callback)
        port_channel_button.grid(row=0, column=5, columnspan=1, sticky=tk.NSEW)

        # Populate interface configuration frame.
        int_select_label = tk.Label(master=self.interface_frame, text="Select Interface:")
        int_select_label.grid(row=0, rowspan=1, column=0, columnspan=2, sticky=tk.EW)
        self.interface_drop_down = ttk.Combobox(master=self.interface_frame, textvariable=self.interface_selection, values=self.interfaces_list)
        self.interface_drop_down.bind('<<ComboboxSelected>>', self.select_interface)        # Set callback binding for combobox cause it's odd.
        self.interface_drop_down.grid(row=0, rowspan=1, column=2, columnspan=8, sticky=tk.EW)

        # Populate vlan configuration frame.
        vlan_select_label = tk.Label(master=self.vlan_frame, text="Select VLAN:")
        vlan_select_label.grid(row=0, rowspan=1, column=0, columnspan=2, sticky=tk.EW)
        self.vlan_drop_down = ttk.Combobox(master=self.vlan_frame, textvariable=self.vlan_selection, values=self.vlans_list)
        self.vlan_drop_down.bind('<<ComboboxSelected>>', self.select_vlan)        # Set callback binding for combobox cause it's odd.
        self.vlan_drop_down.grid(row=0, rowspan=1, column=2, columnspan=8, sticky=tk.EW)

        # Populate upload config frame.
        self.text_box = tk.Text(master=self.upload_frame, width=10, height=5)
        self.text_box.grid(row=0, rowspan=9, column=0, columnspan=10, sticky=tk.NSEW)
        scroll=tk.Scrollbar(master=self.upload_frame, orient='vertical', command=self.text_box.yview)    # Add a scrollbar.
        scroll.grid(row=0, rowspan=9, column=10, sticky=tk.NS)
        self.text_box['yscrollcommand'] = scroll.set         # Link scroll value back to text box.
        write_button = tk.Button(master=self.upload_frame,  text="Upload Config", foreground="black", background="white", command=self.upload_config_callback)
        write_button.grid(row=9, column=0, columnspan=10, sticky=tk.NSEW)

        # Set window initialized flag.
        self.window_is_initialized = True

    def drop_down_callback(self, event) -> None:
        """
        This method is called everytime a new item is selected in the dropdown menu.

        Parameters:
        -----------
            event - The virtual event given to us by the binding of this method to the drop_down object.

        Returns:
        --------
            Nothing
        """
        # Get the index of the currently selected device.
        device_index = self.drop_down.current()
        # Get device connection.
        connection = self.ssh_connections[device_index]

        # Print log.
        self.logger.info(f"Selected device: {self.ip_list[device_index]}. Getting data...")

        # Check if a valid choice has been made.
        if device_index != -1 and (self.ssh_connections[device_index] is None or not self.ssh_connections[device_index].is_alive()):
            # Get the current selected device.
            device = self.devices[device_index]
            # Open ssh connection with switch.
            connection = ssh(device)
            # Store the new connection in the ssh connections list.
            self.ssh_connections[device_index] = connection

        #######################################################################
        # Update config window component data with the new device.
        #######################################################################
        # Check if connection is good.
        if connection is not None and connection.is_alive():
            # Enable config window components. Othewise textbox won't update with input.
            self.enable()
            # Get device.
            device = self.devices[device_index]
            # Update interfaces list and drop down menu.
            self.interfaces_list = device["interfaces"]
            self.interface_drop_down["values"] = [val[1:] for val in self.interfaces_list]
            self.interface_selection.set("No interface is selected")
            # Update vlans list and drop down menu.
            self.vlans_list = device["vlans"]
            self.vlan_drop_down["values"] = self.vlans_list
            self.vlan_selection.set("No vlan is selected")
            # Update config component.
            config_data = device["config"]
            self.text_box.delete("1.0", tk.END)
            self.text_box.insert(tk.END, config_data)

    def write_config_callback(self):
        """
        This method is called everytime the WRITE button is pressed.

        Parameters:
        -----------
            None

        Returns:
        --------
            Nothing
        """
        pass

    def interface_status_callback(self) -> None:
        """
        This method is called everytime the Interface Status button is pressed.
        
        Parameters:
        -----------
            None

        Returns:
        --------
            Nothing
        """
        # Get the current index of the device selected from the dropdown menu.
        current_device_index = self.drop_down.current()
        # Get device.
        device = self.devices[current_device_index]
        # Get connection of device.
        connection = self.ssh_connections[current_device_index]

        # Print log.
        self.logger.info(f"Sending button command 'interface status' to {device['host']}")

        # Send command to switch and open a message box with the command output.
        if connection is not None and connection.is_alive():
            # Run command
            output = connection.send_command("show interface status")
            # Open a new popup window with the output text.
            text_popup(output)
        else:
            # Display message box saying the command was unable to complete.
            messagebox.showwarning(title="Info", message="The command was unable to complete because the connection to the device is currently not alive or was never opened.", parent=self.window)

    def show_log_callback(self) -> None:
        """
        This method is called everytime the Show Log button is pressed.
        
        Parameters:
        -----------
            None

        Returns:
        --------
            Nothing
        """
        # Get the current index of the device selected from the dropdown menu.
        current_device_index = self.drop_down.current()
        # Get device.
        device = self.devices[current_device_index]
        # Get connection of device.
        connection = self.ssh_connections[current_device_index]

        # Print log.
        self.logger.info(f"Sending button command 'show log' to {device['host']}")

        # Send command to switch and open a message box with the command output.
        if connection is not None and connection.is_alive():
            # Run command
            output = connection.send_command("show log")
            # Open a new popup window with the output text.
            text_popup(output, x_grid_size=15, y_grid_size=10)
        else:
            # Display message box saying the command was unable to complete.
            messagebox.showwarning(title="Info", message="The command was unable to complete because the connection to the device is currently not alive or was never opened.", parent=self.window)


    def test_port_link_callback(self) -> None:
        """
        This method is called everytime the Test Port Link Quality button is pressed.
        
        Parameters:
        -----------
            None

        Returns:
        --------
            Nothing
        """
        # Get the current index of the device selected from the dropdown menu.
        current_device_index = self.drop_down.current()
        # Get device.
        device = self.devices[current_device_index]
        # Get connection of device.
        connection = self.ssh_connections[current_device_index]

        # Send command to switch and open a message box with the command output.
        if connection is not None and connection.is_alive():
            # Open a window asking for the user to select an interface from the dropdown menu.
            self.popup = ListPopup()
            selection = self.popup.open([val[1] for val in self.interfaces_list], prompt="Select port to test:")
            # Check if selection is valid.
            if selection is not None:
                # Run command.
                output = connection.send_command(f"test cable tdr interface {selection}")
                # Sleep to give time for the command to run.
                time.sleep(0.1)
                # Get test results.
                output = connection.send_command(f"show cable tdr interface {selection}")
                
                # Print log.
                self.logger.info(f"Sending button command 'test cable tdr interface {selection}' to {device['host']}")

                # Open a new popup window with the output text.
                text_popup(output, x_grid_size=10, y_grid_size=3)
        else:
            # Display message box saying the command was unable to complete.
            messagebox.showwarning(title="Info", message="The command was unable to complete because the connection to the device is currently not alive or was never opened.", parent=self.window)


    def show_interface_errors_callback(self) -> None:
        """
        This method is called everytime the Show Interface Errors button is pressed.
        
        Parameters:
        -----------
            None

        Returns:
        --------
            Nothing
        """
        # Get the current index of the device selected from the dropdown menu.
        current_device_index = self.drop_down.current()
        # Get device.
        device = self.devices[current_device_index]
        # Get connection of device.
        connection = self.ssh_connections[current_device_index]

        # Print log.
        self.logger.info(f"Sending button command 'show interface counter error' to {device['host']}")

        # Send command to switch and open a message box with the command output.
        if connection is not None and connection.is_alive():
            # Run command
            output = connection.send_command("show interface counter error")
            # Open a new popup window with the output text.
            text_popup(output, x_grid_size=11, y_grid_size=10)
        else:
            # Display message box saying the command was unable to complete.
            messagebox.showwarning(title="Info", message="The command was unable to complete because the connection to the device is currently not alive or was never opened.", parent=self.window)


    def clear_interface_errors_callback(self) -> None:
        """
        This method is called everytime the Clear Interface Errors button is pressed.
        
        Parameters:
        -----------
            None

        Returns:
        --------
            Nothing
        """
        # Get the current index of the device selected from the dropdown menu.
        current_device_index = self.drop_down.current()
        # Get device.
        device = self.devices[current_device_index]
        # Get connection of device.
        connection = self.ssh_connections[current_device_index]

        # Print log.
        self.logger.info(f"Sending button command 'clear counters' to {device['host']}")

        # Send command to switch and open a message box with the command output.
        if connection is not None and connection.is_alive():
            # Run command
            output = connection.send_command("clear counters", expect_string="\[confirm\]")
            connection.send_command("\n", expect_string="#")
        else:
            # Display message box saying the command was unable to complete.
            messagebox.showwarning(title="Info", message="The command was unable to complete because the connection to the device is currently not alive or was never opened.", parent=self.window)


    def port_channel_callback(self) -> None:
        """
        This method is called everytime the Create Port Channel button is pressed.
        
        Parameters:
        -----------
            None

        Returns:
        --------
            Nothing
        """
        # Create instance variables.
        selections = None
        channel_number = None

        # Get the current index of the device selected from the dropdown menu.
        current_device_index = self.drop_down.current()
        # Get device.
        device = self.devices[current_device_index]
        # Get connection of device.
        connection = self.ssh_connections[current_device_index]

        # Send command to switch and open a message box with the command output.
        if connection is not None and connection.is_alive():
            # Open a window asking for the user to select interfaces from the dropdown menu.
            self.popup = MultipleListPopup()
            selections = self.popup.open([val[1] for val in self.interfaces_list], prompt="Choose your interfaces: ")
            # Check if selections completed successfully, if so then continue to ask for channel number.\
            if selections is not None:
                # Open a popup window and ask user what number port channel interface they want to connection to.
                self.popup = ListPopup()
                channel_number = self.popup.open(list(range(1,10)), prompt="Choose the port channel number:")

            # Check if we got all info from the user before running commands.
            command_list = ['config t']
            if channel_number is not None:
                # Loop through each interface and build a command config list.
                for interface in selections:
                    command_list.append(f"interface {interface}")
                    command_list.append(f"channel-group {channel_number} mode active")
                # Exit config mode.
                command_list.append("end")

                # Print log.
                self.logger.info(f"Sending button commands to make Po{channel_number} on interfaces {selections} to {device['host']}")
                # Execute switch config.
                output = connection.send_config_set(command_list, exit_config_mode=False)

                # Update interface, vlans, and config after adding port channel.
                interfaces, vlans, config = get_config_info(connection)
                # Store info in device dictionary.
                device["interfaces"] = interfaces
                device["vlans"] = vlans
                device["config"] = config

                # Update interfaces and vlan lists and dropdowns.
                self.interfaces_list = device["interfaces"]
                self.interface_drop_down["values"] = [val[1:] for val in self.interfaces_list]
                self.vlans_list = device["vlans"]
                self.vlan_drop_down["values"] = self.vlans_list

                # Update config textbox component.
                self.text_box.delete("1.0", tk.END)
                self.text_box.insert(tk.END, config)

                # Open text window with the output.
                text_popup(output)
        else:
            # Display message box saying the command was unable to complete.
            messagebox.showwarning(title="Info", message="The command was unable to complete because the connection to the device is currently not alive or was never opened.", parent=self.window)

    def select_interface(self, event) -> None:
        """
        This method is called everytime a new item is selected from the interface dropdown menu.

        Parameters:
        -----------
            event - Given to us by the ComboBox function, kinda useless right now.

        Returns:
        --------
            Nothing
        """
        pass

    def select_vlan(self, event) -> None:
        """
        This method is called everytime a new item is selected from the vlan dropdown menu.

        Parameters:
        -----------
            event - Given to us by the ComboBox function, kinda useless right now.

        Returns:
        --------
            Nothing
        """
        pass
    
    def upload_config_callback(self) -> None:
        """
        This method is called everytime the Upload Config button is pressed.

        Parameters:
        -----------
            None

        Returns:
        --------
            Nothing
        """
        # Get the current index of the device selected from the dropdown menu.
        current_device_index = self.drop_down.current()
        # Get device and device connection.
        device = self.devices[current_device_index]
        connection = self.ssh_connections[current_device_index]
        # Get config from textbox.
        config = self.text_box.get('1.0', tk.END)

        # Start method in new thread.
        # thread = Thread(target=self.upload_textbox_switch_commands, args=(current_device_index, config,))
        # thread.start()
        # thread.join()
        self.upload_text_switch_commands(current_device_index, config)

        # Update device dictionary after uploading config.
        interfaces, vlans, config = get_config_info(connection)
        # Store info in device dictionary.
        device["interfaces"] = interfaces
        device["vlans"] = vlans
        device["config"] = config

        # Update interfaces and vlan lists and dropdowns.
        self.interfaces_list = device["interfaces"]
        self.interface_drop_down["values"] = [val[1:] for val in self.interfaces_list]
        self.vlans_list = device["vlans"]
        self.vlan_drop_down["values"] = self.vlans_list

        # Update config textbox component.
        self.text_box.delete("1.0", tk.END)
        self.text_box.insert(tk.END, config)

    def upload_text_switch_commands(self, current_device_index, config) -> None:
        """
        This method gets the data from the config window's textbox and runs the commands in the currently selected switch.

        Parameters:
        -----------
            current_device_index - The current index of the device in the drop down.
            config_commands - The list of commands to execute.

        Returns:
        --------
            Nothing
        """
        # Get connection of device.
        connection = self.ssh_connections[current_device_index]
        # Get device.
        device = self.devices[current_device_index]

        # Print log.
        self.logger.info(f"Uploading config to {device['host']}. Please wait...")

        # Make sure connection is still alive.
        if connection.is_alive():
            # The send_config_set method is very jank and breaks often between netmiko updates.
            try:
                # Split the config up by !.
                config = re.split("!+", config)
                # Cutoff the last configured by text.
                config = config[3:]
                # Compare the new and old config and only run whats changed.
                diff = []
                for section in config:
                    # If the current line in the textbox config doesn't exist in the running config, then append to new list.
                    if not section in device["config"]:
                        # Append to list.
                        diff.append(section)

                # Turn the list back into a string
                commands = ""
                for command in diff:
                    commands += command
                # Split the difference list up by newlines.
                commands = re.split("\n+", commands)
                # Add config command to command list and end to end of command list. Must do this stuff manually for now because netmiko is brokey.
                commands.insert(0, "config t")

                # Get privs.
                connection.enable()
                # Display info message, so the user doesn't think the program crashed.
                messagebox.showinfo(title="Info", message="Please wait while your config is being uploaded.", parent=self.window)
                # Execute switch config.
                output = connection.send_config_set(commands, exit_config_mode=False)
                # Open new popup window containing the commands output.
                text_popup(output)
            except Exception as error:
                self.logger.critical("A NetMiko issue occured while trying to run the config commands.", stack_info=True, exc_info=error)

        
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

                # Remove duplicate entries.
                ips = list(dict.fromkeys(ips))

                # Print log info.
                if len(self.ip_list) - len(ips) > 0:
                    self.logger.info(f"Throwing out {len(self.ip_list) - len(ips)} of {len(self.ip_list)} IPs because they are duplicates or unreachable.")
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
                            hostname = device["host"]
                            device = f"{addr[0]} {hostname}"
                            self.ip_list[i] = device

                    # Set length of ssh_connection list to the same as devices.
                    self.ssh_connections = [None] * len(self.devices)

                    # Initialize window components.
                    self.initialize_window()

        # Only update window components if window is initialized.
        if self.window_is_initialized:
            # Check if the user has selected a valid option from the dropdown, if they have enable config window frames.
            if self.drop_down.current() == -1 or self.ssh_connections[self.drop_down.current()] is None or not self.ssh_connections[self.drop_down.current()].is_alive():
                # Disable window.
                self.disable()
                # Set toggle.
                self.is_enabled = False
            elif not self.is_enabled:
                # Enable window.
                self.enable()
                # Set toggle.
                self.is_enabled = True

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
        # Close any popup windows.
        if self.popup is not None and self.popup.get_is_window_open():
            # Close window.
            self.popup.close_window()
        # Close window.
        if self.window_is_initialized:
            # Print info.
            self.logger.info("Configure window exit action has been invoked. Performing closing actions.")
            # Set toggle.
            self.window_is_initialized = False
            # Destroy window.
            self.window.destroy()

    def enable(self) -> None:
        """
        Sets all of the child objects of each frame to be enabled.

        Parameters:
        -----------
            None

        Returns:
        --------
            Nothing
        """
        # Loop through selector frame.
        for child in self.selector_frame.winfo_children():
            # Enable.
            child.configure(state="normal")

        # Loop through command_button frame.
        for child in self.command_button_frame.winfo_children():
            # Enable.
            child.configure(state="normal")

        # Loop through interface frame.
        for child in self.interface_frame.winfo_children():
            # Enable.
            child.configure(state="normal")
        
        # Loop through vlan frame.
        for child in self.vlan_frame.winfo_children():
            # Enable.
            child.configure(state="normal")

        # Loop through upload frame.
        for child in self.upload_frame.winfo_children():
            # Can't disable the scrollbar.
            if child.widgetName != "scrollbar":
                # Enable.
                child.configure(state="normal")

    def disable(self) -> None:
        """
        Sets all of the child objects of each frame to be disabled.

        Parameters:
        -----------
            None

        Returns:
        --------
            Nothing
        """
        # Don't set selector frame. We won't to always be able to select a new device.

        # Loop through command_button frame.
        for child in self.command_button_frame.winfo_children():
            # Enable.
            child.configure(state="disable")

        # Loop through interface frame.
        for child in self.interface_frame.winfo_children():
            # Enable.
            child.configure(state="disable")
        
        # Loop through vlan frame.
        for child in self.vlan_frame.winfo_children():
            # Enable.
            child.configure(state="disable")

        # Loop through upload frame.
        for child in self.upload_frame.winfo_children():
            # Can't disable the scrollbar.
            if child.widgetName != "scrollbar":
                # Enable.
                child.configure(state="disable")

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
