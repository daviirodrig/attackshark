#!/bin/bash

# Mouse Battery Monitor Script
# Path: /usr/local/bin/mouse-battery-monitor.sh

# Configuration
BATTERY_SCRIPT="/run/media/davi/EndData/Projects/attackshark/app/utils/monitorBattery.py"
SOUND_FILE="/home/davi/low_battery.mp3"
LOG_FILE="/var/log/mouse-battery-monitor.log"
LAST_NOTIFICATION_FILE="/tmp/mouse_battery_last_notification"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Function to send notification
send_notification() {
    local battery_level=$1
    local current_time=$(date +%s)
    local last_notification_time=0
    
    # Check if we've sent a notification recently (within 5 minutes)
    if [[ -f "$LAST_NOTIFICATION_FILE" ]]; then
        last_notification_time=$(cat "$LAST_NOTIFICATION_FILE" 2>/dev/null || echo 0)
    fi
    
    local time_diff=$((current_time - last_notification_time))
    
    # Only send notification if more than 5 minutes have passed
    if [[ $time_diff -gt 300 ]]; then
        # Get current user using loginctl (works well with Wayland)
        CURRENT_USER=""
        if command -v loginctl >/dev/null 2>&1; then
            CURRENT_USER=$(loginctl list-sessions --no-legend | grep -E "(seat|tty)" | head -n1 | awk '{print $3}')
        fi
        
        # Fallback to who command
        if [[ -z "$CURRENT_USER" ]]; then
            CURRENT_USER=$(who | head -n1 | awk '{print $1}')
        fi
        
        if [[ -n "$CURRENT_USER" ]]; then
            # Get user's runtime directory for Wayland/X11 compatibility
            USER_RUNTIME_DIR="/run/user/$(id -u "$CURRENT_USER")"
            
            # Send notification using notify-send (works best with Wayland)
            if sudo -u "$CURRENT_USER" XDG_RUNTIME_DIR="$USER_RUNTIME_DIR" notify-send "Mouse Battery Low" "Battery at ${battery_level}%" --urgency=critical --expire-time=5000 2>/dev/null; then
                log_message "Notification sent successfully for battery level: ${battery_level}%"
                
                # Play sound
                if [[ -f "$SOUND_FILE" ]]; then
                    sudo -u "$CURRENT_USER" XDG_RUNTIME_DIR="$USER_RUNTIME_DIR" paplay "$SOUND_FILE" 2>/dev/null &
                    log_message "Sound played successfully"
                fi
                
                # Update last notification time
                echo "$current_time" > "$LAST_NOTIFICATION_FILE"
            else
                log_message "Failed to send notification for battery level: ${battery_level}%"
            fi
        else
            log_message "Could not determine current user for notification"
        fi
    else
        log_message "Notification skipped (recently sent) for battery level: ${battery_level}%"
    fi
}

# Main monitoring function
monitor_battery() {
    log_message "Starting battery monitoring check"
    
    # Run the Python script with a timeout and capture output
    if command -v timeout >/dev/null 2>&1; then
        # Use timeout command if available
        output=$(timeout 10s sudo python "$BATTERY_SCRIPT" 2>&1 | tail -n 5)
    else
        # Fallback: run script in background and kill after 10 seconds
        sudo python "$BATTERY_SCRIPT" > /tmp/battery_output.txt 2>&1 &
        script_pid=$!
        sleep 10
        kill $script_pid 2>/dev/null
        wait $script_pid 2>/dev/null
        output=$(tail -n 5 /tmp/battery_output.txt 2>/dev/null)
    fi
    
    # Extract battery percentage from output
    battery_level=$(echo "$output" | grep -o "Battery: [0-9]*%" | tail -n1 | grep -o "[0-9]*")
    
    if [[ -n "$battery_level" && "$battery_level" =~ ^[0-9]+$ ]]; then
        log_message "Battery level detected: ${battery_level}%"
        
        # Check if battery is at critical levels
        if [[ $battery_level -le 15 ]]; then
            send_notification "$battery_level"
        elif [[ $battery_level -eq 20 || $battery_level -eq 30 ]]; then
            send_notification "$battery_level"
        fi
    else
        log_message "Could not extract battery level from output: $output"
    fi
}

# Run the monitoring function
monitor_battery
