import pandas as pd
import netaddr
from bisect import bisect
import re

# Load the IP to location data once at the start
ips = pd.read_csv("ip2location.csv")

def lookup_region(ip):
    """Finds the region for a given IP address."""
    # Replace letters with zeros for anonymized IPs
    ip_numeric = re.sub(r'[a-zA-Z]', '0', ip)
    ip_int = int(netaddr.IPAddress(ip_numeric))
    
    # Use bisect to find the correct region
    idx = bisect(ips['low'], ip_int)
    return ips.iloc[idx-1]['region'] if idx > 0 else "Unknown"

class Filing:
    """Class representing an EDGAR filing document."""
    def __init__(self, html):
        self.dates = self.extract_dates(html)
        self.sic = self.extract_sic(html)
        self.addresses = self.extract_addresses(html)

    def extract_dates(self, html):
        """Extracts dates from the filing."""
        return re.findall(r'\b(19|20)\d{2}-\d{2}-\d{2}\b', html)

    def extract_sic(self, html):
        """Extracts the SIC code from the filing."""
        match = re.search(r'SIC=\s*(\d+)', html)
        return int(match.group(1)) if match else None

    def extract_addresses(self, html):
        """Extracts addresses from the filing."""
        addr_htmls = re.findall(r'<div class="mailer">([\s\S]+?)</div>', html)
        addresses = []
        for addr_html in addr_htmls:
            lines = re.findall(r'<span class="mailerAddress">([\s\S]+?)</span>', addr_html)
            cleaned_lines = [line.strip() for line in lines if line.strip()]
            if cleaned_lines:
                addresses.append("\n".join(cleaned_lines))
        return addresses

    def state(self):
        """Determines the state abbreviation from the addresses."""
        for addr in self.addresses:
            match = re.search(r'\b[A-Z]{2}\s\d{5}\b', addr)
            if match:
                return match.group(0).split()[0]
        return None
