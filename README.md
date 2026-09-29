# Comic Craft Giri - AI Comic Story Creator

Comic Craft Giri (CCG) is an end-to-end AI comic studio that turns character ideas, loose prompts, and wild scenarios into complete 5-panel comic book stories, character dialogues, narrative captions, and stylized illustrations.

Built with **FastAPI**, **Google Gemini AI**, **Multi-Tier Comic Illustration Engines**, and **FPDF2**, Comic Craft Giri provides an authentic comic studio workflow from prompt creation to multi-page PDF comic export with Day/Night mode theming.

---

## Technical Architecture

```
User Scenario & Preferences
         │
         ▼
[ FastAPI Backend: app/routes.py ]
         │
         ├──► 1. [ app/gemini_flash.py ]  ──► Structured 5-panel outline & scene prompts
         ├──► 2. [ app/gemini_pro.py ]    ──► Narration, SFX captions, character dialogues
         ├──► 3. [ app/image_generator.py]──► Multi-tier AI & scene artwork illustrations
         ├──► 4. [ app/layout_builder.py] ──► Sequential 5-panel comic data layout
         └──► 5. [ app/exporters.py ]     ──► Multi-page styled comic book PDF
         │
         ▼
[ Studio Frontend: templates/comic_preview.html / export_success.html ]
```

### Models & Services Used
- **Google Gemini Flash (`models/gemini-3.8-flash` / `models/gemini-flash-latest`)**: Rapid, structured generation of the 5-panel comic outline and scene prompts with prompt-aware fallback.
- **Google Gemini Pro (`models/gemini-3.8-flash` / `models/gemini-pro-latest`)**: Narrative storytelling, character dialogues, and atmospheric sound effect captions (SFX).
- **Multi-Tier Comic Illustration Engine (`app/image_generator.py`)**: 
  - **Tier 1**: Authenticated Hugging Face text-to-image inference using Stable Diffusion 3 Medium.
  - **Tier 2**: Pollinations cloud fallback for temporary provider failures.
  - **Tier 3**: Offline comic canvas fallback so a comic can still complete when cloud providers are unavailable.
- **FPDF2 Exporter (`app/exporters.py`)**: Assembles comic cover art, sequential panels, speech bubbles, and narrative captions into a downloadable PDF.
- **Studio Frontend (`templates/`, `static/`)**: Authentic CCG studio aesthetic with tilted crimson wordmark stamp, Day & Night mode theming, and responsive layout.

---

## Rich Scenario & Setting Options

The studio form includes diverse curated presets plus custom options:

### 1. Curated Settings
- **Hidden Leaf Village & Ichiraku Ramen Shop** *(Anime / Ninja)*
- **Cyberpunk Metropolis & Neon Alleys** *(Neo-Tokyo / Sci-Fi)*
- **Enchanted Ancient Forest** *(High Fantasy)*
- **Deep Space Starship Cruiser** *(Galactic)*
- **Gothic City Rooftops** *(Dark Noir / Detective)*
- **Haunted Victorian Academy** *(Supernatural)*
- **Steampunk Airship Citadel** *(Adventure)*
- **Post-Apocalyptic Wasteland** *(Survival)*
- **Sunken Atlantis Ruins** *(Underwater Empire)*
- **Feudal Samurai Dojo** *(Martial Arts)*
- **Ancient Dragon Peak** *(Mythic)*
- **Custom Setting** *(Write your own custom world)*

### 2. Story Tones
- **Action Shonen**
- **Epic Adventure**
- **Funny & Humorous**
- **Dramatic**
- **Light-hearted & Whimsical**
- **Dark Mystery & Noir**
- **Poetic & Atmospheric**

### 3. Art Styles
- **Shonen Manga / Anime**
- **Classic DC/Marvel Comic Book**
- **Dark Graphic Novel (Noir Ink)**
- **Cyberpunk Neon**
- **Vintage 1980s Pulp Comic**
- **Watercolor Fantasy**
- **Pixel Art Retro**

---

## Directory Structure

```
Comic Craft Giri/
├── .env.example              # Environment variables template
├── .env                      # Local environment configuration
├── requirements.txt          # Python dependencies
├── README.md                 # Complete documentation & setup guide
├── .vscode/
│   ├── launch.json           # VS Code debug & run configurations
│   ├── settings.json         # Workspace settings & test discovery
│   └── extensions.json       # Recommended VS Code extensions
├── app/
│   ├── __init__.py           # App package
│   ├── main.py               # FastAPI entry point & directory startup
│   ├── routes.py             # Route handlers (/, /generate, /generate-comic/json, etc.)
│   ├── gemini_flash.py       # Outline generation service
│   ├── gemini_pro.py         # Narration & dialogue script generator
│   ├── image_generator.py    # Multi-tier comic illustration engine
│   ├── layout_builder.py     # Layout assembly service
│   └── exporters.py          # Multi-page PDF generation engine
├── static/
│   ├── css/
│   │   ├── style.css         # CCG studio styling & Day/Night theming
│   │   └── comic.css         # Comic frames, speech bubbles & layout styles
│   ├── js/
│   │   └── app.js            # Prompt chips, theme toggle & generation stepper
│   ├── panels/               # Generated comic panel images (.png)
│   └── exports/              # Compiled comic PDF files (.pdf)
├── templates/
│   ├── index.html            # Main comic generation studio form
│   ├── comic_preview.html    # 5-panel sequential reader & PDF trigger
│   └── export_success.html   # Download confirmation & showcase
└── tests/
    ├── __init__.py
    ├── test_gemini.py        # Gemini service tests
    ├── test_image.py         # Image generator tests
    ├── test_layout.py        # Layout builder & PDF exporter tests
    └── test_routes.py        # FastAPI route integration tests
```

