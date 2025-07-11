import sys                                 # Access system-specific parameters and functions
import os                                  # Interact with the operating system (paths, files)
import json                                # Read/write JSON configuration files
import re                                  # Regular expressions for pattern matching
import joblib                              # Load and save serialized ML models
import numpy as np                         # Numerical operations (arrays, math)
import sklearn                             # Machine learning utilities (for type access)
import xgboost                             # XGBoost gradient boosting library
from datetime import datetime              # Work with dates and times
from email import policy                   # Define parsing policies for email messages
from email.parser import BytesParser       # Parse raw bytes into email.Message objects

from PyQt5.QtWidgets import (              # Import Qt widgets for GUI construction
    QApplication, QMainWindow, QTextEdit, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QWidget, QFileDialog, QTableWidget, QTableWidgetItem, QDockWidget, QListWidget,
    QListWidgetItem, QToolButton, QDialog, QComboBox, QDialogButtonBox, QLineEdit,
    QMessageBox, QListView, QAbstractItemView, QSlider, QCheckBox, QSplashScreen
)
from PyQt5.QtCore import (                 # Import Qt core classes for events and properties
    Qt, QSettings, QTimer, QPropertyAnimation, QEasingCurve
)
from PyQt5.QtGui import (                  # Import Qt GUI classes for styling and images
    QTextCursor, QTextCharFormat, QBrush, QColor, QIcon, QPixmap, QTextDocument
)

from reportlab.pdfgen import canvas         # Generate PDF reports
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas  # Embed Matplotlib in Qt
from matplotlib.figure import Figure        # Create Matplotlib figures

# === Path utility for PyInstaller compatibility ===
def resource_path(relative_path):          # Define function to get bundle path in PyInstaller
    try:
        base_path = sys._MEIPASS           # If running as a PyInstaller bundle, get temp folder
    except AttributeError:
        base_path = os.path.abspath(".")   # Otherwise use current working directory
    return os.path.join(base_path, relative_path)  # Join base path with relative path

# === Load Models ===
vectorizer = joblib.load(resource_path("models/tfidf_vectorizer.pkl"))  # Load TF-IDF vectorizer
models = {                                # Load each individual ML model
    "Logistic Regression": joblib.load(resource_path("models/logistic_model.pkl")),
    "Naive Bayes":          joblib.load(resource_path("models/naive_bayes_model.pkl")),
    "Random Forest":        joblib.load(resource_path("models/random_forest_model.pkl")),
    "XGBoost":              joblib.load(resource_path("models/xgb_model.pkl")),
    "Voting Classifier":    joblib.load(resource_path("models/voting_model.pkl")),
}
model_weights = {                         # Assign weights for ensemble voting
    "XGBoost": 0.3,
    "Random Forest": 0.25,
    "Logistic Regression": 0.2,
    "Naive Bayes": 0.15,
    "Voting Classifier": 0.1,
}

# === Load Heuristic Keywords from JSON ===
KEYWORD_FILE = r"C:\Users\Amir\Desktop\New folder\Deployment\keywords.json"  # Path to heuristics file
with open(KEYWORD_FILE, "r", encoding="utf-8") as f:  # Open heuristics JSON
    hk = json.load(f)                     # Parse into Python dict

suspicious_keywords        = hk["suspicious_keywords"]        # Words indicating possible phishing
force_flag_keywords        = hk["force_flag_keywords"]        # Words forcing a phishing label
benign_keywords            = hk["benign_keywords"]            # Words indicating benign content
academic_phishing_keywords = hk["academic_phishing_keywords"] # Keywords specific to academic phishing

# === Load exact GCET staff emails for full trust ===
STAFF_FILE = r"C:\Users\Amir\Desktop\New folder\Deployment\gcet_staff.json"  # Staff list path
with open(STAFF_FILE, "r", encoding="utf-8") as f:  # Open staff JSON
    staff_emails = set(json.load(f))         # Parse list into a set for fast lookup

trusted_domains = {"gcet.edu.om"}            # Domains considered fully trusted

