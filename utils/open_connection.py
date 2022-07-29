# Import required packages and modules.
import re
import logging
from functools import partial
from multiprocessing.pool import ThreadPool
import string
import time
from tkinter import messagebox
import netmiko
from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException
from netmiko.ssh_dispatcher import ConnectHandler

# Create constants.
SSH_THREADS = 100

def ssh_autodetect_info(username, password, ip_addr, result_info=None) -> str:
    """
    This method will attempt to autodetect the switch device info using netmiko's
    ssh_autodetect

    Parameters:
    -----------
        username - The username creds to try and login with.
        password - The password creds to try and login with.
        ip_address - The ip address of the device to try to connect to.
        result_info - This can be used as a reference variable if this function is running in
                    a thread and it's return values can't be retrieved.

    Returns:
    --------
        device - A dictionary containing info about the switch like (model, hostname, firmware version, and neighbors)
    """
    # Create instance variables and objects.
    logger = logging.getLogger(__name__)

    # Create device dictionary.
    remote_device = {"device_type": "autodetect", "host": ip_addr, "username": username, "password": password}
    # If the device is not a switch codemiko will crash.
    try:
        # Print logging info.
        logger.info(f"Autodetecting model and opening connection for {ip_addr}")
        # Open new ssh connection with switch.
        ssh_connection = ConnectHandler(**remote_device)
        # Print logging info.
        logger.info("Waiting for command prompt...")

        #######################################################################
        # Get the IP and hostname info.
        #######################################################################
        try:
            # Look for switch prompt.
            prompt = ssh_connection.find_prompt()
            # Print prompt.
            logger.info(f"Found prompt: {prompt}")
            # Take off # from prompt to get hostname.
            remote_device["host"] = prompt[:-1]
            # Store known ip address.
            remote_device["ip_address"] = ip_addr
        except ValueError:
            logger.error(f"Unable to find switch prompt for {ip_addr}")
    except NetmikoAuthenticationException:
        # Print log info.
        logger.error(f"Unable to authenticate with device {ip_addr}")
        # Set default value.
        remote_device["ip_address"] = ip_addr
        remote_device["host"] = "Unable_to_Authenticate"
    except NetmikoTimeoutException:
        # Print log info.
        logger.error(f"Something happened while trying to communicate with device {ip_addr}")
        # Set default value.
        remote_device["ip_address"] = ip_addr
        remote_device["host"] = "Unable_to_Authenticate"

    # Copy devices info to result param.
    result_info = remote_device

    return result_info

def ssh_autodetect_switchlist_info(username, password, ip_list, device_list) -> None:
    """
    This method will attempt to autodetect a list of switches device info using netmiko's
    ssh_autodetect.

    Parameters:
    -----------
        username - The username creds to try and login with.
        password - The password creds to try and login with.
        ip_list - The ip addresses of the device to try to connect to.
        device_list - The list to store the deivce info in. (Returned in same order as ip_list)

    Returns:
    --------
        Nothing
    """
    # Create method instance variables.
    thread_pool = ThreadPool(SSH_THREADS)
    logger = logging.getLogger(__name__)

    # Check if the ip list actually contains something.
    if len(ip_list) > 0:
        # Try to auth with one switch first.
        first_switch = ssh_autodetect_info(username, password, ip_list.pop(0))
        # Check if auth was successful.
        if first_switch["host"] != "Unable_to_Authenticate":
            # Append first device to device list.
            device_list.append(first_switch)

            # Loop through each line and try to ping it in a new thread.
            devices = thread_pool.map_async(partial(ssh_autodetect_info, username, password), ip_list)
            # Wait for pool threads to finish.
            thread_pool.close()
            thread_pool.join()

            # Get results from pool.
            for switch in devices.get():
                device_list.append(switch)
        else:
            # Print log.
            logger.warning("Can't authenticate with the given credentials. Please enter the corrent username and password.")
            # Append none to device list.
            device_list.append(None)
    else:
        # Print log.
        logger.warning("No IPs were givin. Can't open any SSH sessions to autodetect.")