---

---

## 🚀 How to Run Locally (From GitHub)

Follow these simple step-by-step instructions to get Comic Craft Giri running on your local machine.

### 1. Prerequisites
Ensure you have the following installed on your computer:
- **Python 3.10 or newer** (Check with `python --version` or download from [python.org](https://www.python.org/downloads/))
- **Git** ([git-scm.com](https://git-scm.com/))
- **A Free Google Gemini API Key**: Get a free API key in seconds from [Google AI Studio](https://aistudio.google.com/)

---

### 2. Step-by-Step Installation

#### Step 1: Clone the Repository
Open your terminal (PowerShell, Command Prompt, or Terminal on macOS/Linux) and run:
```bash
git clone https://github.com/your-username/comic-craft-giri.git
cd comic-craft-giri
```

#### Step 2: Create a Virtual Environment
It is recommended to use an isolated Python virtual environment:
- **Windows (PowerShell or CMD)**:
  ```powershell
  python -m venv venv
  ```
- **macOS / Linux**:
  ```bash
  python3 -m venv venv
  ```

#### Step 3: Activate the Virtual Environment
- **Windows (PowerShell)**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
  *(If you get a script execution policy warning in PowerShell, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and then run the activate command again).*
- **Windows (Command Prompt)**:
  ```cmd
  venv\Scripts\activate.bat
  ```
- **macOS / Linux**:
  ```bash
  source venv/bin/activate
  ```

#### Step 4: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 5: Configure Your API Key
1. Copy the example environment file:
   - **Windows (PowerShell / CMD)**:
     ```powershell
     copy .env.example .env
     ```
   - **macOS / Linux**:
     ```bash
     cp .env.example .env
     ```
2. Open `.env` in any text editor and paste your Gemini API key:
   ```env
   GEMINI_API_KEY=AIzaSy...your_actual_key_here
   GEMINI_FLASH_MODEL=gemini-flash-lite-latest
   GEMINI_PRO_MODEL=gemini-3.8-flash
   ```
3. To use Hugging Face for the panel artwork, add a Hugging Face user-access token
   with **Inference Providers** permission. ComicCraft sends panels one at a time,
   rather than as a five-request burst, to avoid serverless inference queue and
   rate-limit errors:
   ```env
   HF_API_KEY=hf_your_token_here
   ```

   The default provider model is `stabilityai/stable-diffusion-3-medium-diffusers`.
   To switch to another supported Hugging Face Inference endpoint in the future,
   add its full endpoint URL:
   ```env
   HF_INFERENCE_URL=https://router.huggingface.co/hf-inference/models/your-supported-model
   ```

---

### 3. Running the Application

#### Option A: One-Click Launch in VS Code
1. Open the project folder in VS Code:
   ```bash
   code .
   ```
2. Press **`F5`** (or click **Run and Debug** -> **"Python: Run ComicCraft Server"**).

#### Option B: Launch from Terminal
With your virtual environment active, run:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

---

### 4. Open in Your Browser
Once the server starts, open your browser and navigate to:
- 🌐 **Comic Studio Interface**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- 📖 **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 🩺 **System Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

### 5. Running Automated Tests

To verify that all services, routes, Gemini single-call integration, and image generators are functioning properly:
```bash
pytest -v
```
All 11 unit and route test suites will execute and validate the system.

---

### 🛠️ Common Troubleshooting & Tips

- **PowerShell Script Error (`cannot be loaded because running scripts is disabled`)**:
  Run this one-time command in your PowerShell:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  ```
- **Gemini Quota Management**:
  Comic Craft Giri consolidates storyboard generation, narrative narration, character dialogue, and image prompts into **1 single Gemini API call** per comic, staying well within free-tier limits without burning credits.
- **Image Generation**:
  The application uses Hugging Face inference first when `HF_API_KEY` is configured.
  If the token is absent, rejected, rate limited, or the service is unavailable, it
  falls back to the available renderer so the comic pipeline can still finish. A
  401/403 response means the token is invalid or missing Inference Providers permission;
  a 429/503 response means Hugging Face is rate limiting or loading the model.

- **Hugging Face HTTP 410 (retired model)**:
  This means Hugging Face no longer serves the configured model through the selected
  provider; it is not a token error. The application defaults to Stable Diffusion 3
  Medium, a supported Hugging Face inference model. If a future model retirement
  occurs, set `HF_INFERENCE_URL` to a current supported endpoint and restart the server.

- **`quote_from_bytes() expected bytes` during fallback**:
  This previously occurred when an image prompt was missing or not plain text.
  ComicCraft now converts every panel prompt into safe text before calling either
  Hugging Face or the fallback generator.

- **Generated outputs are intentionally not committed**:
  `static/panels/` and `static/exports/` remain in the project structure but their
  generated images and PDFs are ignored by Git. This keeps the repository small and
  prevents local comic output from being published accidentally.
