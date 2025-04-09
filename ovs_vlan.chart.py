# -*- coding: utf-8 -*-
# Description: Netdata python.d plugin for monitoring OVS VLAN port assignments
# Author: [Your Name or Organization]
# Note: Ensure the netdata user has passwordless sudo access for ovs-vsctl commands.

import subprocess
from bases.FrameworkServices.SimpleService import SimpleService

# Plugin default configuration
priority = 90000          # Chart priority (order in the dashboard)
update_every = 1          # Update frequency (seconds)

# Chart definitions for Netdata
ORDER = ['vlan_ports']
CHARTS = {
    'vlan_ports': {
        'options': [None, 'OVS VLAN Port Assignments', 'ports', 'OVS', 'ovs.vlan_ports', 'stacked'],
        'lines': [
            ['assigned',   'Assigned',   'absolute', 1, 1, '#ff0000'],  # red area for assigned ports
            ['unassigned', 'Unassigned', 'absolute', 1, 1, '#00ff00']   # green area for unassigned ports
        ]
    }
}

class Service(SimpleService):
    def __init__(self, configuration=None, name=None):
        """Initialize the service and define charts."""
        super(Service, self).__init__(configuration=configuration, name=name)
        self.order = ORDER
        self.definitions = CHARTS

    def check(self):
        """
        Check if ovs-vsctl is accessible (requires sudo privileges).
        Returns True if the check succeeds, False otherwise.
        """
        try:
            # Test command to ensure OVS is reachable (using sudo)
            subprocess.run(
                ['sudo', 'ovs-vsctl', 'show'],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5
            )
        except Exception as e:
            # Log an error if OVS command fails
            self.error(f"OVS VLAN plugin check failed: {e}")
            return False
        return True

    def get_data(self):
        """
        Collect the number of OVS ports with VLAN assignments and without.
        Always return data (even if unchanged) to force chart update.
        """
        assigned_count = 0
        unassigned_count = 0

        try:
            # Run the ovs-vsctl command to list Port details (requires sudo)
            output = subprocess.check_output(
                ['sudo', 'ovs-vsctl', 'list', 'Port'], 
                text=True, timeout=5
            )
        except Exception as e:
            # Log the error and return None to indicate a temporary data collection issue
            self.error(f"Failed to run ovs-vsctl: {e}")
            return None

        # Each OVS Port entry is separated by a blank line in the output
        port_blocks = output.strip().split("\n\n")
        for block in port_blocks:
            if not block.strip():
                continue  # skip any empty segments
            # Assume port is unassigned until we find a VLAN tag/trunk
            port_assigned = False
            for line in block.splitlines():
                line = line.strip()
                if line.startswith("tag"):
                    # Example line: tag                 : 100   (assigned) or tag                 : [] (none)
                    if not line.endswith(": []"):
                        port_assigned = True
                elif line.startswith("trunks"):
                    # Example line: trunks              : [100, 200] (assigned) or trunks              : [] (none)
                    if not line.endswith(": []"):
                        port_assigned = True
            if port_assigned:
                assigned_count += 1
            else:
                unassigned_count += 1

        # Debug log to confirm values are being updated every cycle
        self.debug(f"Updating OVS VLAN ports chart: assigned={assigned_count}, unassigned={unassigned_count}")

        # Return the data dict for Netdata (always provide data to avoid skipping updates)
        return {'assigned': assigned_count, 'unassigned': unassigned_count}