def ssh(device) -> netmiko.ssh_dispatcher:
    """
    This method uses the given ip to open a new ssh connetion.

    Parameters:
    -----------
        device - A dictionary object containing the required keys and values to connect to the device.

    Returns:
    --------
        ssh_connection - The live connection object to the device.
    """
    # Create instance variables and objects.
    logger = logging.getLogger(__name__)
    connection = None

    # Only give connect handler what it needs. 
    remote_device = {"device_type": device["device_type"], "host": device["ip_address"], "username": device["username"], "password": device["password"]}

    # If the device is not a switch codemiko will crash.
    try:
        # Try to open a connection with the device.
        connection = ConnectHandler(**remote_device)
    except NetmikoAuthenticationException:
        # Print log info.
        logger.error(f"Unable to authenticate with device {device['host']}")
    except NetmikoTimeoutException:
        # Print log info.
        logger.error(f"Something happened while trying to communicate with device {device['host']}")

    # Configure terminal properties if connection is alive.
    if connection is not None and connection.is_alive():
        # Tell switch to continuously print output.
        connection.send_command("terminal length 0", expect_string="#")
        connection.send_command("set length 0", expect_string="#")
        # Get priviledged terminal.
        connection.enable()

    # Get device interface, vlan, and config info.
    interfaces, vlans, config = get_config_info(connection)
    # Store info in device dictionary.
    device["interfaces"] = interfaces
    device["vlans"] = vlans
    device["config"] = config

    # Connect and return
    return connection

