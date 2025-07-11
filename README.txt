# PhishGuard AI

A desktop application for hybrid phishing-email detection, combining machine learning and heuristic rules.

Project Structure

Within this folder/
├ main.py
├ models/
│  ├ tfidf\_vectorizer.pkl
│  ├ logistic\_model.pkl
│  ├ naive\_bayes\_model.pkl
│  ├ random\_forest\_model.pkl
│  ├ xgb\_model.pkl
│  └ voting\_model.pkl
├ keywords.json
├ install.bat
├ run\_phishguard.bat
└ README.txt

Prerequisites

• Windows 7/8/10/11 (for automated setup via install.bat) or any OS with Python 3.6+
• Python 3.6+ installed and on your PATH
• (Optional) Virtual environment tool (venv)

Installation

**Windows (automated)**

1. Copy or unzip “Ready to submit” to your local drive.
2. Change directory to the project folder:

   ```bat
   cd "C:\Users\Amir\Desktop\PhishGuardAI-Amir Mehdi Memari"
   ```
3. Run the automated installer:

   ```bat
   install.bat
   ```

   This will create and activate a virtual environment, upgrade pip, and install all dependencies.

After installation, you can launch the app by running **run\_phishguard.bat**.

**Manual or other OS**

1. Copy or unzip to your local drive.
2. (Optional) Create & activate a virtual environment:

   ```bash
   cd "/path/to/Ready to submit"
   python3 -m venv venv
   source venv/bin/activate   # or venv\Scripts\activate on Windows
   ```
3. Install dependencies:

   ```bash
   pip install pyqt5 joblib numpy reportlab matplotlib xgboost scikit-learn
   ```

Usage

**Via batch launcher**

1. Double-click **run\_phishguard.bat**

   * Or from a command prompt:

     ```bat
     cd "C:\Users\Amir\Desktop\PhishGuardAI-Amir Mehdi Memari"
     run_phishguard.bat [path_to_email.eml]
     ```

**Via direct Python**

```bash
cd "/path/to/Ready to submit"
python main.py [path_to_email.eml]
```

If no `.eml` argument is passed, the GUI will prompt you to browse for a file.

Configuration

• Model files are stored in `models/*.pkl`.
• Heuristic keywords are in `keywords.json`.
• Both `install.bat` and `run_phishguard.bat` auto-detect paths relative to the project root.

Troubleshooting

• **ModuleNotFoundError: sklearn**
→ `pip install scikit-learn`

• **Missing model files**
→ Ensure `models/*.pkl` exist and are named correctly.

• **Batch file does nothing**
→ Verify `python` is on your PATH.
→ Activate venv then re-run.

License & Contact

MIT License
For support, contact Amir Mehdi Memari: amirmahdimemari@gmail.com
Enjoy effective phishing detection!
