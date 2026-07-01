# zhanwen/MathModel Local Import

Generated at: `2026-07-01T15:38:50+00:00`
Source: `C:\Users\zklzk\Downloads\Compressed\MathModel-master\MathModel-master`
Destination: `D:\WorkSpace_MathModel\knowledge\raw\zhanwen_mathmodel`
Mode: `copied`

## Why Raw Files Are Local Only

The downloaded repository does not include an explicit LICENSE/COPYING file in the inspected local copy. Raw PDFs, papers, templates, and attachments are therefore kept under `knowledge/raw/`, which is ignored by Git. Commit this note, the import script, and local RAG configuration; do not commit the copied third-party raw files unless licensing is later confirmed.

## Imported Counts

| Library | Files | MB |
| --- | ---: | ---: |
| `code_templates` | 18 | 12.37 |
| `cumcm_problems` | 143 | 216.42 |
| `excellent_papers` | 120 | 578.99 |
| `mcm_icm_problems` | 27 | 25.96 |
| `model_methods` | 61 | 38.76 |
| `paper_expression` | 27 | 19.34 |
| `review_rubrics` | 26 | 4.81 |

## Local Manifest

- Manifest: `D:\WorkSpace_MathModel\knowledge\raw\zhanwen_mathmodel\zhanwen_mathmodel_manifest.jsonl`

## Next Commands

```powershell
python scripts\rag_ingest.py --source knowledge\raw\zhanwen_mathmodel --vector-store none
python scripts\rag_query.py "综合评价 TOPSIS 权重 稳定性" --library model_methods
python scripts\rag_query.py "评委 快审 摘要 关键图 结论" --library review_rubrics
```

For full excellent-paper import, rerun:

```powershell
python scripts\import_zhanwen_mathmodel.py --source "C:\Users\zklzk\Downloads\Compressed\MathModel-master\MathModel-master" --full-papers
```
