'''
Finds and executes the IP info
'''
import requests
import subprocess
import time
import psutil
from threading import Thread

from pigeovpn.constants import CREDS_FILE, IP_REFRESH_INTERVAL, UPDATE_DELAY, upload_usage, download_usage, upload_speed, download_speed

ip_directory = {
        "ip": "Unknown",
        "city": "Unknown",
        "region": "Unknown",
        "org": "Unknown",
        "postal": "Unknown",
        "country": "Unknown",
        "country_name": "Unknown"
        }

def fetch_ip_info():
    """Fetch the public IP info and update the global cache."""
    global ip_directory

    def get_ip():
        try:
            response = requests.get("https://ipinfo.io/json", timeout=2).json()
        except requests.exceptions.ConnectTimeout:
            return False
        except ReadTimeout:
            return False
        else:
            return response["ip"]

    def update_ip_directory(data):
        for key in ["ip", "city", "region", "org", "postal", "country", "country_name"]:
            if key in data:
                ip_directory[key] = data[key]

    ip_address = get_ip()
    if ip_address:
        try:
            ip_address = get_ip()
            response_ipapi = requests.get(f'https://ipapi.co/{ip_address}/json/') # This is more accurate than https://ipinfo.io/json
            response_ipapi.raise_for_status()  # Raise exception for bad HTTP status
            data = response_ipapi.json()
        except requests.exceptions.HTTPError: # If too many requests are sent to ipapi, continue with ipinfo
            try:
                data=requests.get("https://ipinfo.io/json", timeout=5).json()
            except Exception as e:
                print(type(e), e)
            else:
                update_ip_directory(data)
        else:
            update_ip_directory(data)

def start_ip_info_thread():
    """Start background thread to refresh IP info every 30 seconds."""
    def thread_func():
        while True:
            fetch_ip_info()
            time.sleep(IP_REFRESH_INTERVAL)
    Thread(target=thread_func, daemon=True).start()

"""
Monitor network usage / data transfering. Taken from https://thepythoncode.com/article/make-a-network-usage-monitor-in-python
"""
def get_size(bytes):
    """
    Returns size of bytes in a nice format
    """
    for unit in ['', 'K', 'M', 'G', 'T', 'P']:
        if bytes < 1024:
            return f"{bytes:.2f}{unit}B"
        bytes /= 1024

def network_usage():
    global upload_usage, download_usage, upload_speed, download_speed
    # get the network I/O stats from psutil
    io = psutil.net_io_counters()
    # extract the total bytes sent and received
    bytes_sent, bytes_recv = io.bytes_sent, io.bytes_recv

    while True:
         # sleep for `UPDATE_DELAY` seconds
        time.sleep(UPDATE_DELAY)
        # get the stats again
        io_2 = psutil.net_io_counters()
        # new - old stats gets us the speed
        us, ds = io_2.bytes_sent - bytes_sent, io_2.bytes_recv - bytes_recv
        # Speeds and usage
        upload_usage = get_size(io_2.bytes_sent)
        download_usage = get_size(io_2.bytes_recv)
        upload_speed = get_size(us / UPDATE_DELAY)
        download_speed = get_size(ds / UPDATE_DELAY)
        # update the bytes_sent and bytes_recv for next iteration
        bytes_sent, bytes_recv = io_2.bytes_sent, io_2.bytes_recv
