#!/usr/bin/env python3
"""
Enhanced Environment Variables Loader
Secure loading with validation and encryption support
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import base64
from cryptography.fernet import Fernet


# Safe logger setup
logger = None

def get_logger():
    """Get logger instance safely"""
    global logger
    if logger is None:
        try:
            import logging
            logger = logging.getLogger(__name__)
        except:
            logger = None
    return logger

def safe_log_info(message):
    """Safe logging info"""
    try:
        log = get_logger()
        if log:
            log.info(message)
        else:
            print("INFO: {}".format(message))
    except:
        print("INFO: {}".format(message))

def safe_log_error(message):
    """Safe logging error"""
    try:
        log = get_logger()
        if log:
            log.error(message)
        else:
            print("ERROR: {}".format(message))
    except:
        print("ERROR: {}".format(message))

def safe_log_warning(message):
    """Safe logging warning"""
    try:
        log = get_logger()
        if log:
            log.warning(message)
        else:
            print("WARNING: {}".format(message))
    except:
        print("WARNING: {}".format(message))


class SecureEnvLoader:
    """Enhanced environment loader with security features"""
    
    def __init__(self, env_path: Optional[str] = None):
        self.env_path = Path(env_path) if env_path else Path(__file__).parent / '.env'
        self.encryption_key = self._get_or_create_key()
        
    def _get_or_create_key(self) -> Optional[bytes]:
        """Get or create encryption key"""
        key_file = Path(__file__).parent / '.env.key'
        try:
            if key_file.exists():
                with open(key_file, 'rb') as f:
                    return f.read()
            else:
                # Create new key for first time
                key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(key)
                safe_log_info("🔑 New encryption key generated")
                return key
        except Exception as e:
            safe_log_warning("⚠️ Could not handle encryption key: {}".format(e))
            return None
    
    def encrypt_value(self, value: str) -> str:
        """Encrypt sensitive value"""
        if not self.encryption_key:
            return value
        try:
            f = Fernet(self.encryption_key)
            encrypted = f.encrypt(value.encode())
            return "ENC:{}".format(base64.b64encode(encrypted).decode())
        except Exception as e:
            safe_log_warning("⚠️ Encryption failed: {}".format(e))
            return value
    
    def decrypt_value(self, value: str) -> str:
        """Decrypt encrypted value"""
        if not value.startswith("ENC:") or not self.encryption_key:
            return value
        try:
            f = Fernet(self.encryption_key)
            encrypted_data = base64.b64decode(value[4:])
            return f.decrypt(encrypted_data).decode()
        except Exception as e:
            safe_log_warning("⚠️ Decryption failed: {}".format(e))
            return value
    
    def load_env_file(self) -> bool:
        """Load environment variables with enhanced security"""
        if not self.env_path.exists():
            safe_log_error("❌ Environment file not found: {}".format(self.env_path))
            return False
        
        try:
            loaded_vars = 0
            with open(self.env_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse key=value pairs
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if (value.startswith('"') and value.endswith('"')) or \
                           (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                        
                        # Decrypt if encrypted
                        if value.startswith("ENC:"):
                            value = self.decrypt_value(value)
                        
                        # Set environment variable
                        os.environ[key] = value
                        loaded_vars += 1
                    else:
                        safe_log_warning("⚠️ Invalid format at line {}: {}".format(line_num, line))
            
            safe_log_info("✅ Loaded {} environment variables from: {}".format(loaded_vars, self.env_path))
            return True
            
        except Exception as e:
            safe_log_error("❌ Error loading environment file: {}".format(e))
            return False
    
    def validate_required_vars(self) -> bool:
        """Enhanced validation with detailed feedback"""
        required_vars = {
            'ZABBIX_URL': 'Zabbix API endpoint URL',
            'ZABBIX_USER': 'Zabbix username',
            'ZABBIX_PASS': 'Zabbix password',
            'EMAIL_USERNAME': 'SMTP username',
            'EMAIL_PASSWORD': 'SMTP password/app password',
            'SENDER_EMAIL': 'Email sender address',
            'TO_EMAILS': 'Recipient email addresses'
        }
        
        missing_vars = []
        invalid_vars = []
        
        for var, description in required_vars.items():
            value = os.getenv(var)
            if not value:
                missing_vars.append("{} - {description}".format(var))
            else:
                # Basic validation
                if var.endswith('_EMAIL') or var == 'TO_EMAILS':
                    if '@' not in value:
                        invalid_vars.append("{} - Invalid email format".format(var))
                elif var == 'ZABBIX_URL':
                    if not (value.startswith('http://') or value.startswith('https://')):
                        invalid_vars.append("{} - Must be valid URL".format(var))
        
        if missing_vars or invalid_vars:
            safe_log_error("❌ Configuration validation failed:")
            if missing_vars:
                safe_log_error("Missing variables:")
                for var in missing_vars:
                    safe_log_error("   - {}".format(var))
            if invalid_vars:
                safe_log_error("Invalid variables:")
                for var in invalid_vars:
                    safe_log_error("   - {}".format(var))
            return False
        
        safe_log_info("✅ All required environment variables validated successfully")
        return True
    
    def show_config_summary(self):
        """Show configuration summary with security"""
        sensitive_vars = ['PASS', 'PASSWORD', 'KEY', 'SECRET', 'TOKEN']
        
        config_groups = {
            'Zabbix Settings': ['ZABBIX_URL', 'ZABBIX_USER', 'ZABBIX_PASS', 'ZABBIX_TIMEOUT'],
            'Email Settings': ['SMTP_SERVER', 'SMTP_PORT', 'EMAIL_USERNAME', 'EMAIL_PASSWORD', 
                             'SENDER_EMAIL', 'SENDER_NAME', 'TO_EMAILS'],
            'Report Settings': ['REPORT_OUTPUT_DIR', 'REPORT_TEMPLATE_DIR', 'COMPANY_LOGO'],
            'Logging Settings': ['LOG_LEVEL', 'LOG_DIR']
        }
        
        print("\n" + "="*60)
        print("📋 VM DAILY REPORT - CONFIGURATION SUMMARY")
        print("="*60)
        
        for group_name, vars_list in config_groups.items():
            print("\n🔧 {}:".format(group_name))
            print("-" * 40)
            
            for var in vars_list:
                value = os.getenv(var)
                if value:
                    # Hide sensitive data
                    if any(sensitive in var.upper() for sensitive in sensitive_vars):
                        display_value = "***ENCRYPTED***" if value.startswith("ENC:") else "***HIDDEN***"
                    else:
                        display_value = value
                    print("✅ {}: {display_value}".format(var))
                else:
                    print("❌ {}: Not set".format(var))
        
        print("\n" + "="*60)
        print("🔒 Security: Sensitive values are encrypted/hidden")
        print("📅 Generated:", __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print("="*60)

# Backward compatibility functions
def load_env_file(env_path: Optional[str] = None) -> bool:
    """Backward compatible load function"""
    loader = SecureEnvLoader(env_path)
    return loader.load_env_file()

def check_required_vars() -> bool:
    """Backward compatible validation function"""
    loader = SecureEnvLoader()
    return loader.validate_required_vars()

def show_current_config():
    """Backward compatible config display"""
    loader = SecureEnvLoader()
    loader.show_config_summary()

# Enhanced utility functions
def get_config_dict() -> Dict[str, Any]:
    """Get configuration as dictionary"""
    return {
        'zabbix': {
            'url': os.getenv('ZABBIX_URL'),
            'user': os.getenv('ZABBIX_USER'),
            'password': os.getenv('ZABBIX_PASS'),
            'timeout': int(os.getenv('ZABBIX_TIMEOUT', '30')),
            'verify_ssl': os.getenv('ZABBIX_VERIFY_SSL', 'true').lower() == 'true'
        },
        'email': {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'username': os.getenv('EMAIL_USERNAME'),
            'password': os.getenv('EMAIL_PASSWORD'),
            'sender_email': os.getenv('SENDER_EMAIL'),
            'sender_name': os.getenv('SENDER_NAME', 'VM Monitoring System'),
            'to_emails': [email.strip() for email in os.getenv('TO_EMAILS', '').split(',') if email.strip()],
            'cc_emails': [email.strip() for email in os.getenv('CC_EMAILS', '').split(',') if email.strip()],
            'bcc_emails': [email.strip() for email in os.getenv('BCC_EMAILS', '').split(',') if email.strip()],
            'use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        },
        'report': {
            'output_dir': os.getenv('REPORT_OUTPUT_DIR', 'output'),
            'template_dir': os.getenv('REPORT_TEMPLATE_DIR', 'templates'),
            'static_dir': os.getenv('REPORT_STATIC_DIR', 'static'),
            'company_logo': os.getenv('COMPANY_LOGO', 'tech_corp')
        },
        'logging': {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'dir': os.getenv('LOG_DIR', 'logs')
        }
    }

def setup_logging():
    """Setup enhanced logging with external library suppression"""
    import logging
    import logging.handlers
    
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_dir = Path(os.getenv('LOG_DIR', 'logs'))
    
    # Create log directory
    log_dir.mkdir(exist_ok=True)
    
    # Suppress verbose logging from external libraries
    logging.getLogger('weasyprint').setLevel(logging.CRITICAL)
    logging.getLogger('fontTools').setLevel(logging.CRITICAL)
    logging.getLogger('fontTools.subset').setLevel(logging.CRITICAL)
    logging.getLogger('fontTools.ttLib').setLevel(logging.CRITICAL)
    logging.getLogger('fontTools.ttLib.ttFont').setLevel(logging.CRITICAL)
    logging.getLogger('fontTools.subset.timer').setLevel(logging.CRITICAL)
    logging.getLogger('pyzabbix.api').setLevel(logging.WARNING)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'vm_daily_report.log',
        maxBytes=int(os.getenv('LOG_MAX_BYTES', '10485760')),  # 10MB
        backupCount=int(os.getenv('LOG_BACKUP_COUNT', '5'))
    )
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, log_level))
    
    # Configure root logger  
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger

if __name__ == "__main__":
    # Setup logging first
    setup_logging()
    
    # Load and validate environment
    print("🚀 VM Daily Report - Environment Configuration Tool")
    print("="*60)
    
    loader = SecureEnvLoader()
    
    if loader.load_env_file():
        if loader.validate_required_vars():
            loader.show_config_summary()
            print("\n✅ Environment configuration is ready!")
        else:
            print("\n❌ Configuration validation failed!")
            exit(1)
    else:
        print("\n❌ Failed to load environment configuration!")
        exit(1)
