import yaml
import os
import subprocess
import shutil
import datetime
import tempfile
import glob

# Load the configuration file
def load_config(config_path):
    with open(config_path, 'r') as config_file:
        return yaml.safe_load(config_file)

# Create the keystore and import signed certificates
def create_keystore(keystore_path, entries, ca_cert, ca_private_key, ca_cert_imported):
    if os.path.exists(keystore_path):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        new_keystore_path = f"{keystore_path}_{timestamp}"
        print(f"{keystore_path} exists. Renaming to {new_keystore_path}.")
        os.rename(keystore_path, new_keystore_path)

    keytool_cmd = ['keytool', '-genkeypair', '-keystore', keystore_path]

    for entry in entries.values():
        san_list = entry.get('subject_alternative_names', [])
        san_param = ','.join([f"DNS:{san}" for san in san_list if san])
        dname = f"CN={entry['service_main_name']}, O={entry['organization_name']}, " \
                f"OU={entry['organization_dept']}, L={entry['organization_city']}, " \
                f"ST={entry['organization_state']}, C={entry['organization_country_code']}"

        cmd = keytool_cmd + [
            '-alias', entry['alias'],
            '-keyalg', entry['keyalg'],
            '-keysize', str(entry['keysize']),
            '-sigalg', entry['sigalg'],
            '-storetype', entry['keystore_type'],
            '-dname', dname,
            '-storepass', entry['keystore_password'],
            '-keypass', entry['keystore_password']
        ]

        if san_param:
            cmd += ['-ext', f"san={san_param}"]

        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            print(f"Error creating keystore for {entry['alias']}: {result.stderr}")
            continue

        # Generate CSR
        csr_path = f"./tmp/{entry['alias']}.csr"
        subprocess.run(['keytool', '-certreq', '-keystore', keystore_path, 
                        '-alias', entry['alias'], '-file', csr_path, 
                        '-storepass', entry['keystore_password']], check=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.crt') as ca_cert_file, \
             tempfile.NamedTemporaryFile(delete=False, suffix='.key') as ca_key_file:

            ca_cert_path = ca_cert_file.name
            ca_key_path = ca_key_file.name

            ca_cert_file.write(ca_cert.encode())
            ca_key_file.write(ca_private_key.encode())
        
        signed_cert_path = f"./tmp/{entry['alias']}_signed.crt"
        openssl_cmd = f"openssl x509 -req -in {csr_path} -CA {ca_cert_path} -CAkey {ca_key_path} " \
                       f"-CAcreateserial -out {signed_cert_path} -days 365 -sha256"
        
        print(f"Executing OpenSSL command for {entry['alias']}: {openssl_cmd}")
        result = subprocess.run(openssl_cmd, shell=True, check=False)
        if result.returncode != 0:
            print(f"Error signing CSR for {entry['alias']}: {result.stderr}")
            continue

        # Check the content of the signed certificate
        with open(signed_cert_path, 'r') as signed_cert_file:
            signed_cert_content = signed_cert_file.read()
            print(f"Signed certificate content for {entry['alias']}:\n{signed_cert_content}")

        # Dynamic alias for the CA certificate
        ca_alias = "ca_certificate"

        # Import the CA certificate into the keystore if it hasn't been imported yet
        result = subprocess.run(['keytool', '-list', '-keystore', keystore_path, '-alias', ca_alias, '-storepass', entry['keystore_password']], check=False)
        if result.returncode != 0:  # CA certificate is not present
            print(f"Importing CA certificate into keystore for {entry['alias']}")
            result = subprocess.run(['keytool', '-importcert', '-keystore', keystore_path, 
                                     '-alias', ca_alias, '-file', ca_cert_path, 
                                     '-storepass', entry['keystore_password'], '-noprompt'], check=False)
            if result.returncode != 0:
                print(f"Error importing CA certificate for {entry['alias']}: {result.stderr}")

        # Create a file that contains the certificate chain (signed certificate + CA certificate)
        chain_cert_path = f"./tmp/{entry['alias']}_chain.crt"
        with open(chain_cert_path, 'w') as chain_cert_file:
            with open(signed_cert_path, 'r') as signed_cert_file, open(ca_cert_path, 'r') as ca_cert_file:
                chain_cert_file.write(signed_cert_file.read())  # Signed certificate first
                chain_cert_file.write(ca_cert_file.read())  # CA certificate second

        # Import the certificate chain into the keystore
        result = subprocess.run(['keytool', '-importcert', '-keystore', keystore_path, 
                                 '-alias', entry['alias'], '-file', chain_cert_path, 
                                 '-storepass', entry['keystore_password'], '-noprompt'], check=False)
        if result.returncode != 0:
            print(f"Error importing signed certificate for {entry['alias']}: {result.stderr}")

        # Clean up temporary files
        os.remove(csr_path)
        os.remove(signed_cert_path)
        os.remove(ca_cert_path)
        os.remove(ca_key_path)
        os.remove(chain_cert_path)

    return ca_cert_imported

# Create the truststore, import the CA certificate and public keys
def create_truststore(truststore_path, truststore_password, ca_cert, public_keys):
    java_home = os.environ.get('JAVA_HOME')
    if not java_home:
        raise EnvironmentError("JAVA_HOME environment variable is not set.")
    
    cacerts_path = os.path.join(java_home, 'lib', 'security', 'cacerts')

    # Check for existing ".old" truststores and delete them
    truststore_dir = os.path.dirname(truststore_path)
    truststore_base = os.path.basename(truststore_path)

    for filename in os.listdir(truststore_dir):
        if filename.startswith(truststore_base) and filename.endswith('.old'):
            old_truststore_path = os.path.join(truststore_dir, filename)
            print(f"Deleting old truststore: {old_truststore_path}")
            os.remove(old_truststore_path)

    if os.path.exists(truststore_path):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        new_truststore_path = f"{truststore_path}_{timestamp}"
        print(f"{truststore_path} exists. Renaming to {new_truststore_path}.")
        os.rename(truststore_path, new_truststore_path)
    
    shutil.copyfile(cacerts_path, truststore_path)

    result = subprocess.run([
        'keytool', '-importkeystore', 
        '-srckeystore', truststore_path, 
        '-destkeystore', truststore_path, 
        '-srcstorepass', 'changeit', 
        '-deststorepass', truststore_password
    ], check=False)

    if result.returncode != 0:
        print(f"Error updating truststore password: {result.stderr}")

    # Import public keys into the truststore
    for alias, public_key in public_keys.items():
        public_key_path = f"./tmp/{alias}_public_key.crt"
        with open(public_key_path, 'w') as public_key_file:
            public_key_file.write(public_key)

        result = subprocess.run([
            'keytool', '-importcert', '-keystore', truststore_path,
            '-alias', alias, '-file', public_key_path,
            '-storepass', truststore_password, '-noprompt'
        ], check=False)
        if result.returncode != 0:
            print(f"Error importing public key {alias} into TrustStore: {result.stderr}")

        os.remove(public_key_path)

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

    # Collect all public_key entries for the current environment (e.g., prod)
    public_keys = {}
    for ca_entry, ca_values in secret_config['ca_certificates']['stage'][stage].items():
        if 'public_key' in ca_values:
            public_keys[ca_entry] = ca_values['public_key']

    # Create truststores and keystores
    ca_cert_imported = False
    for truststore in secret_config['java_key_stores']['stage'][stage]['truststores'].values():
        create_truststore(truststore['path'], truststore['truststore_password'], ca_cert, public_keys)

    for keystore in secret_config['java_key_stores']['stage'][stage]['keystores'].values():
        ca_cert_imported = create_keystore(keystore['path'], keystore['entries'], ca_cert, ca_private_key, ca_cert_imported)

    # Remove any .old files left in the tmp directory
    old_files = glob.glob("./tmp/*.old")
    for old_file in old_files:
        print(f"Removing old file: {old_file}")
        os.remove(old_file)

if __name__ == "__main__":
    # Load external configuration file (dynamic parameters)
    config_path = './configs/config.yaml'  # Path to the configuration file
    config = load_config(config_path)
    main(config)
