from dummy_agent import run


def test_run_echoes_prompt():
    result = run("hola")
    assert result["model"] == "dummy"
    assert result["response"] == "echo: hola"
