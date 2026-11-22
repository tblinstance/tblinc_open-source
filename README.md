# tblinc

**High-level Python AI & Standalone MTV/MVC Web Framework** — pure Python stdlib core (no Django, no Flask, no FastAPI) featuring **25 modular AI model folders**, a **12-module MTV/MVC web framework**, **Personal & Admin AI API Keys, Per-Model Token Quotas, Wallet Billing & Transactions**, **CUDA / Intel XPU / OpenVINO / CPU hardware detection**, **SQLite ORM**, **Custom Template Engine**, **Validated Forms & ModelForms**, **PBKDF2 Auth & CSRF Protection**, and an **Auto-Generated Admin Panel + tblinc AI + Model Trainer** styled via CDN with **Tailwind CSS**, **Lucide Icons**, **Google Fonts (Inter + JetBrains Mono)**, and **Motion**.

## Quick Install

```bash
pip install -e .
```

Optional AI/ML & GPU hardware stacks:

```bash
tblinc install
tblinc install tensorflow cuda
tblinc install torch llm vision
tblinc install all
```

## Create, Verify & Serve

```bash
tblinc verify
tblinc devices
tblinc create ai my_ai_app
cd my_ai_app
tblinc createsuperuser
tblinc serve
```

Additional CLI commands:

```bash
tblinc serve --host 0.0.0.0 --port 8080
tblinc migrate
tblinc createsuperuser --username root --password strongpass
tblinc models list
tblinc models demo multimodal
```

- **App & Live tblinc AI**: `http://127.0.0.1:8000/`
- **User Profile & Personal AI Keys**: `http://127.0.0.1:8000/profile/`
- **Billing, Balance & Transactions**: `http://127.0.0.1:8000/billing/`
- **Workspace Settings**: `http://127.0.0.1:8000/settings/`
- **Auto-Generated Admin Panel**: `http://127.0.0.1:8000/admin/` (create admin account via `tblinc createsuperuser`)
- **Admin tblinc AI (`ai_chat`)**: `http://127.0.0.1:8000/admin/ai/`
- **Admin Model Hub (25 Models)**: `http://127.0.0.1:8000/admin/models/`
- **Admin Training**: `http://127.0.0.1:8000/admin/train/`
- **Admin Keys & Quotas**: `http://127.0.0.1:8000/admin/keys/`
- **Admin Settings**: `http://127.0.0.1:8000/admin/settings/`
- **Hardware & System API**: `http://127.0.0.1:8000/api/system/`

## Package Architecture (`src/tblinc_open_source/`)

- `ai_models/` — **25 modular AI model folders** + `core/` & `hardware/` (CUDA / Intel XPU / OpenVINO / CPU detection)
- `web/` — **12 modular web framework folders** (`admin`, `auth`, `core`, `forms`, `http`, `middleware`, `orm`, `routing`, `staticfiles`, `templates`, `testing`, `views`)
- `generator/` — **modular project scaffolder** (`builder.py`, `backend_files.py`, `theme_assets.py`, `html_templates.py`)
- `cli/` — **modular CLI package** (`parser.py`, `commands.py`)

## 12 Modular Web Framework Folders (`src/tblinc_open_source/web/`)

| # | Folder | Purpose |
|---|---|---|
| 1 | `web/core/` | `TblincApp` WSGI core, auto asset sync & threaded dev server |
| 2 | `web/http/` | `Request`, `Response`, JSON/HTML/Redirect/Static responses & HTTP errors (`400`/`403`/`404`/`429`) |
| 3 | `web/routing/` | Typed URL router (`<int:pk>`, `<str:slug>`, `<path:rest>`) & `url_for` |
| 4 | `web/orm/` | Declarative SQLite ORM, typed fields, `QuerySet`, validation & additive column auto-migrations |
| 5 | `web/templates/` | Custom template engine (`extends`/`block`/`include`/`if`/`for`) & Tailwind/Lucide/Motion layouts |
| 6 | `web/forms/` | `Form` & auto-generated `ModelForm` with Tailwind widgets, user dropdowns & `<datalist>` presets |
| 7 | `web/auth/` | `User`/`Session` models, PBKDF2 hashing, signed cookies, CSRF, Profile, Billing & Settings views |
| 8 | `web/middleware/` | Session/CSRF, security headers, CORS, and response timing middleware |
| 9 | `web/views/` | MTV `render()` helper & MVC `Controller` / `ModelController` |
| 10 | `web/admin/` | Auto-generated Admin Panel, `ai_chat`, Model Hub, Model Trainer, API Keys, Quotas, Transactions & Settings |
| 11 | `web/staticfiles/` | Safe static file handler with path-traversal protection |
| 12 | `web/testing/` | In-process WSGI `TestClient` with automatic cookie jar |

## 27 Modular Folders in `src/tblinc_open_source/ai_models/` (25 AI Models + `core/` + `hardware/`)

| # | Folder | Model / Module | Category |
|---|---|---|---|
| 1 | `ai_models/audio/` | Sound & Speech Classifier | Audio / Speech |
| 2 | `ai_models/boost/` | Gradient Boosting AI | Tabular / ML |
| 3 | `ai_models/chat/` | AI Text & Chat Model | LLM / NLP |
| 4 | `ai_models/classify/` | Smart Category Classifier | Tabular / ML |
| 5 | `ai_models/cluster/` | Smart Data Clustering | Unsupervised ML |
| 6 | `ai_models/detector/` | Anomaly & Fraud Detector | Anomaly & Security |
| 7 | `ai_models/embed/` | Text Embedding Engine | Vector & Search |
| 8 | `ai_models/forecast/` | Trend Forecaster | Time Series |
| 9 | `ai_models/forest/` | Random Forest AI | Tabular / ML |
| 10 | `ai_models/image/` | AI Image Generator | Generative / Diffusion |
| 11 | `ai_models/multimodal/` | Vision-Language AI | VLM / Multimodal |
| 12 | `ai_models/music/` | AI Music Composer | Audio / Music |
| 13 | `ai_models/neural/` | Deep Neural Network | Deep Learning |
| 14 | `ai_models/objects/` | Object Detection AI | Computer Vision |
| 15 | `ai_models/predict/` | Numeric Value Predictor | Tabular / ML |
| 16 | `ai_models/recommend/` | Smart Recommender | Recommendation Systems |
| 17 | `ai_models/search/` | Knowledge Search (RAG) | RAG & Search |
| 18 | `ai_models/sentiment/` | Sentiment Analyzer | LLM / NLP |
| 19 | `ai_models/similarity/` | Similarity Matcher | Tabular / ML |
| 20 | `ai_models/summarize/` | Text Summarizer AI | LLM / NLP |
| 21 | `ai_models/transcribe/` | Speech-to-Text AI | Audio / Speech |
| 22 | `ai_models/tree/` | Decision Tree AI | Tabular / ML |
| 23 | `ai_models/video/` | AI Video Generator | Video AI |
| 24 | `ai_models/vision/` | Image Recognition AI | Computer Vision |
| 25 | `ai_models/voice/` | AI Voice Generator | Audio / TTS |
| — | `ai_models/core/` | `BaseAIModel`, `ModelMetadata`, `PredictionResult`, `ModelRegistry` | Core Runtime |
| — | `ai_models/hardware/` | CUDA, Intel XPU, OpenVINO, MPS & CPU detector | Hardware Runtime |
