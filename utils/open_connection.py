# Import required packages and modules.
import re
import logging
from functools import partial
from multiprocessing.pool import ThreadPool
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

        #######################################################################
        # Get the neighboring connected switches.
        #######################################################################
        # Run command.
        output = ssh_connection.send_command("show cdp neighbors detail")
        # Parse cdp neighbors output
        neighbor_ips = []
        # Find starting index of IP address line.
        index = 0
        while index != -1:
            # Get starting index of IP.
            index = output.find("IP")
            # Step forward until we hit a newline char.
            neighbor_ip = ""
            counter = 0
            for char in output[index:]:
                # Check if current character is a newline.
                if (char != "\n"):
                    # Append char to new string.
                    neighbor_ip = neighbor_ip + char
                    # Increment counter.
                    counter += 1
                else:
                    # Stop looping once we reach the end of the ip.
                    break

            # Split neighbor ip string by space.
            neighbor_ips.append(neighbor_ip.split(sep=" ")[-1])
            # Cutoff the string we already searched.
            output = output[index + counter:]
        
        # Remove duplicates from neighbor list and add to dictionary.
        neighbor_ips = [addr for addr in neighbor_ips if len(addr) >= 8]
        remote_device["neighbors"] = list(set(neighbor_ips))

        #######################################################################
        # Get the model and firmware version info.
        #######################################################################
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
        # Loop through each line and try to ping it in a new thread.
        devices = thread_pool.map_async(partial(ssh_autodetect_info, username, password), ip_list)

        # Wait for pool threads to finish.
        thread_pool.close()
        thread_pool.join()

        # Get results from pool.
        for switch in devices.get():
            device_list.append(switch)
    else:
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
    config = ""

    # Check if connection is good.
    if connection is not None and connection.is_alive():
        # Elevate privs and prevent the terminal from pausing during long command outputs.
        connection.enable()
        connection.send_command("terminal length 0")

        ###########################################################################
        # Parse and store interfaces output.
        ###########################################################################
        # Get interface output.
        interface_output = connection.send_command("show interface status")
        descriptions = connection.send_command("show interfaces description")

        # Parse interface output.
        output_split = interface_output.splitlines()[2:]
        for line in output_split:
            # Split the current line by spaces.
            line = re.split(" +", line)
            # Keep the interface name, and vlan.
            name = line[0]
            vlan = line[-4]
            # Append to interfaces list.
            interfaces.append([vlan, name])

        # Parse description output.
        output_split = descriptions.splitlines()[1:]
        for line in output_split:
            # Split the current line by spaces.
            line = re.split(" +", line)
            # Keep the interface name and description.
            name = line[0]
            # Find index of protocol column.
            try:
                # Attempt to find up protocal word.
                index = line.index("up")
            except ValueError:
                try:
                    # If up fails try down.
                    index = line.index("down")
                except ValueError:
                    # If we can't find anything just take the last word.
                    index = -1
            # Store everything after the protocol column.
            description = ""
            for word in line[index + 2:]:
                # Add each word to the description string.
                description += word

            # Find the same interface in the interfaces list and add the description to the list.
            for interface in interfaces:
                # Check if the names are the same.
                if interface[1] == name:
                    # Append the description.
                    interface.append(description)

        ###########################################################################
        # Parse and store vlan output.
        ###########################################################################
        # Add interface and vlan info to the switch device dictionary.
        vlan_output = connection.send_command("show vlan brief")
        output_split = vlan_output.splitlines()[3:]
        # Loop through each line and get relavent data.
        for line in output_split:
            # Split line into words at each whitespace.
            line = re.split(" +", line)
            # Get data.
            vlan = line[0]
            name = line[1]
            # Append to vlan array.
            vlans.append([vlan, name])
        
        ###########################################################################
        # Parse and store config.
        ###########################################################################
        # Get config output.
        config = connection.send_command("show run")
        # Split config text into lines and remove first three.
        config = config.split("\n")[3:]
        # Reassemble.
        config_output = ""
        for line in config:
            config_output += line + "\n"
        # Store config.
        config = config_output

    return interfaces, vlans, config