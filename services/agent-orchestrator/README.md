# Agente orquestador

Se encarga de recibir peticiones del backend y decidir:
- Si consulta contexto en RAG.
- Si delega en un agente/modelo externo especializado.
- Si ejecuta herramientas via MCP.
- Como ensamblar y devolver la respuesta final.

Ideas:
- Mantener memoria conversacional con storage externo.
- Politicas de enrutado configurables.
- Observabilidad con spans por decision tomada.
