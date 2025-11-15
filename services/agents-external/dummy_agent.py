"""Stub para agentes externos.
Implementar cada integración con su propio cliente y pruebas de contrato.
"""


def run(prompt: str) -> dict:
    return {"model": "dummy", "response": f"echo: {prompt}"}


if __name__ == "__main__":
    print(run("hola"))
