import json
from pathlib import Path
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# HTTPBearer scheme tells Swagger UI we just want a simple Bearer Token
security_scheme = HTTPBearer()

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

from fastapi import Query, Request
def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
    token_query: str | None = Query(None, alias="token")
):
    """FastAPI dependency to validate requests against the static token."""
    token = ""
    if credentials:
        token = credentials.credentials
    elif token_query:
        token = token_query

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
