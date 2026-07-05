# MathModel Studio V3 Frontend

This is the new product shell for MathModel Studio V3. The legacy Vue Control Center is frozen under `app/frontend`.

## Local Run

```powershell
cd app/frontend-studio
npm install
$env:NEXT_PUBLIC_MATHMODEL_API_BASE="http://127.0.0.1:8000"
npm run dev
```

The first screen is the working Studio surface: project creation, file upload, runtime selection, stage timeline, Human Gate, model configuration, built-in template import, template library, artifact preview, and quality checks.
