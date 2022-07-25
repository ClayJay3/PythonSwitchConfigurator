# Import required packages and modules.
from functools import partial
import re
import logging
from multiprocessing.pool import ThreadPool
import netmiko
from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException
from netmiko.ssh_dispatcher import ConnectHandler

# Define Constants.
MAX_DISCOVERY_THREADS = 100

# Create global file variables.
discovery_list = []

def cdp_auto_discover(ip_list, username, password) -> list:
    """
    This function takes in a list of strings containing the ip addresses to start auto discovery with.
    Then new processes are spawned that run a show cdp neighbors command and parse the output to find more connected switches.
    Those new switches then go through the same process until no more switches are discoverd.

    This method is recursive.

    Parameters:
    -----------
        list(string) - A list of the initially known switch IPs.

    Returns:
    --------
        list(string) - A list of strings containg the new switch IPs. Duplicated are removed.
    """
    # Create instance variables and objects.
    logger = logging.getLogger(__name__)

    # Check if length of IP list is greater than zero.
    if len(ip_list) == 0:
        # Print log.
        logger.info("Discovery has reached the end of the network, closing recursive branches now.")
        # Return if we hit the end of the switch line.
        return discovery_list
    else:
        # Create a new thread pool and get cdp info.
        pool = ThreadPool(MAX_DISCOVERY_THREADS)
        # Loop through each ip and create a new thread to get info.
        result_ips = pool.map_async(partial(get_cdp_neighbors_info, username, password), ip_list)
        # Wait for pool threads to finish.
        pool.close()
        pool.join()

        # Get resulting IPs and filter out duplicates.
        new_ips = []
        for discovered_ip_addrs in result_ips.get():
            for ip_addr in discovered_ip_addrs:
                if not ip_addr in discovery_list:
                    # Append them to discover list. Also create a new list with this recursion layers new unique IPs.
                    discovery_list.append(ip_addr)
                    new_ips.append(ip_addr)

        # Print log.
        logger.info(f"Discovered IPs {new_ips} from the following devices: {ip_list}")

        # Recursion baby.
        return cdp_auto_discover(new_ips, username, password)
        
def get_cdp_neighbors_info(username, password, ip_addr) -> dict:
    """
    This function opens a new ssh connection with the given ip and gets cdp neighbors info.

    Parameters:
    -----------
        ip_addr - The IP address of the switch.
        username - The login username
        password - The login password

    Returns:
    --------
        list - A list containing the connected cdp devices IP info.
    """
    # Create instance variables and objects.
    logger = logging.getLogger(__name__)
    cdp_neighbors_result_ips = []

    # Create device dictionary.
    remote_device = {"device_type": "autodetect", "host": ip_addr, "username": username, "password": password}
    # If the device is not a switch codemiko will crash.
    try:
        # Open new ssh connection with switch.
        ssh_connection = ConnectHandler(**remote_device)

        #######################################################################
        # Get the IP and hostname info.
        #######################################################################
        try:
            # Run cdp command to get relavant info.
            output = ssh_connection.send_command("show cdp neighbors detail | inc Device | address:")

            # Parse output, split string based on the Device keyword.
            device_cdps = re.split("Device", output)
            # Loop through device strings.
            for device in device_cdps:
                # Count occurences of keyword in the current device string.
                count = device.count("IP address:")

                # If count is 2, than the device is a full switch. (not a phone)
                if count >= 2:
                    # Split lines.
                    addrs = device.splitlines()
                    # Loop through each line and find the device IP.
                    for addr in addrs:
                        if "IP address:" in addr:
                            final_ip = addr.replace("IP address: ", "")
                            # Remove leading whitespace and append final ip to the cdp info list.
                            cdp_neighbors_result_ips.append(final_ip.strip())
                            # Stop for loop iteration.
                            break

            # Close ssh connection.
            ssh_connection.disconnect()
        except ValueError:
            # Do nothing. Errors are expected.
            pass
    except Exception:
        # Do nothing. Errors are expected.
        pass

    return cdp_neighbors_result_ips
