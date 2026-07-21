from __future__ import annotations

import hmac
import secrets
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import HTTPException, Request, status

from ktoolbox.configuration import WebUIConfiguration
from ktoolbox.webui.database import WebUIDatabase, WebUISession

SESSION_COOKIE = "ktoolbox_session"
CSRF_HEADER = "X-CSRF-Token"


@dataclass(frozen=True, slots=True)
class LoginResult:
    token: str
    session: WebUISession


class LoginRateLimiter:
    def __init__(self, *, maximum: int = 5, window_seconds: float = 300) -> None:
        self.maximum = maximum
        self.window_seconds = window_seconds
        self._attempts: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        attempts = self._active_attempts(key)
        if len(attempts) >= self.maximum:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Try again later.",
            )

    def failure(self, key: str) -> None:
        self._active_attempts(key).append(time.monotonic())

    def success(self, key: str) -> None:
        self._attempts.pop(key, None)

    def _active_attempts(self, key: str) -> deque[float]:
        attempts = self._attempts[key]
        threshold = time.monotonic() - self.window_seconds
        while attempts and attempts[0] < threshold:
            attempts.popleft()
        return attempts


class AuthService:
    def __init__(
        self,
        configuration: WebUIConfiguration,
        database: WebUIDatabase,
        *,
        password_hasher: PasswordHasher | None = None,
        rate_limiter: LoginRateLimiter | None = None,
    ) -> None:
        self.configuration = configuration
        self.database = database
        self.password_hasher = password_hasher or PasswordHasher()
        self.rate_limiter = rate_limiter or LoginRateLimiter()

    def validate_configuration(self) -> None:
        if not self.configuration.username.strip():
            raise ValueError("KTOOLBOX_WEBUI__USERNAME must be configured")
        if not self._password_hash and not self._plaintext_password:
            raise ValueError("KTOOLBOX_WEBUI__PASSWORD_HASH or KTOOLBOX_WEBUI__PASSWORD must be configured")
        if self._password_hash:
            try:
                self.password_hasher.check_needs_rehash(self._password_hash)
            except InvalidHashError as error:
                raise ValueError("KTOOLBOX_WEBUI__PASSWORD_HASH is not a valid Argon2 hash") from error

    async def login(self, username: str, password: str, client_key: str) -> LoginResult:
        key = f"{client_key}:{username.casefold()}"
        self.rate_limiter.check(key)
        if not self._credentials_match(username, password):
            self.rate_limiter.failure(key)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
        self.rate_limiter.success(key)
        token = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(24)
        session = await self.database.create_session(token, self.configuration.username, csrf_token)
        return LoginResult(token, session)

    async def session(self, token: str | None) -> WebUISession:
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
        session = await self.database.get_session(
            token,
            idle_lifetime=timedelta(hours=self.configuration.session_idle_hours),
            absolute_lifetime=timedelta(hours=self.configuration.session_absolute_hours),
        )
        if session is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
        return session

    async def logout(self, token: str | None) -> None:
        if token:
            await self.database.delete_session(token)

    def verify_csrf(self, request: Request, session: WebUISession) -> None:
        supplied = request.headers.get(CSRF_HEADER, "")
        if not supplied or not hmac.compare_digest(supplied, session.csrf_token):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")
        origin = request.headers.get("origin")
        if origin and origin.rstrip("/") != str(request.base_url).rstrip("/"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-origin request rejected")

    @property
    def _password_hash(self) -> str:
        return self.configuration.password_hash.get_secret_value()

    @property
    def _plaintext_password(self) -> str:
        return self.configuration.password.get_secret_value()

    def _credentials_match(self, username: str, password: str) -> bool:
        username_matches = hmac.compare_digest(username, self.configuration.username)
        password_matches = False
        if self._password_hash:
            try:
                password_matches = self.password_hasher.verify(self._password_hash, password)
            except (VerificationError, InvalidHashError):
                password_matches = False
        elif self._plaintext_password:
            password_matches = hmac.compare_digest(password, self._plaintext_password)
        return username_matches and password_matches


def client_identifier(request: Request) -> str:
    return request.client.host if request.client else "unknown"
