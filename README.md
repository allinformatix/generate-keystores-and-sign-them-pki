# Create Java Keystores with Signed Certificates (Offline)**

This program simplifies the process of creating Java KeyStores with key pairs and signing them with certificates from a Certificate Authority (CA), particularly useful within a Public Key Infrastructure (PKI) IT environment. 

The tool automates the otherwise tedious process, generating KeyStores and TrustStores with signed certificates, saving time and reducing errors.

The final output files will be stored in the `./tmp/` directory.

## **IMPORTANT!**
⚠️ **Security Notice**: This program uses test data and is intended for educational or testing purposes. Be extremely cautious when dealing with your own private keys, especially if you are using your own CA. Mismanagement of CA private keys can lead to serious security vulnerabilities.

---

## **Requirements**
The script is developed on **macOS**, but can be adapted for **Windows** and **Linux** environments as well. The following dependencies and setup are required to run the script:

### **Environment Setup**
- **Python 3.x**: Ensure you have Python 3 installed. This script requires Python 3.x to run.
- **Java**: You need a Java Runtime Environment (JRE) or Java Development Kit (JDK). Make sure `JAVA_HOME` is set in your environment.
- **Virtual Environment**: This script utilizes Python's virtual environments to isolate dependencies.

### **Python Libraries**
The script imports and uses the following Python libraries:
- `yaml`: For parsing configuration files.
- `os`, `subprocess`, `shutil`, `datetime`, `tempfile`, `glob`: These are standard Python libraries and do not require installation.

If any required library is missing, the setup script will install it automatically.

### **Ensure `JAVA_HOME` is Set**
Before running the script, ensure that the `JAVA_HOME` environment variable is set to your Java installation. You can check this by running the following command:
```bash
echo $JAVA_HOME
```
If it’s not set, you can configure it by adding the following to your `.bashrc`, `.zshrc`, or `.profile`:
```bash
export JAVA_HOME=$(/usr/libexec/java_home)
```
For **Linux** users, it may look like:
```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
```

### **Folder Structure**
```text
.
├── scripts
│   ├── setup.sh  # Script to set up the environment and dependencies
│   ├── gen_keyStores_and_sign.py  # Main Python script to generate and sign keystores
│   └── config.yaml  # Configuration file defining key details (keystore paths, CA certificates, etc.)
├── venv/  # Virtual environment directory (created by setup.sh)
├── tmp/  # Temporary directory where keystores and truststores will be generated
```

---

## **How to Run the Program**

Follow these steps to run the script and create the keystores:

### **Step 1: Set Up the Environment**
Run the following script to check your Python installation, create a virtual environment, and install required dependencies (like `PyYAML`):

```bash
./scripts/setup.sh
```

This script will:
- Verify that Python 3 is installed.
- Create a Python virtual environment in the `venv/` directory if it doesn't exist.
- Install the required dependencies (like `PyYAML`) inside the virtual environment.

### **Step 2: Activate the Virtual Environment**
Once the setup is complete, activate the virtual environment to isolate the Python dependencies:

```bash
source venv/bin/activate
```

You must activate the virtual environment each time you run the script to ensure it uses the correct Python environment.

### **Step 3: Run the Python Script**
After activating the virtual environment, run the main Python script to generate the keystores, create key pairs, and sign them with your CA:

```bash
python3 scripts/gen_keyStores_and_sign.py
```

The script will:
- Generate Java KeyStores and TrustStores based on the configuration in `config.yaml`.
- Create key pairs and request certificates.
- Sign the certificates using the specified CA.
- Store all output files in the `./tmp/` directory.

### **Step 4: View the Results**
All final keystore and truststore files, along with the signed certificates, will be available in the `./tmp/` directory.

```bash
ls ./tmp/
```

---

## **Customizing the Configuration**

The configuration for keystores, truststores, and CA certificates is stored in the `config.yaml` file. You can modify this file to adjust the key pair settings, certificate paths, and signing process. Below is a sample structure of `config.yaml`:

```yaml
java_key_stores:
  stage:
    prod:
      truststores:
        truststore1:
          path: /tmp/truststore1
          password: changeit
      keystores:
        keystore1:
          path: /tmp/keystore1
          entries:
            entry1:
              service_main_name: example-service
              domain_name: example.com
              organization_name: Example Inc.
              keystore_password: password
ca_certificates:
  stage:
    prod:
      my_ca:
        public_key: |
          -----BEGIN CERTIFICATE-----
          [CA CERTIFICATE CONTENT]
          -----END CERTIFICATE-----
        private_key: |
          -----BEGIN PRIVATE KEY-----
          [PRIVATE KEY CONTENT]
          -----END PRIVATE KEY-----
```

Modify this file to define your own keystore paths, entries, and certificates.

---

## **Cleaning Up**

To remove the virtual environment and start from scratch:
1. Deactivate the virtual environment by running:
   ```bash
   deactivate
   ```
2. Delete the `venv/` directory:
   ```bash
   rm -rf venv/
   ```

---

## **Troubleshooting**

- **ModuleNotFoundError: No module named 'yaml'**
  If you encounter this error, ensure that you have activated the virtual environment using `source venv/bin/activate` and that `PyYAML` is installed.

- **Permission Denied Errors**
  Make sure you have the necessary permissions to execute the script (`setup.sh`) and write to the `tmp/` directory. You can make the script executable with:
  ```bash
  chmod +x ./scripts/setup.sh
  ```

---

This guide should help you get started with the script, from setting up your environment to generating signed Java keystores and truststores. If you encounter any issues, refer to the troubleshooting section or consult the configuration details.