# Goal 6: Security & Privacy

## Context from Business Objective

This goal establishes comprehensive security and privacy controls to meet enterprise requirements and compliance standards. The security framework must protect sensitive data, prevent unauthorized access, and provide complete audit trails while maintaining system performance.

## Objective

Implement enterprise-grade security measures including network isolation, secrets management, RBAC enforcement, audit logging, and privacy controls. This ensures the RAG solution meets security compliance requirements for sensitive enterprise environments.

## Core Features

- Network isolation and HTTPS encryption
- Comprehensive secrets management
- RBAC enforcement at all levels
- Complete audit logging and monitoring
- Privacy controls and data protection
- Security scanning and vulnerability management

## Business Impact

**Meet enterprise security and compliance requirements**

### Risk Mitigation
- **Data Breach Prevention**: Multi-layered security prevents unauthorized access
- **Compliance Readiness**: Audit trails and controls support regulatory requirements
- **Incident Response**: Comprehensive logging enables rapid threat detection
- **Business Continuity**: Security measures protect against service disruption

### Trust and Adoption
- **Enterprise Confidence**: Security standards encourage organizational adoption
- **Regulatory Compliance**: Meet GDPR, HIPAA, SOX, and other requirements
- **Customer Assurance**: Demonstrate commitment to data protection
- **Risk Management**: Reduce legal and financial exposure

## Technical Implementation

### Security Configuration

**Core Security Middleware**:

```python
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "*.yourcompany.com"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourcompany.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# RBAC enforcement
def enforce_rbac(required_roles: list):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            token = kwargs.get('token')
            user_roles = extract_roles_from_token(token)
            if not any(role in user_roles for role in required_roles):
                raise HTTPException(403, "Insufficient permissions")
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### Security Architecture

```mermaid
graph TB
    A[Internet] --> B[WAF/Firewall]
    B --> C[Load Balancer + SSL]
    C --> D[API Gateway]
    
    D --> E[Authentication Service]
    D --> F[RAG Backend]
    
    E --> G[User Database]
    F --> H[Document Store]
    F --> I[Vector Database]
    
    J[Security Monitoring] --> D
    J --> F
    J --> E
    
    K[Audit Logs] --> F
    K --> E
    
    L[Secrets Management] --> F
    L --> E
