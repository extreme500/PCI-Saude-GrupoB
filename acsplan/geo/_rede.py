"""
Transporte HTTP para os servicos externos de geo.

Por que isto existe
-------------------
Os servidores publicos do OSRM apresentam uma cadeia de certificados
INCOMPLETA: falta um intermediario, e o que sobra inclui uma assinatura
cruzada vencida. O Windows (Schannel) e o curl resolvem isso sozinhos,
porque buscam o intermediario que falta pelo campo AIA do certificado. O
OpenSSL, que e o que o Python usa, nao faz essa busca: ele valida a cadeia
como foi apresentada, encontra o certificado vencido e recusa.

O sintoma, visto de dentro do projeto, era enganoso: `--distancias osrm`
simplesmente "nao respondia" e caia para haversine, e ficou registrado por
um tempo como se o servico estivesse inacessivel desta maquina. Nao estava.

A saida adotada aqui NAO e desligar a verificacao, que seria trocar um
problema de configuracao por um buraco de seguranca. E tentar primeiro o
caminho normal (urllib) e, se o OpenSSL recusar a cadeia, repetir pelo
curl, que valida pelo armazem do sistema e consegue completar a cadeia.
Quem verifica continua sendo uma autoridade certificadora; muda so quem
monta o caminho ate ela.

Se nenhum dos dois funcionar, a funcao devolve None e quem chama decide o
que fazer: a matriz cai para haversine, o mapa desenha linhas retas.
"""

from __future__ import annotations

import json
import shutil
import ssl
import subprocess
import urllib.error
import urllib.request

AGENTE = "acsplan/1.0 (projeto academico, UFRGS)"


def _por_urllib(url: str, timeout: int) -> tuple[dict | None, str]:
    try:
        requisicao = urllib.request.Request(url, headers={"User-Agent": AGENTE})
        with urllib.request.urlopen(requisicao, timeout=timeout) as resposta:
            return json.loads(resposta.read().decode("utf-8")), ""
    except urllib.error.URLError as erro:
        motivo = erro.reason
        if isinstance(motivo, ssl.SSLError):
            return None, "cadeia-tls"
        return None, f"rede: {motivo}"
    except (TimeoutError, OSError, ValueError) as erro:
        return None, f"{type(erro).__name__}: {erro}"


def _por_curl(url: str, timeout: int) -> tuple[dict | None, str]:
    executavel = shutil.which("curl")
    if not executavel:
        return None, "curl indisponivel"
    try:
        processo = subprocess.run(
            [executavel, "-sS", "--fail", "--max-time", str(timeout),
             "-A", AGENTE, url],
            capture_output=True, timeout=timeout + 10)
    except (subprocess.SubprocessError, OSError) as erro:
        return None, f"curl: {type(erro).__name__}"
    if processo.returncode != 0:
        return None, f"curl saiu com {processo.returncode}"
    try:
        return json.loads(processo.stdout.decode("utf-8")), ""
    except ValueError:
        return None, "curl devolveu algo que nao e JSON"


def obter_json(url: str, *, timeout: int = 25,
               silencioso: bool = True) -> dict | None:
    """GET de JSON, com o curl como segunda tentativa. None se nao der."""
    corpo, motivo = _por_urllib(url, timeout)
    if corpo is not None:
        return corpo

    if motivo != "cadeia-tls":
        if not silencioso:
            print(f"  [aviso] servico externo indisponivel ({motivo}).")
        return None

    corpo, motivo_curl = _por_curl(url, timeout)
    if corpo is not None:
        return corpo
    if not silencioso:
        print("  [aviso] o OpenSSL recusou a cadeia de certificados do servidor "
              f"e o curl tambem nao resolveu ({motivo_curl}).")
    return None
