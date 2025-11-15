"""Stub para agentes externos.
Implementar cada integracion con su propio cliente y pruebas de contrato.
"""


def run(prompt: str) -> dict:
    return {"model": "dummy", "response": "echo: " + prompt}


if __name__ == "__main__":
    print(run("hola"))