# === UI Themes ===
THEMES = {                                  # Define CSS styles for multiple UI themes
    "Light": """
        QWidget { background-color: #fefefe; color: #202020; }
        QPushButton { background-color: #1e88e5; color: white; padding: 5px; border-radius: 6px; }
    """,
    "Dark": """
        QWidget { background-color: #1e1e1e; color: #e0e0e0; }
        QPushButton { background-color: #00acc1; color: black; font-weight: bold; padding: 5px; border-radius: 6px; }
    """,
    "Solarized": """
        QWidget { background-color: #002b36; color: #fdf6e3; }
        QPushButton { background-color: #859900; color: #002b36; font-weight: bold; padding: 5px; border-radius: 6px; }
    """,
    "High Contrast": """
        QWidget { background-color: #000000; color: #ffffff; font-weight: bold; }
        QPushButton { background-color: #ff1744; color: white; font-weight: bold; padding: 5px; border-radius: 6px; }
    """
}

# === Theme Selection Dialog ===
class ThemeDialog(QDialog):                 # Popup dialog to choose a UI theme
    def __init__(self, parent=None):
        super().__init__(parent)            # Initialize base QDialog
        self.setWindowTitle("Select Theme") # Set dialog title
        layout = QVBoxLayout()              # Vertical layout container
        self.combo = QComboBox()            # Dropdown widget
        self.combo.addItems(THEMES.keys())  # Populate with theme names
        layout.addWidget(QLabel("Choose a theme:"))  # Instruction label
        layout.addWidget(self.combo)        # Add dropdown to layout
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)   # OK → accept dialog
        self.buttons.rejected.connect(self.reject)   # Cancel → reject dialog
        layout.addWidget(self.buttons)      # Add buttons to layout
        self.setLayout(layout)              # Set dialog layout

    def selected_theme(self):             # Return currently selected theme
        return self.combo.currentText()

# === Threshold Adjustment Dialog ===
class ThresholdDialog(QDialog):           # Popup to adjust phishing-probability threshold
    def __init__(self, current_threshold, parent=None):
        super().__init__(parent)            # Initialize base QDialog
        self.setWindowTitle("Adjust Risk Threshold")  # Title
        self.slider = QSlider(Qt.Horizontal) # Horizontal slider widget
        self.slider.setRange(50, 95)         # Range 0.50 to 0.95 when divided by 100
        self.slider.setValue(int(current_threshold * 100))  # Set initial slider pos
        self.slider.setTickInterval(5)       # Tick every 5 units
        self.slider.setTickPosition(QSlider.TicksBelow)  # Show ticks below
        self.label = QLabel(f"Threshold: {current_threshold:.2f}")  # Display current value
        self.slider.valueChanged.connect(lambda v: self.label.setText(f"Threshold: {v/100:.2f}"))
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)   # OK → accept
        self.buttonBox.rejected.connect(self.reject)   # Cancel → reject
        layout = QVBoxLayout()              # Vertical layout
        layout.addWidget(self.label)        # Show label
        layout.addWidget(self.slider)       # Show slider
        layout.addWidget(self.buttonBox)    # Show buttons
        self.setLayout(layout)              # Apply layout

    def get_threshold(self):               # Return slider value as float [0,1]
        return self.slider.value() / 100

# === Confidence Bar Chart Widget ===
class BarChartCanvas(FigureCanvas):      # Canvas to plot model confidence bars
    def __init__(self, parent=None):
        fig = Figure(figsize=(5, 2))      # Create figure of size 5×2 inches
        self.ax = fig.add_subplot(111)    # Add single subplot
        super().__init__(fig)             # Initialize FigureCanvas

    def plot_confidence(self, results):   # Plot bar chart of model probabilities
        self.ax.clear()                   # Clear previous figure
        names = list(results.keys())      # Model names
        probs = [results[n]["prob"] for n in names]  # Corresponding probabilities
        colors = ['green' if p < 0.5 else 'orange' if p < 0.7 else 'red' for p in probs]  # Color code
        self.ax.bar(names, probs, color=colors)  # Draw bars
        self.ax.set_ylim(0, 1)            # Y-axis from 0 to 1
        self.ax.set_ylabel("Probability") # Y-axis label
        self.ax.set_title("Model Confidence")  # Title
        self.draw()                       # Render plot

