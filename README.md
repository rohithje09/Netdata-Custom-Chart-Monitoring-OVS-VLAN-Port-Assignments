# Netdata Custom Chart: Monitoring OVS VLAN Port Assignments

This guide explains how to create a custom Netdata chart using the python.d.plugin framework to monitor VLAN port assignments in Open vSwitch (OVS).

## ✨ Features
- Stack chart with Assigned (red) and Unassigned (green) port counts
- Updates every 5 seconds
- Collects data from all OVS bridges and ports
- Uses `sudo ovs-vsctl` commands to gather VLAN info

## ⚡ Prerequisites
- Netdata installed and running
- Open vSwitch (OVS) installed and configured
- The netdata user must be able to run `ovs-vsctl` with sudo (no password prompt)

### Grant Netdata sudo access:
```bash
sudo visudo
```
Add this line:
```
netdata ALL=(ALL) NOPASSWD: /usr/bin/ovs-vsctl
```
Replace `/usr/bin/ovs-vsctl` with the correct path from `which ovs-vsctl` if needed.

## 🔧 Installation

### Step 1: Plugin Script
Delete old versions:
```bash
sudo rm /usr/libexec/netdata/python.d/ovs_vlan.chart.py
```

Create new:
```bash
sudo nano /usr/libexec/netdata/python.d/ovs_vlan.chart.py
```

Paste this code:
```python
from bases.FrameworkServices.SimpleService import SimpleService
import subprocess
import re

UPDATE_EVERY = 5
PRIORITY = 60000
REORDERING = 1

CHARTS = {
    'vlan_ports': {
        'options': ['vlan_ports', 'OVS VLAN Port Assignments', 'ports', 'OVS', 'ovs_vlan.ports', 'stacked'],
        'lines': [
            ['assigned', 'Assigned', 'absolute', 1, 1, '#ff0000'],
            ['unassigned', 'Unassigned', 'absolute', 1, 1, '#00ff00']
        ]
    }
}

class Service(SimpleService):
    def __init__(self, configuration=None, name=None):
        super().__init__(configuration=configuration, name=name)
        self.order = ['vlan_ports']
        self.definitions = CHARTS

    def check(self):
        try:
            subprocess.run(['sudo', 'ovs-vsctl', 'show'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            self.error(f"OVS check failed: {e}")
            return False
        return True

    def get_data(self):
        assigned = 0
        unassigned = 0

        try:
            output = subprocess.check_output(['sudo', 'ovs-vsctl', 'list', 'Port'], text=True)
        except Exception as e:
            self.error(f"Failed to run ovs-vsctl: {e}")
            return None

        port_blocks = output.strip().split("\n\n")
        for block in port_blocks:
            if not block.strip():
                continue
            port_assigned = False
            for line in block.splitlines():
                line = line.strip()
                if line.startswith("tag") and not line.endswith(": []"):
                    port_assigned = True
                elif line.startswith("trunks") and not line.endswith(": []"):
                    port_assigned = True
            if port_assigned:
                assigned += 1
            else:
                unassigned += 1

        self.debug(f"Updating OVS VLAN ports chart: assigned={assigned}, unassigned={unassigned}")
        return {'vlan_ports': {'assigned': assigned, 'unassigned': unassigned}}
```

### Step 2: Configuration
Create plugin config:
```bash
sudo nano /etc/netdata/python.d/ovs_vlan.conf
```

Paste:
```yaml
update_every: 5

local:
  name: 'local'
```

### Step 3: Test the Plugin
```bash
sudo -u netdata /usr/libexec/netdata/plugins.d/python.d.plugin ovs_vlan debug trace
```

You should see:
```
SET 'assigned' = 13
SET 'unassigned' = 12
update => [OK]
```

### Step 4: Restart Netdata
```bash
sudo systemctl restart netdata
```

Then visit your dashboard:
```
http://<your-server-ip>:19999
```
Search for: **OVS VLAN Port Assignments**

## 💪 Done!
Your custom stacked chart is now live and updating every 5 seconds.

## ✨ Future Features (Optional)
- Per-bridge charts (br0, br1...)
- Alerts on high unassigned count
- VLAN ID usage stats
- Port → VLAN mapping view

