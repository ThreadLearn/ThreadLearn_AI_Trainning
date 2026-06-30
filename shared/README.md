# Shared Modules

Cross-team module dependencies between AI1 and AI2.

## AI1 → AI2 Dependencies

| Module | Location | Used by |
|--------|----------|---------|
| `ast_preprocessor.py` | `training/modules/` | AI2-03 race_detector, AI2-06 rag_pipeline |
| `output_parser.py` | `training/modules/` | AI2-08 llm_client (Ollama swap) |

## Import Pattern (from server/server/)

```python
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "training", "modules"))
from ast_preprocessor import parse
```

## Delivery Schedule

| Module | Expected | Blocking |
|--------|----------|---------|
| `ast_preprocessor.py` | End W2 | AI2-03 |
| `output_parser.py` | End W6 | AI2-08 |
