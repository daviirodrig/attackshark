# attackshark

This is a simple script to read battery levels from a usb wireless mouse, Attackshark X11 on linux.

### 1. Clone the repository

```bash
git clone https://github.com/daviirodrig/attackshark.git
cd attackshark
```

### 2. Set Up Python Environment

It’s recommended to use a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Script Paths

Many scripts in this repo use hardcoded or example paths.  
**Update all relevant file paths in the scripts to match your environment before running.**

- Check for path variables at the top of each script.
- Review any references to input/output directories or resources.

### 4. Install and Configure systemd Services

This project uses systemd for managing background services.  
To enable services:

1. Copy the `.service` files to your systemd directory, for example:
    ```bash
    sudo cp systemd/*.service /etc/systemd/system/
    ```
2. Edit the `.service` files as needed (e.g. update `ExecStart` paths).
3. Reload systemd and enable/start the services:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable <service-name>.service
    sudo systemctl start <service-name>.service
    ```

### 5. Usage

After configuring, run scripts manually or let systemd manage them as background services.

---

## Notes

- This repo is meant to be adapted—**edit scripts and service files to fit your specific setup**.
- Double-check permissions and environment variables.
- For troubleshooting, check logs in your systemd journal and Python error traces.

---