```

## Network Security

### HTTPS and TLS Configuration

```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name your-rag-system.com;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/certs/your-cert.crt;
    ssl_certificate_key /etc/ssl/private/your-key.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    location / {
        proxy_pass http://rag-backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Network Isolation

```yaml
# docker-compose.security.yml
version: '3.8'
networks:
  frontend:
    driver: bridge
    internal: false
  backend:
    driver: bridge
    internal: true
  database:
    driver: bridge
    internal: true

services:
  nginx:
    networks:
      - frontend
      - backend
    
  rag-backend:
    networks:
      - backend
      - database
    
  postgres:
    networks:
      - database
    
  ollama:
    networks:
      - backend
```

## Authentication and Authorization

### JWT Security Implementation

```python
# src/security/auth.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer

class SecurityManager:
    """Comprehensive security management system."""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.security = HTTPBearer()
    
    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        """Create JWT access token with security claims."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=1)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": self._generate_jti(),  # Unique token ID
            "iss": "rag-system",
            "aud": "rag-users"
        })
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> dict:
        """Verify and decode JWT token with security validation."""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                audience="rag-users",
                issuer="rag-system"
            )
            
            # Check token blacklist
            if self._is_token_blacklisted(payload.get("jti")):
                raise HTTPException(401, "Token has been revoked")
            
            return payload
            
        except JWTError:
            raise HTTPException(401, "Invalid token")
    
    def hash_password(self, password: str) -> str:
        """Hash password with secure algorithm."""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
```

### Multi-Factor Authentication

```python
# src/security/mfa.py
import pyotp
import qrcode
from io import BytesIO
import base64

class MFAManager:
    """Multi-Factor Authentication management."""
    
    def generate_secret(self, user_email: str) -> str:
        """Generate TOTP secret for user."""
        secret = pyotp.random_base32()
        
        # Store secret securely (encrypted)
        self._store_user_secret(user_email, secret)
        
        return secret
    
    def generate_qr_code(self, user_email: str, secret: str) -> str:
        """Generate QR code for TOTP setup."""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name="RAG System"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    def verify_totp(self, user_email: str, token: str) -> bool:
        """Verify TOTP token."""
        secret = self._get_user_secret(user_email)
        if not secret:
            return False
        
        totp = pyotp.TOTP(secret)
        
        # Allow for clock skew (±30 seconds)
        return totp.verify(token, valid_window=1)
```

## Secrets Management

### Secure Configuration

```python
# src/security/secrets.py
from cryptography.fernet import Fernet
import os
import base64
from typing import Optional

class SecretsManager:
    """Secure secrets management with encryption."""
    
    def __init__(self):
        self.encryption_key = self._get_or_create_key()
        self.cipher_suite = Fernet(self.encryption_key)
    
    def encrypt_secret(self, value: str) -> str:
        """Encrypt a secret value."""
        encrypted_bytes = self.cipher_suite.encrypt(value.encode())
        return base64.b64encode(encrypted_bytes).decode()
    
    def decrypt_secret(self, encrypted_value: str) -> str:
        """Decrypt a secret value."""
        encrypted_bytes = base64.b64decode(encrypted_value.encode())
        decrypted_bytes = self.cipher_suite.decrypt(encrypted_bytes)
        return decrypted_bytes.decode()
    
    def get_secret(self, key: str) -> Optional[str]:
        """Get secret from environment or secure store."""
        # Try environment variable first
        env_value = os.getenv(key)
        if env_value:
            return env_value
        
        # Try encrypted secret store
        encrypted_value = self._get_from_secure_store(key)
        if encrypted_value:
            return self.decrypt_secret(encrypted_value)
        
        return None
    
    def _get_or_create_key(self) -> bytes:
        """Get encryption key from secure location."""
        key_file = "/etc/rag-system/encryption.key"
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # Restrict permissions
            return key
```

### Environment Configuration

```bash
# .env.example
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/ragdb

# Security
JWT_SECRET=your-super-secret-jwt-key-here
ENCRYPTION_KEY=your-encryption-key-here

# LLM Configuration
OLLAMA_ENDPOINT=http://localhost:11434
DEFAULT_MODEL=mistral:7b

# Monitoring
ENABLE_METRICS=true
LOG_LEVEL=INFO

# External Services (if any)
SMTP_SERVER=smtp.yourcompany.com
SMTP_USERNAME=notifications@yourcompany.com
SMTP_PASSWORD=your-smtp-password
```

## Audit Logging and Monitoring

### Comprehensive Audit System

```python
# src/security/audit.py
import json
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional

class AuditEventType(Enum):
    """Types of audit events."""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    DOCUMENT_ACCESS = "document_access"
    QUERY_EXECUTED = "query_executed"
    ADMIN_ACTION = "admin_action"
    SECURITY_VIOLATION = "security_violation"
    DATA_EXPORT = "data_export"

class AuditLogger:
    """Centralized audit logging system."""
    
    def __init__(self):
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        
        # Configure audit log handler
        handler = logging.FileHandler("/var/log/rag-system/audit.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log security audit event."""
        
        audit_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type.value,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "details": details
        }
        
        self.logger.info(json.dumps(audit_record))
        
        # Also store in database for queries
        self._store_audit_record(audit_record)
    
    def log_document_access(
        self,
        user_id: str,
        document_id: str,
        action: str,
        ip_address: str
    ):
        """Log document access events."""
        self.log_event(
            AuditEventType.DOCUMENT_ACCESS,
            user_id,
            {
                "document_id": document_id,
                "action": action,
                "success": True
            },
            ip_address
        )
    
    def log_security_violation(
        self,
        user_id: str,
        violation_type: str,
        details: Dict[str, Any],
        ip_address: str
    ):
        """Log security violations."""
        self.log_event(
            AuditEventType.SECURITY_VIOLATION,
            user_id,
            {
                "violation_type": violation_type,
                "severity": "high",
                **details
            },
            ip_address
        )
```

### Real-time Security Monitoring

```python
# src/security/monitoring.py
from collections import defaultdict, deque
from datetime import datetime, timedelta
import asyncio

class SecurityMonitor:
    """Real-time security monitoring and alerting."""
    
    def __init__(self):
        self.failed_logins = defaultdict(deque)
        self.suspicious_queries = deque(maxlen=1000)
        self.rate_limits = defaultdict(deque)
        
    def track_failed_login(self, ip_address: str, user_id: str):
        """Track failed login attempts."""
        now = datetime.utcnow()
        self.failed_logins[ip_address].append(now)
        
        # Keep only last hour of attempts
        cutoff = now - timedelta(hours=1)
        while (self.failed_logins[ip_address] and 
               self.failed_logins[ip_address][0] < cutoff):
            self.failed_logins[ip_address].popleft()
        
        # Alert if too many failures
        if len(self.failed_logins[ip_address]) > 5:
            self._alert_brute_force_attempt(ip_address, user_id)
    
    def check_suspicious_query(self, query: str, user_id: str) -> bool:
        """Check for suspicious query patterns."""
        suspicious_patterns = [
            "DROP TABLE",
            "DELETE FROM",
            "INSERT INTO",
            "UPDATE SET",
            "EXEC ",
            "xp_cmdshell",
            "--",
            "/*",
            "UNION SELECT"
        ]
        
        query_upper = query.upper()
        for pattern in suspicious_patterns:
            if pattern in query_upper:
                self._alert_suspicious_query(query, user_id, pattern)
                return True
        
        return False
    
    def _alert_brute_force_attempt(self, ip_address: str, user_id: str):
        """Alert on brute force attempts."""
        alert_data = {
            "type": "brute_force",
            "ip_address": ip_address,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "severity": "high"
        }
        
        # Send to monitoring system
        asyncio.create_task(self._send_security_alert(alert_data))
```

## Data Privacy and Protection

### Data Encryption

```python
# src/security/encryption.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import base64

class DataEncryption:
    """Data encryption for sensitive information."""
    
    def __init__(self, password: str):
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.cipher_suite = Fernet(key)
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        encrypted_data = self.cipher_suite.encrypt(data.encode())
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        encrypted_bytes = base64.b64decode(encrypted_data.encode())
        decrypted_data = self.cipher_suite.decrypt(encrypted_bytes)
        return decrypted_data.decode()

class PIIDetector:
    """Detect and protect personally identifiable information."""
    
    def __init__(self):
        self.patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'phone': r'\b\d{3}-\d{3}-\d{4}\b',
            'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
        }
    
    def detect_pii(self, text: str) -> Dict[str, List[str]]:
        """Detect PII in text."""
        import re
        
        detected = {}
        for pii_type, pattern in self.patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                detected[pii_type] = matches
        
        return detected
    
    def mask_pii(self, text: str) -> str:
        """Mask PII in text for logging."""
        import re
        
        masked_text = text
        for pii_type, pattern in self.patterns.items():
            masked_text = re.sub(pattern, f"[{pii_type.upper()}_MASKED]", masked_text)
        
        return masked_text
```

### Data Retention and Deletion

```python
# src/security/retention.py
from datetime import datetime, timedelta
import asyncio

class DataRetentionManager:
    """Manage data retention and deletion policies."""
    
    def __init__(self):
        self.retention_policies = {
            'audit_logs': timedelta(days=2555),  # 7 years
            'user_sessions': timedelta(days=30),
            'query_history': timedelta(days=365),
            'document_metadata': timedelta(days=2555),
            'system_logs': timedelta(days=90)
        }
    
    async def cleanup_expired_data(self):
        """Clean up data based on retention policies."""
        for data_type, retention_period in self.retention_policies.items():
            cutoff_date = datetime.utcnow() - retention_period
            
            if data_type == 'audit_logs':
                await self._cleanup_audit_logs(cutoff_date)
            elif data_type == 'user_sessions':
                await self._cleanup_user_sessions(cutoff_date)
            elif data_type == 'query_history':
                await self._cleanup_query_history(cutoff_date)
    
    async def delete_user_data(self, user_id: str):
        """Delete all data for a specific user (GDPR compliance)."""
        
        # Delete user profile
        await self._delete_user_profile(user_id)
        
        # Anonymize audit logs
        await self._anonymize_user_audit_logs(user_id)
        
        # Delete query history
        await self._delete_user_query_history(user_id)
        
        # Delete user sessions
        await self._delete_user_sessions(user_id)
```

## Implementation Tasks

### Task 6.1: Network Security
- HTTPS/TLS configuration
- Network isolation setup
- Firewall rules and rate limiting
- VPN integration (if required)

### Task 6.2: Authentication Security
- JWT implementation with security features
- Multi-factor authentication setup
- Password policy enforcement
- Session management

### Task 6.3: Authorization Framework
- RBAC enforcement at all levels
- API endpoint protection
- Resource-level permissions
- Privilege escalation prevention

### Task 6.4: Monitoring and Auditing
- Comprehensive audit logging
- Real-time security monitoring
- Intrusion detection system
- Compliance reporting

## Success Criteria

### Security Requirements
- [ ] All communications encrypted (HTTPS/TLS)
- [ ] Authentication system prevents unauthorized access
- [ ] RBAC properly enforces permissions at all levels
- [ ] All security events logged and monitored
- [ ] Vulnerability scans show no critical issues

### Privacy Requirements
- [ ] PII detection and protection implemented
- [ ] Data retention policies enforced
- [ ] User data deletion capability (GDPR compliance)
- [ ] Audit trail for all data access

### Compliance Requirements
- [ ] Security controls documented
- [ ] Audit logs meet compliance standards
- [ ] Data encryption at rest and in transit
- [ ] Access controls regularly reviewed

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Data Breach** | Critical | Multi-layer security, encryption, monitoring |
| **Unauthorized Access** | High | Strong authentication, RBAC, MFA |
| **Insider Threats** | High | Audit logging, privilege restrictions, monitoring |
| **Compliance Violations** | High | Regular audits, automated compliance checks |

## Timeline & Priority

**Timeline**: 2-3 weeks | **Priority**: High | **Dependencies**: Goals 1, 5

### Week 1: Foundation Security
- HTTPS/TLS setup
- Basic authentication
- Network isolation

### Week 2: Advanced Security
- RBAC implementation
- Audit logging system
- Security monitoring

### Week 3: Compliance & Testing
- Privacy controls
- Security testing
- Compliance validation

## Next Steps

Upon completion of Goal 6:
1. Security penetration testing
2. Compliance audit preparation
3. Security documentation finalization

## Related Documentation

- [Goal 1: Technical Foundation](goal-1.md)
- [Goal 2: Interactive Q&A Interface](goal-2.md)
- [Goal 5: Deployment & Infrastructure](goal-5.md) 