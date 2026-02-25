import json
from pathlib import Path
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

# OAuth2 scheme for extracting the token from the request
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")

class Token(BaseModel):
    access_token: str
    token_type: str

def _load_static_token() -> str:
    """Loads the hardcoded access token from token.json."""
    token_file = Path(__file__).parent.parent / "token.json"
    if not token_file.exists():
        # Fallback if file doesn't exist, though it should
        return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc3MjQ1ODMxMX0.4R6BiFuxZvDbzZNEwr55C6FZ04pwIF920XvYkLCN3Qo"
    
    try:
        data = json.loads(token_file.read_text())
        return data.get("access_token", "")
    except Exception:
        return ""

def get_current_user(token: str = Depends(oauth2_scheme)):
    """FastAPI dependency to validate requests against the static token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    expected_token = _load_static_token()
    
    # Exact match required
    if not expected_token or token != expected_token:
        raise credentials_exception

    return "authorized_user"