def get_config_info(connection) -> netmiko.ssh_dispatcher:
    """
    Gathers information on the devices interfaces, vlans, and raw config given a netmiko connection to it.

    Parameters:
    -----------
        connection - The netmiko connection session to the device.

    Returns:
        interfaces - A list containing info about the devices interfaces.
        vlans - A list containing info about the devices vlans.
        config - The raw config output from the device.
    """
    # Create instance variables.
    interfaces = []
    vlans = []
    config = "Unable to pull config from device. Check console output for errors. Try refreshing device info."
    logger = logging.getLogger(__name__)

    # This one gets complicated, just gonna try-catch it all.
    try:
        # Check if connection is good.
        if connection is not None and connection.is_alive():
            # Elevate privs and prevent the terminal from pausing during long command outputs.
            connection.enable()
            # Find prompt for connection.
            prompt = connection.find_prompt()

            ###########################################################################
            # Parse and store config.
            ###########################################################################
            # Get config output.
            config = connection.send_command("show run", expect_string=prompt)
            # Split config text into lines and remove first three.
            config = config.split("\n")[3:]
            # Reassemble.
            config_output = ""
            for line in config:
                config_output += line + "\n"
            # Store config.
            config = config_output

            ###########################################################################
            # Parse and store interfaces output.
            ###########################################################################
            # Get interface output.
            interface_output = connection.send_command("show interface status", expect_string=prompt)

            # Parse interface output.
            output_split = interface_output.splitlines()[2:]
            for line in output_split:
                # Check length of line.
                if len(line) > 2:
                    # Split the current line by spaces.
                    line = re.split(" +", line)
                    # Keep the interface name and strip it of leading and trailing whitespace.
                    name = line[0].strip()
                    # Append new dictionary to interfaces list.
                    interfaces.append({"name" : name})

            ## Get individual interface data.
            # Split up config by !.
            config_blocks = re.split("!+", config)

            interface_blocks = []
            # Loop through the split up config blocks and only keep the interface ones.          
            for block in config_blocks:
                # Check if the block contains the word interface.
                if "interface" in block:
                    # Remove first two chars from block.
                    block = block[1:]
                    # split block up by new lines.
                    block = block.splitlines()
                    # Append to list.
                    interface_blocks.append(block)
            
            # Loop through the interfaces and blocks and match them by name.
            for interface in interfaces:
                for interface_data in interface_blocks:
                    # Get interface name.
                    name_data = re.split(" +", interface_data[0])[1]
                    block_name = name_data[:2] + name_data.translate(str.maketrans('', '', string.ascii_letters + "-"))
                    # Check if names are equal.
                    if interface["name"] == block_name:
                        # Add relevant info to the interface using the interface_data list.
                        description = ""
                        shutdown = False
                        switch_mode_access = False
                        switch_mode_trunk = False
                        spanning_tree_portfast = False
                        spanning_tree_bpduguard = False
                        switch_access_vlan = 0
                        switch_voice_vlan = 0
                        switch_trunk_vlan = 0


                        # Loop through each config line for the interface and get data.
                        for data in interface_data:
                            # Get Description info.
                            if "description" in data and description == "":
                                # Remove unneeded keywork from data.
                                data = data.replace("description", "")
                                # Remove trailing and leading spaces and set description equal to new data.
                                description = data.strip()

                            # Get port shutdown info.
                            if "shutdown" in data and not "no shutdown" in data:
                                # Set toggle.
                                shutdown = True

                            # Check for sw mo acc interface flag.
                            if "switchport mode access" in data:
                                # Set toggle.
                                switch_mode_access = True

                            # Check for spanning tree.
                            if "spanning-tree portfast" in data:
                                # Set toggle.
                                spanning_tree_portfast = True
                            if "spanning-tree bpduguard enable" in data:
                                # Set toggle.
                                spanning_tree_bpduguard = True

                            # Check for trunk mode data.
                            if "switchport mode trunk" in data:
                                # Set toggle.
                                switch_mode_trunk = True

                            # Check for access, voicem, and trunk vlan number.
                            if "switchport access vlan" in data:
                                # Remove all letters from data.
                                data = data.translate(str.maketrans('', '', string.ascii_letters))
                                # Remove trailing and leading whitespace and store.
                                switch_access_vlan = data.strip()
                            if "switchport voice vlan" in data:
                                # Remove all letters from data.
                                data = data.translate(str.maketrans('', '', string.ascii_letters))
                                # Remove trailing and leading whitespace and store.
                                switch_voice_vlan = data.strip()
                            if "switchport trunk native vlan" in data:
                                # Remove all letters from data.
                                data = data.translate(str.maketrans('', '', string.ascii_letters))
                                # Remove trailing and leading whitespace and store.
                                switch_trunk_vlan = data.strip()

                            
                        # Add description to interface dictionary.
                        interface["description"] = description
                        interface["shutdown"] = shutdown
                        interface["switchport mode access"] = switch_mode_access
                        interface["switchport mode trunk"] = switch_mode_trunk
                        interface["spanning-tree portfast"] = spanning_tree_portfast
                        interface["spanning-tree bpduguard enable"] = spanning_tree_bpduguard
                        interface["switchport access vlan"] = switch_access_vlan
                        interface["switchport voice vlan"] = switch_voice_vlan
                        interface["switchport trunk native vlan"] = switch_trunk_vlan
                        interface["config_has_changed"] = False

            ###########################################################################
            # Parse and store vlan output.
            ###########################################################################
            # Add interface and vlan info to the switch device dictionary.
            vlan_output = connection.send_command("show vlan brief", expect_string=prompt)
            output_split = vlan_output.splitlines()[3:]
            # Loop through each line and get relavent data.
            for line in output_split:
                # Check line validity.
                if len(line) > 2:
                    # Split line into words at each whitespace.
                    line = re.split(" +", line)
                    # Check if vlan is active.
                    if "active" in line[2]:
                        # Get data.
                        vlan = line[0]
                        name = line[1]
                        # Append to vlan array.
                        vlans.append({"vlan" : vlan, "name" : name})

            ## Get individual interface data.
            # Split up config by !.
            config_blocks = re.split("!+", config)

            vlan_blocks = []
            # Loop through the split up config blocks and only keep the interface ones.          
            for block in config_blocks:
                # Check if the block contains the word interface.
                if "interface Vlan" in block:
                    # split block up by new lines and remove first line. (it's empty)
                    block = block.splitlines()[1:]
                    # Append to list.
                    vlan_blocks.append(block)
            
            # Loop through the vlans and blocks and match them by name.
            for vlan in vlans:
                for vlan_data in vlan_blocks:
                    # Get vlan name.
                    name_data = re.split(" +", vlan_data[0])[1]
                    block_name = name_data.translate(str.maketrans('', '', string.ascii_letters + "-"))
                    # Check if names are equal.
                    if vlan["vlan"] == block_name:
                        # Add relevant info to the vlan using the vlan_data list.
                        description = ""
                        ip_addr = ""
                        shutdown = False

                        # Loop through each config line for the vlan and get data.
                        for data in vlan_data:
                            # Get Description info.
                            if "description" in data and description == "":
                                # Remove unneeded keyword from data.
                                data = data.replace("description", "")
                                # Remove trailing and leading spaces and set description equal to new data.
                                description = data.strip()
                            # Get ip address info.
                            if not "no ip address" in data and "ip address" in data:
                                # Remove uneeded keyword from data.
                                data = data.replace("ip address", "")
                                # Remove trailing and leading spaces and set new data.
                                ip_addr = data.strip()
                            # Get vlan shutdown info.
                            if "shutdown" in data and not "no shutdown" in data:
                                # Set toggle.
                                shutdown = True
                            
                        # Add description to vlan dictionary.
                        vlan["description"] = description
                        vlan["ip address"] = ip_addr
                        vlan["shutdown"] = shutdown
                        vlan["config_has_changed"] = False
    except Exception as error:
        # Print log.
        logger.error("Something goofy happened while updating switch configuration info: ", exc_info=error, stack_info=True)

    return interfaces, vlans, config