import os
import subprocess

os.makedirs('ssl', exist_ok=True)

# 1. OpenSSL Config with proper Subject Alternative Names (SAN)
config_content = """
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_ca
prompt = no

[req_distinguished_name]
CN = FleetOps Local CA

[v3_ca]
basicConstraints = critical,CA:TRUE
keyUsage = critical, digitalSignature, cRLSign, keyCertSign
subjectKeyIdentifier = hash

[server_cert]
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = fleetops.local
DNS.2 = *.fleetops.local
DNS.3 = localhost
IP.1 = 127.0.0.1
"""

with open("ssl/openssl.cnf", "w") as f:
    f.write(config_content.strip())

print("Creating Local Root CA...")
# Generate CA Private Key & Root Certificate
subprocess.run([
    "openssl", "req", "-x509", "-new", "-nodes",
    "-keyout", "ssl/ca.key",
    "-sha256", "-days", "1024",
    "-out", "ssl/ca.crt",
    "-config", "ssl/openssl.cnf",
    "-extensions", "v3_ca"
], check=True)

print("Creating Server Certificate for *.fleetops.local...")
# Generate Server Private Key
subprocess.run([
    "openssl", "genrsa", "-out", "ssl/key.pem", "2048"
], check=True)

# Generate CSR
subprocess.run([
    "openssl", "req", "-new",
    "-key", "ssl/key.pem",
    "-out", "ssl/server.csr",
    "-subj", "/CN=*.fleetops.local"
], check=True)

# Sign Server Certificate with Local Root CA
subprocess.run([
    "openssl", "x509", "-req",
    "-in", "ssl/server.csr",
    "-CA", "ssl/ca.crt",
    "-CAkey", "ssl/ca.key",
    "-CAcreateserial",
    "-out", "ssl/cert.pem",
    "-days", "365",
    "-sha256",
    "-extfile", "ssl/openssl.cnf",
    "-extensions", "server_cert"
], check=True)

print("✅ Complete! Created ssl/ca.crt and ssl/cert.pem with full CA validation.")