# === Email (.eml) File Parser ===
class EmlParser:                         # Helper to extract parts from .eml files
    def __init__(self, path):
        self.path = path                  # Store file path
        self.msg  = BytesParser(policy=policy.default).parse(open(path, 'rb'))  # Parse email

    def get_sender(self):                 # Return "From" header
        return self.msg.get("From", "")

    def get_subject(self):                # Return "Subject" header
        return self.msg.get("Subject", "")

    def get_body(self):                   # Extract plain-text body
        if self.msg.is_multipart():       # If multipart, search for text/plain
            for part in self.msg.walk():
                if part.get_content_type() == "text/plain":
                    return part.get_payload(decode=True).decode(errors='ignore')
        return self.msg.get_payload(decode=True).decode(errors='ignore')  # Otherwise decode directly

    def get_headers(self):                # Return full headers as string
        return str(self.msg)

# === Main Application Window ===
class MainWindow(QMainWindow):           # Main GUI window for PhishGuard AI
    def __init__(self):
        super().__init__                 # Initialize QMainWindow
        super().__init__()               # Call parent constructor
        self.setWindowTitle("PhishGuard AI – by Amir Mehdi Memari")  # Window title
        self.setWindowIcon(QIcon(resource_path("logo.png")))        # Window icon
        self.resize(1200, 850)            # Default size

        self.settings      = QSettings("PhishGuard", "Config")  # Persistent settings
        self.threshold     = float(self.settings.value("threshold", 0.7))  # Default threshold
        self.current_theme = self.settings.value("theme", "Light")        # Default theme

        # Sidebar Drawer
        self.drawer = QDockWidget("Navigation", self)  # Dockable navigation panel
        self.drawer.setAllowedAreas(Qt.LeftDockWidgetArea)  # Only left side
        self.drawer.setFeatures(QDockWidget.DockWidgetClosable)  # Can close
        self.drawer_list = QListWidget()  # List of actions
        for name in [                   # Define menu items
            "📜 History", "📂 Open File", "🎨 Theme", "⚙️ Settings",
            "🖨️ Export", "📚 Learn", "📝 Feedback", "ℹ️ About"
        ]:
            QListWidgetItem(name, self.drawer_list)  # Add each to list
        self.drawer_list.itemClicked.connect(self.drawer_action)  # Connect click handler
        self.drawer.setWidget(self.drawer_list)  # Set as widget in dock
        self.addDockWidget(Qt.LeftDockWidgetArea, self.drawer)  # Add dock to main window

        # Inputs & Controls
        self.hamburger_btn = QToolButton()  # Button to toggle sidebar
        self.hamburger_btn.setText("☰")     # Hamburger icon
        self.hamburger_btn.clicked.connect(
            lambda: self.drawer.setVisible(not self.drawer.isVisible())  # Toggle visibility
        )

        self.sender_input  = QLineEdit(); self.sender_input.setPlaceholderText("Sender Email")  # Sender field
        self.subject_input = QLineEdit(); self.subject_input.setPlaceholderText("Email Subject")  # Subject field
        self.body_input    = QTextEdit(); self.body_input.setPlaceholderText("Paste email body here...")  # Body text area

        self.result_label     = QLabel("Result: Pending")  # Prediction label
        self.result_label.setStyleSheet("font-weight: bold;")  # Bold text
        self.risk_level_label = QLabel("Risk: Unknown")  # Risk level label
        self.explain_label    = QLabel("")   # Explanation label
        self.threat_label     = QLabel("Threat Intel: None")  # Threat intel label

        predict_btn     = QPushButton("Predict")  # Trigger prediction
        predict_btn.clicked.connect(self.predict)
        export_btn      = QPushButton("Export PDF")  # Export to PDF
        export_btn.clicked.connect(self.export_pdf)
        clear_btn       = QPushButton("Clear")  # Clear inputs
        clear_btn.clicked.connect(self.clear_inputs)
        feedback_safe   = QPushButton("👍 Actually Safe")  # User feedback: safe
        feedback_safe.clicked.connect(lambda: self.save_feedback("SAFE"))
        feedback_phish  = QPushButton("👎 Actually Phishing")  # User feedback: phishing
        feedback_phish.clicked.connect(lambda: self.save_feedback("PHISHING"))

        self.chart = BarChartCanvas()  # Embed confidence bar chart
        self.table = QTableWidget(len(models), 3)  # Table for model-by-model results
        self.table.setHorizontalHeaderLabels(["Model", "Prob", "Pred"])  # Column headers
        self.table.verticalHeader().setVisible(False)  # Hide row headers
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # Make read-only
        self.table.setAlternatingRowColors(True)  # Zebra striping
        self.table.horizontalHeader().setStretchLastSection(True)  # Stretch last column

        # Layout Setup
        control_layout = QHBoxLayout()  # Horizontal layout for controls
        control_layout.addWidget(self.hamburger_btn)
        control_layout.addWidget(predict_btn)
        control_layout.addWidget(export_btn)
        control_layout.addWidget(clear_btn)
        control_layout.addStretch()
        control_layout.addWidget(self.risk_level_label)

        feedback_layout = QHBoxLayout()  # Horizontal layout for feedback buttons
        feedback_layout.addWidget(feedback_safe)
        feedback_layout.addWidget(feedback_phish)

        layout = QVBoxLayout()  # Main vertical layout
        layout.addWidget(QLabel("🔐 PhishGuard AI – v1.0"))  # Title label
        layout.addWidget(self.sender_input)
        layout.addWidget(self.subject_input)
        layout.addWidget(self.body_input)
        layout.addLayout(control_layout)
        layout.addWidget(self.result_label)
        layout.addWidget(self.explain_label)
        layout.addWidget(self.threat_label)
        layout.addWidget(self.table)
        layout.addWidget(self.chart)
        layout.addLayout(feedback_layout)

        footer = QLabel("© 2025 Amir Mehdi Memari – Powered by Machine Learning")  # Footer text
        footer.setAlignment(Qt.AlignCenter)  # Center alignment
        footer.setStyleSheet("color: gray; padding: 6px;")  # Gray, padded
        layout.addWidget(footer)

        container = QWidget()  # Central widget container
        container.setLayout(layout)  # Apply main layout
        self.setCentralWidget(container)  # Set as main window content
        self.apply_theme()  # Apply saved theme

    def apply_theme(self):                   # Apply stylesheet based on selected theme
        self.setStyleSheet(THEMES.get(self.current_theme, ""))

    def drawer_action(self, item):           # Handle sidebar menu clicks
        label = item.text()
        if "Theme" in label:                # If theme item clicked
            dlg = ThemeDialog(self)
            if dlg.exec_():                  # Show dialog
                self.current_theme = dlg.selected_theme()
                self.settings.setValue("theme", self.current_theme)
                self.apply_theme()
        elif "Settings" in label:           # If settings clicked
            dlg = ThresholdDialog(self.threshold, self)
            if dlg.exec_():
                self.threshold = dlg.get_threshold()
                self.settings.setValue("threshold", self.threshold)
        elif "Open File" in label:          # Open an email or text file
            fname, _ = QFileDialog.getOpenFileName(
                self, "Open Email File", "", "Email/Text Files (*.eml *.txt *.html)"
            )
            if fname.endswith(".eml"):
                eml = EmlParser(fname)
                self.sender_input.setText(eml.get_sender())
                self.subject_input.setText(eml.get_subject())
                self.body_input.setText(eml.get_body())
                self.last_headers = eml.get_headers()
            else:
                with open(fname, 'r', encoding='utf-8', errors='ignore') as f:
                    self.body_input.setText(f.read())
        elif "Feedback" in label or "History" in label:  # Show feedback history
            self.show_feedback_log()
        elif "Export" in label:             # Export PDF via menu
            self.export_pdf()
        elif "Learn" in label:              # Show informational popup
            QMessageBox.information(
                self, "Learn",
                "PhishGuard AI uses multiple ML models:\n\n"
                "🔹 Logistic Regression – fast, interpretable.\n"
                "🔹 Naive Bayes – simple, spam detection.\n"
                "🔹 Random Forest – ensemble of trees.\n"
                "🔹 XGBoost – powerful gradient booster.\n"
                "🔹 Voting Classifier – combines all models.\n\n"
                "Also uses heuristics from an external JSON file."
            )
        elif "About" in label:              # Show about dialog
            QMessageBox.information(
                self, "About",
                "PhishGuard AI\nBuilt by Amir Mehdi Memari\nPowered by Machine Learning"
            )

    def highlight_keywords(self, text, extra_keywords=None):  # Highlight suspicious terms
        self.body_input.moveCursor(QTextCursor.Start)  # Move cursor to start
        cursor = self.body_input.textCursor()
        fmt = QTextCharFormat()                      # Define text format
        fmt.setBackground(QBrush(QColor("yellow")))  # Yellow highlight

        keywords = suspicious_keywords[:]            # Base suspicious list
        if extra_keywords:
            keywords += extra_keywords               # Add any extra

        for word in keywords:                        # Loop through each keyword
            pos = 0
            while True:
                cursor = self.body_input.document().find(word, pos, QTextDocument.FindCaseSensitively)
                if cursor.isNull():
                    break
                cursor.mergeCharFormat(fmt)          # Apply highlight
                pos = cursor.position()

    def predict(self):                           # Run phishing prediction
        sender  = self.sender_input.text().strip()        # Sender email
        subject = self.subject_input.text().strip()       # Email subject
        body    = self.body_input.toPlainText().strip()   # Email body
        full_text = f"{sender} {subject} {body}".lower()  # Combine & lowercase

        if not sender or not subject or not body:         # Check required fields
            QMessageBox.warning(self, "Missing Fields", "Please fill in sender, subject, and body.")
            return

        # Highlight academic keywords
        academic_hits = [kw for kw in academic_phishing_keywords if kw in full_text]
        num_academic_hits = len(academic_hits)
        self.highlight_keywords(body, extra_keywords=academic_hits)

        # SPF/DKIM checks in last opened .eml headers
        spf_fail = dkim_fail = False
        if hasattr(self, "last_headers"):
            hdr = self.last_headers.lower()
            spf_fail  = "spf=fail" in hdr or "spf=softfail" in hdr
            dkim_fail = "dkim=fail" in hdr

        # Exact-match trust for known staff
        is_trusted = sender in staff_emails

        # Domain-adjusted threshold for non-staff addresses
        sender_domain = sender.split("@")[-1] if "@" in sender else ""
        if sender_domain.endswith("gcet.edu.om"):
            adjusted_threshold = min(self.threshold + 0.10, 0.95)
        else:
            adjusted_threshold = max(self.threshold - 0.10, 0.50)

        # Vectorize text for model input
        vec = vectorizer.transform([full_text])
        result = {}
        weighted_sum = total_weight = 0
        for i, (name, model) in enumerate(models.items()):  # For each ML model
            try:
                prob  = model.predict_proba(vec)[0][1]  # Phishing probability
                label = int(prob > adjusted_threshold)  # 1 if above threshold
                weight= model_weights.get(name, 0.2)    # Model weight
                weighted_sum += prob * weight
                total_weight += weight
                result[name] = {"prob": prob, "label": label}
                self.table.setItem(i, 0, QTableWidgetItem(name))
                self.table.setItem(i, 1, QTableWidgetItem(f"{prob:.2f}"))
                self.table.setItem(i, 2, QTableWidgetItem(str(label)))
            except Exception as e:
                print(f"Model {name} failed: {e}")

        avg_prob = (weighted_sum / total_weight) if total_weight else 0  # Weighted average
        votes    = sum(r["label"] for r in result.values())           # Sum of binary votes
        force    = any(k in full_text for k in force_flag_keywords)   # Force flag
        benign   = any(k in full_text for k in benign_keywords)       # Benign override
        high     = any(r["prob"] > adjusted_threshold for r in result.values())  # Any high prob

        # Final decision logic
        if not is_trusted:
            if votes >= 4 or (high and not benign) or (force and not benign) or spf_fail or dkim_fail or num_academic_hits >= 5:
                is_phish = True
            elif votes == 2 or avg_prob > 0.6 or num_academic_hits >= 3:
                is_phish = "unsure"
            else:
                is_phish = False
        else:
            is_phish = False  # Trusted staff always safe

        # Update UI with result
        if is_phish is True:
            self.result_label.setText("Result: PHISHING ⚠️")
            self.risk_level_label.setText("Risk: 🔴 High")
            self.risk_level_label.setStyleSheet("color: red; font-weight: bold;")
        elif is_phish == "unsure":
            self.result_label.setText("Result: UNSURE ⚠️")
            self.risk_level_label.setText("Risk: 🟠 Medium")
            self.risk_level_label.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.result_label.setText("Result: SAFE ✅")
            self.risk_level_label.setText("Risk: 🟢 Low")
            self.risk_level_label.setStyleSheet("color: green; font-weight: bold;")

        self.explain_label.setText(f"Phishing Score: {avg_prob:.2f} | Votes: {votes}/5")

        urls = re.findall(r"https?://[\w./\\-]+", full_text)  # Extract URLs
        mismatch = [u for u in urls if any(f in u for f in ["verify","phishy",".xyz","alert","suspend"])]
        self.threat_label.setText(f"Threat Intel: {len(mismatch)} flagged URLs | {num_academic_hits} academic keywords")

        self.chart.plot_confidence(result)  # Refresh bar chart

    def export_pdf(self):                      # Export report to PDF
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Report As", "phishing_report.pdf", "PDF Files (*.pdf);;All Files (*)"
        )
        if not path:
            return
        text = self.body_input.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "Nothing to Export", "Email body is empty.")
            return
        c = canvas.Canvas(path)               # Create PDF canvas
        c.setFont("Helvetica", 12)            # Set font
        c.drawString(50, 800, f"PhishGuard AI Report – {datetime.now():%Y-%m-%d %H:%M:%S}")  # Header
        c.drawString(50, 780, self.result_label.text())
        c.drawString(50, 760, self.explain_label.text())
        c.drawString(50, 740, self.threat_label.text())
        c.drawString(50, 720, "Preview:")
        c.drawString(50, 700, text[:300].replace("\n"," "))  # Body preview
        c.save()                              # Save PDF
        QMessageBox.information(self, "Exported", f"Report saved to:\n{path}")

    def clear_inputs(self):                   # Clear all input fields and results
        self.sender_input.clear()
        self.subject_input.clear()
        self.body_input.clear()
        self.result_label.setText("Result: Pending")
        self.risk_level_label.setText("Risk: Unknown")
        self.explain_label.setText("")
        self.threat_label.setText("")
        self.table.clearContents()
        self.chart.ax.clear()
        self.chart.draw()
        if hasattr(self, "last_headers"):
            del self.last_headers         # Remove stored headers if any

    def save_feedback(self, label):           # Save user feedback to JSONL log
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sender": self.sender_input.text().strip(),
            "subject": self.subject_input.text().strip(),
            "body": self.body_input.toPlainText().strip(),
            "prediction": self.result_label.text(),
            "user_label": label
        }
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Feedback Log", "feedback_log.jsonl", "JSONL Files (*.jsonl);;All Files (*)"
        )
        if not path:
            return
        with open(path, "a", encoding="utf-8") as f:  # Append to log file
            f.write(json.dumps(entry) + "\n")
        QMessageBox.information(self, "Saved", f"Feedback saved to:\n{path}")

    def show_feedback_log(self):               # Display saved feedback entries
        try:
            with open("feedback_log.jsonl", "r", encoding="utf-8") as f:
                lines = f.readlines()
        except FileNotFoundError:
            QMessageBox.information(self, "Empty Log", "No feedback entries found.")
            return

        dlg = QDialog(self)                     # Dialog to show history
        dlg.setWindowTitle("Feedback Log Viewer")
        dlg.resize(600, 400)
        view = QListWidget()
        for line in lines:
            try:
                e = json.loads(line.strip())
                view.addItem(f"[{e['timestamp']}] {e['prediction']} → {e['user_label']} | {e['subject']}")
            except:
                continue
        layout = QVBoxLayout()
        layout.addWidget(view)
        dlg.setLayout(layout)
        dlg.exec_()

# === Application Startup ===
if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)            # Create Qt application
        splash_pix = QPixmap(resource_path("logo.png"))  # Load splash image
        splash = QSplashScreen(splash_pix)      # Show splash screen
        splash.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint)
        splash.setMask(splash_pix.mask())
        splash.show()

        anim = QPropertyAnimation(splash, b"windowOpacity")  # Fade-out animation
        anim.setDuration(1500)
        anim.setStartValue(1)
        anim.setEndValue(0)
        anim.setEasingCurve(QEasingCurve.InOutQuad)

        def start_app():                        # After animation, show main window
            splash.close()
            w = MainWindow()
            w.show()

        QTimer.singleShot(2000, anim.start)     # Start fade after 2s
        QTimer.singleShot(2500, start_app)      # Launch main window after 2.5s
        sys.exit(app.exec_())                   # Enter Qt event loop

    except Exception as e:                      # Catch unhandled exceptions
        import traceback
        with open("error_log.txt", "w") as f:
            f.write("Unhandled Exception:\n")
            traceback.print_exc(file=f)        # Save stack trace to file
