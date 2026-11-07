"""IDs opacos na URL (``/rsc/MMhbs5`` em vez de ``/rsc/1``).

Algoritmo Hashids, compatível com a biblioteca PHP do sistema original (mesmo salt → mesmos
códigos). Cada entidade codifica ``[id, a, b]`` com um sufixo próprio, conferido ao decodificar:
o código de uma atividade não vale como código de requerimento.
Hashid NÃO é controle de acesso; a checagem de dono continua obrigatória.
"""

from functools import lru_cache

from django.conf import settings
from hashids import Hashids

SUFIXOS: dict[str, tuple[int, int]] = {
    "usuario": (1, 2),
    "rsc": (3, 7),
    "atividade": (4, 8),
}


@lru_cache(maxsize=4)
def _hashids(salt: str) -> Hashids:
    return Hashids(salt=salt)


def _codec() -> Hashids:
    return _hashids(settings.HASHIDS_SALT)


def codificar(entidade: str, id_: int) -> str:
    return _codec().encode(id_, *SUFIXOS[entidade])


def decodificar(entidade: str, hashid: str) -> int | None:
    valores = _codec().decode(hashid or "")
    if len(valores) == 3 and tuple(valores[1:]) == SUFIXOS[entidade]:
        return valores[0]
    return None
