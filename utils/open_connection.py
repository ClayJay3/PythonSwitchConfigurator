# Import required packages and modules.
import logging
from functools import partial
from multiprocessing.pool import ThreadPool
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
    devices_info = {}

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
            devices_info["hostname"] = prompt[:-1]
            # Store known ip address.
            devices_info["ip_address"] = ip_addr
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
        devices_info["neighbors"] = list(set(neighbor_ips))

        #######################################################################
        # Get the model and firmware version info.
        #######################################################################
    except NetmikoAuthenticationException:
        # Print log info.
        logger.error(f"Unable to authenticate with device {ip_addr}")
        # Set default value.
        devices_info = {"ip_address": ip_addr, "hostname": "Unable to Authenticate"}
    except NetmikoTimeoutException:
        # Print log info.
        logger.error(f"Something happened while trying to communicate with device {ip_addr}")
        # Set default value.
        devices_info = {"ip_address": ip_addr, "hostname": "Unable to Authenticate"}

    # Copy devices info to result param.
    result_info = devices_info

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
    