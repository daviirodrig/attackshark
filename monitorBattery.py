import hid
import time
import sys
import signal  # To handle Ctrl+C gracefully
from datetime import datetime  # Import datetime for timestamp formatting

# --- Configuration ---
VENDOR_ID = 0x1D57
PRODUCT_ID = 0xFA60
DEVICE_PATH = b"/dev/hidraw2"  # Path confirmed to work

REPORT_ID_BATTERY = 0x03
EXPECTED_REPORT_LENGTH = 5  # Report ID + 4 data bytes
CHARGING_STATUS_INDEX = 3  # 4th byte overall (index 3)
BATTERY_LEVEL_INDEX = 4  # 5th byte overall (index 4)

# How often to print status even if unchanged (in seconds)
UPDATE_INTERVAL = 5
# Logging configuration
ENABLE_LOGGING = False
LOG_FILE = "bats.txt"
# ---------------------

# Global variable to signal exit
running = True
device = None


def signal_handler(sig, frame):
    """Handles Ctrl+C"""
    global running
    print("\nCtrl+C detected. Exiting gracefully...")
    running = False


def get_charging_status_str(status_byte):
    """Converts the status byte to a readable string"""
    if status_byte == 0x01:
        return "Discharging"
    elif status_byte == 0x03:
        return "Charging"
    # Add more conditions here if you discover other states (e.g., fully charged)
    else:
        return f"Unknown (0x{status_byte:02x})"


def log_battery_status(battery_level):
    """Logs the battery status to the specified file."""
    try:
        # Get current timestamps
        # Convert time.time() float to integer
        timestamp_unix = int(time.time())
        now = datetime.now()
        timestamp_formatted = now.strftime("%d/%m/%Y %H:%M:%S")  # DD/MM/YYYY HH:MM:SS

        # Format the log line
        log_line = f"{timestamp_unix}|{battery_level}|{timestamp_formatted}\n"

        # Open the file in append mode ('a') and write the line
        # 'with open(...)' ensures the file is closed automatically
        with open(LOG_FILE, "a") as f:
            f.write(log_line)

    except IOError as e:
        print(f"\nError writing to log file {LOG_FILE}: {e}")
    except Exception as e:
        print(f"\nUnexpected error during logging: {e}")


# Register the signal handler for Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

last_battery_level = -1
last_charging_status_byte = -1
last_update_time = 0

try:
    print(f"Attempting to open device path: {DEVICE_PATH.decode()}")
    # Open the device once
    device = hid.device()
    device.open_path(DEVICE_PATH)
    device.set_nonblocking(1)  # Use non-blocking mode

    print(
        f"Device opened: {device.get_manufacturer_string()} - {device.get_product_string()}"
    )
    if ENABLE_LOGGING:
        print(f"Logging battery status to {LOG_FILE}")
    print("Monitoring battery status... (Press Ctrl+C to stop)")

    while running:
        report = device.read(64)  # Read up to 64 bytes

        current_time = time.time()
        status_changed = False

        if report:
            # Check if it's the battery report we expect
            if report[0] == REPORT_ID_BATTERY and len(report) >= EXPECTED_REPORT_LENGTH:
                current_charging_status_byte = report[CHARGING_STATUS_INDEX]
                current_battery_level = report[BATTERY_LEVEL_INDEX]

                # --- Log the battery status ---
                if ENABLE_LOGGING:
                    log_battery_status(current_battery_level)
                # ------------------------------

                # Check if status changed since last report
                if (
                    current_battery_level != last_battery_level
                    or current_charging_status_byte != last_charging_status_byte
                ):
                    last_battery_level = current_battery_level
                    last_charging_status_byte = current_charging_status_byte
                    status_changed = True

        # Print status to console if it changed OR if UPDATE_INTERVAL has passed
        if status_changed or (current_time - last_update_time > UPDATE_INTERVAL):
            if (
                last_battery_level != -1
            ):  # Check if we have received at least one valid report
                charging_str = get_charging_status_str(last_charging_status_byte)
                # Use \r to overwrite the previous line, and end='' to prevent newline
                print(
                    f"\rStatus: {charging_str} | Battery: {last_battery_level}%   ",
                    end="",
                )
                sys.stdout.flush()  # Make sure it prints immediately
                last_update_time = current_time
            elif not report and current_time - last_update_time > UPDATE_INTERVAL:
                # If no valid report received yet, print waiting message periodically
                print(f"\rWaiting for first battery report...", end="")
                sys.stdout.flush()  # Make sure it prints immediately
                last_update_time = current_time

        # Small sleep to prevent CPU hogging
        time.sleep(0.1)  # Check roughly 10 times per second

except hid.HIDException as ex:
    print(f"\nError opening or reading HID device: {ex}")
    print(f"Ensure the device path '{DEVICE_PATH.decode()}' exists, is correct,")
    print("and you have the necessary permissions (check udev rules).")
    print("Try running with 'sudo' to test for permission issues.")
except FileNotFoundError:
    print(f"\nError: Device path '{DEVICE_PATH.decode()}' not found.")
    print("Ensure the mouse dongle is plugged in.")
except Exception as ex:
    print(f"\nAn unexpected error occurred: {ex}")
finally:
    if device:
        print("\nClosing device.")
        device.close()
    print("Exited.")
