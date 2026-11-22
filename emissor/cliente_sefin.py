"""Cliente HTTP isolado para a produção restrita da SEFIN Nacional.

Nunca contém endpoints de produção. PEMs temporários são removidos após o uso.
"""
from contextlib import contextmanager
import os
from pathlib import Path
import tempfile

import requests
from cryptography.hazmat.primitives.serialization import (
    Encoding, PrivateFormat, NoEncryption, pkcs12,
)

HOST_RESTRITO = "https://sefin.producaorestrita.nfse.gov.br"
BASE_RESTRITA = HOST_RESTRITO + "/SefinNacional"


@contextmanager
def sessao_certificado(p12_path, password):
    key, cert, chain = pkcs12.load_key_and_certificates(
        Path(p12_path).read_bytes(), password.encode("utf-8")
    )
    if key is None or cert is None:
        raise ValueError("PKCS#12 não contém chave privada e certificado")
    with tempfile.TemporaryDirectory(prefix="nfse-mtls-") as folder:
        key_file = Path(folder) / "key.pem"
        cert_file = Path(folder) / "cert.pem"
        content = (
            (key_file, key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())),
            (cert_file, cert.public_bytes(Encoding.PEM) +
             b"".join(c.public_bytes(Encoding.PEM) for c in (chain or []))),
        )
        for path, payload in content:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
        with requests.Session() as session:
            session.cert = (str(cert_file), str(key_file))
            session.verify = True
            session.trust_env = False  # não permite redirecionar para proxies do ambiente
            yield session


def enviar_request(session, method, endpoint, **kwargs):
    if not endpoint.startswith("/") or endpoint.startswith("//"):
        raise ValueError("Endpoint relativo obrigatório")
    return session.request(
        method, BASE_RESTRITA + endpoint,
        timeout=(10, 35), allow_redirects=False,
        headers={"Accept": "application/json", **kwargs.pop("headers", {})},
        **kwargs,
    )
