# RAG Validation Guide

## Quick Start

### 1. Generar PDFs Sintéticos

```bash
cd services/rag/server
python generate_test_pdfs.py
```

Esto creará 5 PDFs de prueba en `./test_pdfs/`:
- `technical_architecture.pdf` - Arquitectura del sistema
- `product_features.pdf` - Características del producto  
- `user_guide.pdf` - Guía de usuario
- `faq_document.pdf` - Preguntas frecuentes
- `research_paper.pdf` - Paper de investigación (multi-página)

### 2. Levantar el Sistema

```bash
cd ../../..  # Volver a raíz del proyecto
./scripts/start.ps1  # Windows
# o
./scripts/start.sh   # Linux/Mac
```

Asegúrate de configurar las variables de entorno en `.env`:
```env
# Embeddings (OpenAI o local)
EMBEDDING_PROVIDER=openai  # o "local"
OPENAI_API_KEY=tu-api-key  # si usas OpenAI
# LOCAL_EMBEDDING_MODEL=BAAI/bge-m3  # si usas local

# Habilitar contenido y reranking
ENABLE_CONTENT_EMBED=1
ENABLE_RERANKING=1

# Chunking ilimitado
MAX_CHUNKS=None
CHUNK_SIZE_CHARS=600
```

### 3. Ejecutar Validación

```bash
cd services/rag/server
python validate_rag.py
```

El script automáticamente:
1. ✅ Sube los 5 PDFs al servidor RAG
2. ✅ Espera a que se complete la indexación
3. ✅ Ejecuta 15 consultas de prueba SIN reranking
4. ✅ Ejecuta las mismas 15 consultas CON reranking
5. ✅ Compara los resultados y genera un reporte

### 4. Revisar Resultados

El script genera:
- **Salida en consola**: Resumen con estadísticas clave
- **Archivo JSON**: `rag_test_results_YYYYMMDD_HHMMSS.json` con resultados detallados

## Ejemplo de Salida

```
📊 RAG VALIDATION REPORT
================================================

Total Queries: 15
Results Reordered by Reranking: 8 (53.3%)

Average Latency:
  Without Reranking: 245.3ms
  With Reranking:    487.6ms
  Reranking Overhead: 242.3ms

Results by Category:
  factual_retrieval: 2/3 reordered (67%)
  technical_detail: 1/2 reordered (50%)
  research_finding: 2/2 reordered (100%)
  ...

Top 5 Reranking Impacts:
  1. What is reranking and why is it useful?
     Score change: 0.721 → 0.912 (Δ+0.191)
  ...
```

## Métricas Clave a Observar

### ✅ Indicadores de Éxito

1. **Reordenamiento**: 40-60% de queries deberían mostrar reordenamiento
   - Indica que el reranking está mejorando la relevancia

2. **Latencia Aceptable**: 
   - Sin reranking: < 500ms
   - Con reranking: < 1000ms (overhead ~200-500ms)

3. **Modo de Búsqueda**: 
   - Debe mostrar `"vector"` o `"vector+rerank"`
   - Si muestra `"like"` = problema con embeddings/Qdrant

4. **Chunks Generados**:
   - Revisar logs del servidor durante upload
   - Deberías ver "Indexed N content chunks" con N >> 4

### ⚠️ Problemas Comunes

**Problema**: `"mode": "like"` en vez de `"vector"`
- **Causa**: Embeddings no configurados o Qdrant no disponible
- **Solución**: Verificar `ENABLE_CONTENT_EMBED=1` y `EMBEDDING_PROVIDER`

**Problema**: Latencia muy alta (> 2 segundos)
- **Causa**: Modelo de reranking muy grande o CPU lento
- **Solución**: Usar modelo más ligero o ajustar `RERANK_TOP_K`

**Problema**: Todos los scores muy bajos (< 0.5)
- **Causa**: Embeddings no coinciden con el contenido
- **Solución**: Reindexar documentos con la configuración correcta

## Validación Manual

### Consultas de Prueba Recomendadas

```python
# Factual simple
"What port does the Gateway run on?"
# Esperado: "8088" de technical_architecture.pdf

# Explicación conceptual  
"What is reranking and why is it useful?"
# Esperado: Explicación detallada de FAQ

# Dato cuantitativo
"What was the accuracy improvement from reranking?"
# Esperado: "15-20%" de research_paper.pdf

# Multi-documento
"What file formats are supported?"
# Esperado: Puede venir de FAQ o product_features
```

### Probar Reranking Manualmente

```bash
# Sin reranking
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"text": "What is reranking?", "limit": 5, "rerank": false}'

# Con reranking
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"text": "What is reranking?", "limit": 5, "rerank": true}'
```

Compara:
- El orden de los resultados
- Los campos `rerank_score` vs `original_score`
- La relevancia del primer resultado

## Validación de Chunking Ilimitado

### Ver Chunks en Qdrant

```bash
# Listar colecciones
curl http://localhost:6333/collections

# Ver puntos en la colección de contenido
curl http://localhost:6333/collections/uploads-content/points/scroll?limit=100
```

Deberías ver:
- Muchos más puntos que antes (100-200 por documento vs 4)
- Payload con `chunk_index`, `total_chunks`, `chunk_type`

### Comparación Antes/Después

**Antes (MAX_CHUNKS=4)**:
- PDF 50 páginas → 4 chunks
- Mucho contenido perdido
- Búsquedas fallan en contenido intermedio

**Después (MAX_CHUNKS=None)**:
- PDF 50 páginas → ~100-150 chunks
- Todo el contenido indexado
- Búsquedas encuentran cualquier sección

## Tips de Optimización

### Si usas OpenAI API
```env
# Reducir costos manteniendo calidad
CHUNK_SIZE_CHARS=600  # Chunks más pequeños = menos tokens
MAX_CHUNKS=100        # Límite razonable en vez de None
```

### Si usas modelos locales
```env
# Máxima calidad sin coste
EMBEDDING_PROVIDER=local
LOCAL_EMBEDDING_MODEL=BAAI/bge-m3  # Mejor calidad multilingüe
MAX_CHUNKS=None                     # Sin límites
ENABLE_RERANKING=1                  # Reranking siempre
```

### Ajuste fino de reranking
```env
# Para latencia sensible
RERANK_TOP_K=20   # Menos resultados a rerank
RERANK_FINAL_K=5  # Menos resultados finales

# Para máxima calidad
RERANK_TOP_K=100  # Más resultados a rerank
RERANK_FINAL_K=10 # Más resultados finales
```

## Siguientes Pasos

Después de validar con PDFs sintéticos:

1. **Probar con documentos reales** de tu dominio
2. **Ajustar parámetros** según los resultados
3. **Crear tu propio test_queries.json** con preguntas de tu caso de uso
4. **Monitorear métricas** en producción con Prometheus

---

## Estructura de Archivos de Validación

```
services/rag/server/
├── generate_test_pdfs.py      # Generador de PDFs
├── test_queries.json           # Consultas de prueba
├── validate_rag.py             # Script de validación
├── test_pdfs/                  # PDFs generados
│   ├── technical_architecture.pdf
│   ├── product_features.pdf
│   ├── user_guide.pdf
│   ├── faq_document.pdf
│   └── research_paper.pdf
└── rag_test_results_*.json    # Resultados generados
```
