"""
认证加密服务：提供登录公钥和 RSA-OAEP 解密能力。
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from flask import current_app

from app.common.errors import BusinessError
from app.constants import ErrorCode


@dataclass(frozen=True)
class AuthKeyPair:
    key_id: str
    algorithm: str
    private_key: rsa.RSAPrivateKey
    public_key_pem: str


def _read_text(path_value: str) -> str:
    if not path_value:
        return ""
    path = Path(path_value)
    if not path.exists():
        raise BusinessError(ErrorCode.INTERNAL_ERROR, f"登录密钥文件不存在: {path}")
    return path.read_text(encoding="utf-8").strip()


class AuthCryptoService:
    algorithm = "RSA-OAEP-256"

    def _dev_key_paths(self) -> tuple[Path, Path]:
        runtime_dir = Path(current_app.instance_path) / "auth-keys"
        runtime_dir.mkdir(parents=True, exist_ok=True)
        return (
            runtime_dir / "auth-login-dev-private.pem",
            runtime_dir / "auth-login-dev-public.pem",
        )

    def _load_private_key_pem(self) -> str:
        config = current_app.config
        return (
            (config.get("AUTH_LOGIN_RSA_PRIVATE_KEY") or "").strip()
            or _read_text(config.get("AUTH_LOGIN_RSA_PRIVATE_KEY_PATH") or "")
        )

    def _load_public_key_pem(self) -> str:
        config = current_app.config
        return (
            (config.get("AUTH_LOGIN_RSA_PUBLIC_KEY") or "").strip()
            or _read_text(config.get("AUTH_LOGIN_RSA_PUBLIC_KEY_PATH") or "")
        )

    def _build_dev_key_pair(self, key_id: str) -> AuthKeyPair:
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key_pem = (
            private_key.public_key()
            .public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            .decode("utf-8")
        )
        return AuthKeyPair(
            key_id=key_id,
            algorithm=self.algorithm,
            private_key=private_key,
            public_key_pem=public_key_pem,
        )

    def _load_or_create_dev_key_pair(self, key_id: str) -> AuthKeyPair:
        private_key_path, public_key_path = self._dev_key_paths()
        if private_key_path.exists():
            private_key_pem = private_key_path.read_text(encoding="utf-8").strip()
            public_key_pem = public_key_path.read_text(encoding="utf-8").strip() if public_key_path.exists() else ""
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode("utf-8"),
                password=None,
            )
            if not isinstance(private_key, rsa.RSAPrivateKey):
                raise BusinessError(ErrorCode.INTERNAL_ERROR, "开发环境登录私钥不是 RSA 私钥")
            if not public_key_pem:
                public_key_pem = (
                    private_key.public_key()
                    .public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo,
                    )
                    .decode("utf-8")
                )
                public_key_path.write_text(public_key_pem, encoding="utf-8")
            return AuthKeyPair(
                key_id=key_id,
                algorithm=self.algorithm,
                private_key=private_key,
                public_key_pem=public_key_pem,
            )

        key_pair = self._build_dev_key_pair(key_id)
        private_key_pem = key_pair.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")
        private_key_path.write_text(private_key_pem, encoding="utf-8")
        public_key_path.write_text(key_pair.public_key_pem, encoding="utf-8")
        return key_pair

    @lru_cache(maxsize=1)
    def _load_key_pair(self) -> AuthKeyPair:
        config = current_app.config
        key_id = str(config.get("AUTH_LOGIN_RSA_KEY_ID") or "default").strip() or "default"
        private_key_pem = self._load_private_key_pem()
        public_key_pem = self._load_public_key_pem()

        if not private_key_pem:
            if current_app.debug or current_app.testing:
                return self._load_or_create_dev_key_pair(key_id)
            raise BusinessError(ErrorCode.INTERNAL_ERROR, "未配置登录 RSA 私钥")

        try:
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode("utf-8"),
                password=None,
            )
        except Exception as exc:
            raise BusinessError(ErrorCode.INTERNAL_ERROR, f"加载登录私钥失败: {exc}") from exc

        if not isinstance(private_key, rsa.RSAPrivateKey):
            raise BusinessError(ErrorCode.INTERNAL_ERROR, "登录私钥不是 RSA 私钥")

        if not public_key_pem:
            public_key_pem = (
                private_key.public_key()
                .public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
                .decode("utf-8")
            )

        return AuthKeyPair(
            key_id=key_id,
            algorithm=self.algorithm,
            private_key=private_key,
            public_key_pem=public_key_pem,
        )

    def get_public_key(self) -> dict:
        pair = self._load_key_pair()
        return {
            "key_id": pair.key_id,
            "algorithm": pair.algorithm,
            "public_key_pem": pair.public_key_pem,
        }

    def decrypt_password(self, ciphertext: str, key_id: Optional[str]) -> str:
        pair = self._load_key_pair()
        if not ciphertext:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "缺少加密密码")
        if key_id and str(key_id).strip() and str(key_id).strip() != pair.key_id:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "登录密钥版本不匹配，请刷新页面重试")

        try:
            decoded = base64.b64decode(ciphertext)
        except Exception as exc:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "登录密文格式无效") from exc

        try:
            plain = pair.private_key.decrypt(
                decoded,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
        except Exception as exc:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "登录密文解密失败") from exc

        password = plain.decode("utf-8").strip()
        if not password:
            raise BusinessError(ErrorCode.VALIDATION_ERROR, "密码不能为空")
        return password


auth_crypto_service = AuthCryptoService()
