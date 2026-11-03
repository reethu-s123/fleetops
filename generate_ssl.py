import os
import subprocess

# Ensure ssl directory exists
os.makedirs('ssl', exist_ok=True)

# Generate self-signed certificate for *.fleetops.local and fleetops.local
cmd = [
    "openssl", "req", "-x509", "-nodes", "-days", "365",
    "-newkey", "rsa:2048",
    "-keyout", "ssl/key.pem",
    "-out", "ssl/cert.pem",
    "-subj", "/CN=*.fleetops.local",
    "-addext", "subjectAltName=DNS:fleetops.local,DNS:*.fleetops.local"
]

subprocess.run(cmd, check=True)
print("✅ SSL Certificate generated successfully in the ssl/ folder!")