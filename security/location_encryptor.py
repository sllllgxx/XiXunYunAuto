# 这个模块集中维护签到经纬度所需的 RSA 加密逻辑。
# 加密流程固定为载入 PEM 公钥、执行 RSA PKCS#1 v1.5 加密，再输出 Base64 字符串。
from __future__ import annotations

import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding


PUBLIC_KEY_PEM = b"""-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDlYsiV3DsG+t8OFMLyhdmG2P2J
4GJwmwb1rKKcDZmTxEphPiYTeFIg4IFEiqDCATAPHs8UHypphZTK6LlzANyTzl9L
jQS6BYVQk81LhQ29dxyrXgwkRw9RdWaMPtcXRD4h6ovx6FQjwQlBM5vaHaJOHhEo
rHOSyd/deTvcS+hRSQIDAQAB
-----END PUBLIC KEY-----"""


# 公钥对象在模块加载时完成解析，后续每次加密都会直接复用这一个对象。
_PUBLIC_KEY = serialization.load_pem_public_key(PUBLIC_KEY_PEM)


def encrypt_coordinate(coordinate: str) -> str:
    # 每次发起签到前都会对单个坐标值重新加密，并返回接口要求的 Base64 文本。
    encrypted_bytes = _PUBLIC_KEY.encrypt(
        coordinate.encode("utf-8"), padding.PKCS1v15()
    )
    return base64.b64encode(encrypted_bytes).decode("ascii")
