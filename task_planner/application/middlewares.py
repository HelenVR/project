from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import status

security = HTTPBasic()


def basic_auth(login: str, password: str):
    if not (login and password):
        raise Exception(f"Login and/or password must be supplied with login/password in 'api' section in config")

    def credential_checker(credentials: HTTPBasicCredentials = Depends(security)):
        if not (credentials.username == login and credentials.password == password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect login or password",
                headers={"WWW-Authenticate": "Basic"},
            )
        return credentials.username
    return credential_checker
