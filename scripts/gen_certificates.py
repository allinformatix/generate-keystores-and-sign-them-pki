import yaml
import os
import subprocess
import shutil
import datetime
import tempfile

# Load configuration
def load_config(config_path):
    with open(config_path, 'r') as config_file:
        return yaml.safe_load(config_file)

# Create certificates (NGINX, Apache, or RDP) based on YAML information
def create_certificates(service_name, cert_info, cert_path, private_key_path, ca_cert, ca_private_key):
    print(f"Creating certificates for {service_name}...")

    # Extract relevant information from cert_info
    country = cert_info['organization_country_code']
    state = cert_info['organization_state']
    locality = cert_info['organization_city']
    org_name = cert_info['organization_name']
    org_unit = cert_info['organization_dept']
    common_name = cert_info['service_main_name']

    # Generate unique filenames for each certificate and key
    private_key = f"{private_key_path}/{service_name}_{common_name}.key"
    csr_file = f"{cert_path}/{service_name}_{common_name}.csr"
    signed_cert_file = f"{cert_path}/{service_name}_{common_name}_signed.crt"

    # Generate private key
    subprocess.run([
        "openssl", "genpkey", "-algorithm", "RSA", "-out", private_key, "-pkeyopt", "rsa_keygen_bits:2048"
    ], check=True)

    # Generate CSR using the extracted information
    subprocess.run([
        "openssl", "req", "-new", "-key", private_key, "-out", csr_file, "-subj",
        f"/CN={common_name}/O={org_name}/OU={org_unit}/L={locality}/ST={state}/C={country}"
    ], check=True)

    # Write CA certificate and private key to temporary files
    with tempfile.NamedTemporaryFile(delete=False, suffix=".crt") as ca_cert_file, \
         tempfile.NamedTemporaryFile(delete=False, suffix=".key") as ca_key_file:

        ca_cert_file.write(ca_cert.encode())
        ca_key_file.write(ca_private_key.encode())
        ca_cert_file.flush()
        ca_key_file.flush()

        # Sign CSR with CA private key
        openssl_cmd = [
            "openssl", "x509", "-req", "-in", csr_file, "-CA", ca_cert_file.name,
            "-CAkey", ca_key_file.name, "-CAcreateserial", "-out", signed_cert_file, "-days", "365", "-sha256"
        ]
        print(f"Executing OpenSSL command for {service_name}: {openssl_cmd}")
        result = subprocess.run(openssl_cmd, check=False)
        if result.returncode != 0:
            print(f"Error signing CSR for {service_name}: {result.stderr}")
        else:
            print(f"Certificates for {service_name} ({common_name}) created successfully.")

    # Clean up temporary files
    os.remove(ca_cert_file.name)
    os.remove(ca_key_file.name)

    # Return the paths to the generated files for use in creating the PFX file (for RDP)
    return private_key, signed_cert_file

# Create PKCS#12 (PFX) certificate for Microsoft RDP
def create_pfx_certificate(service_name, cert_path, private_key_path, ca_cert, common_name):
    print(f"Creating PFX certificate for Microsoft RDP: {service_name}...")

    # Ensure the correct filenames for private key and signed certificate
    private_key = f"{private_key_path}/{service_name}_{common_name}.key"
    signed_cert_file = f"{cert_path}/{service_name}_{common_name}_signed.crt"
    pfx_file = f"{cert_path}/{service_name}_{common_name}.pfx"

    # Check if private key and signed certificate exist
    if not os.path.exists(private_key) or not os.path.exists(signed_cert_file):
        print(f"Error: Private key or signed certificate for {service_name} is missing.")
        return

    # Write CA certificate to temporary file
    with tempfile.NamedTemporaryFile(delete=False) as ca_cert_file:
        ca_cert_file.write(ca_cert.encode())
        ca_cert_file.flush()

        # Generate PFX file using OpenSSL
        openssl_cmd = [
            "openssl", "pkcs12", "-export", "-out", pfx_file, "-inkey", private_key,
            "-in", signed_cert_file, "-certfile", ca_cert_file.name, "-password", "pass:yourpassword"
        ]
        print(f"Executing OpenSSL command for {service_name}: {openssl_cmd}")
        result = subprocess.run(openssl_cmd, check=False)
        if result.returncode != 0:
            print(f"Error creating PFX for {service_name}: {result.stderr}")
        else:
            print(f"PFX file for {service_name} created successfully: {pfx_file}")

    # Clean up the temporary CA certificate file
    os.remove(ca_cert_file.name)

# Main function to handle truststore and keystore creation
def main(config):
    # Load the stage and secret file path from the config
    stage = config['stage']
    secret_file_path = config['secret_file_path']
    ca_name = config['ca_name']

    # Load the content of the secret file
    with open(secret_file_path, 'r') as f:
        secret_config = yaml.safe_load(f)

    ca_cert = secret_config['ca_certificates']['stage'][stage][ca_name]['public_key']
    ca_private_key = secret_config['ca_certificates']['stage'][stage][ca_name]['private_key']

    # Specify paths for certificates and private keys
    cert_path = './tmp/certificates'
    private_key_path = './tmp/private_keys'

    # Create directories if they don't exist
    os.makedirs(cert_path, exist_ok=True)
    os.makedirs(private_key_path, exist_ok=True)

    # Generate certificates for each service (NGINX, Apache, RDP)
    for keystore in secret_config['java_key_stores']['stage'][stage]['keystores'].values():
        for entry_name, entry_info in keystore['entries'].items():
            # Generate certificates for NGINX and Apache
            create_certificates('nginx', entry_info, cert_path, private_key_path, ca_cert, ca_private_key)
            create_certificates('apache', entry_info, cert_path, private_key_path, ca_cert, ca_private_key)

            # Generate PFX for RDP
            create_certificates('rdp', entry_info, cert_path, private_key_path, ca_cert, ca_private_key)  # This ensures RDP keys are generated first
            create_pfx_certificate('rdp', cert_path, private_key_path, ca_cert, entry_info['service_main_name'])

if __name__ == "__main__":
    # Load external configuration file (dynamic parameters)
    config_path = './configs/config.yaml'  # Path to the configuration file
    config = load_config(config_path)
    main(config)
