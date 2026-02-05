# GitLab Compliance Checker - Complete Technical Documentation

## 📖 COMPREHENSIVE API & FUNCTION REFERENCE

---

## 1️⃣ PYTHON-GITLAB API - DETAILED REFERENCE

### 1.1 Project Object APIs

```python
# Get a project
project = gl.projects.get(project_id_or_path)

# Access project metadata
project.id                          # Project ID (integer)
project.name                        # Project name
project.path_with_namespace         # Full path (group/project)
project.description                 # Project description
project.default_branch              # Default branch name
project.tags.list()                 # Get project tags
```

### 1.2 Repository Tree API

```python
# List files in repository
files = project.repository_tree(ref='main', recursive=True, all=True)

# Output: List of dicts with structure:
[
    {
        'id': '...',
        'name': 'filename.py',
        'type': 'blob',           # or 'tree' for directories
        'path': 'src/filename.py'
    }
]

# Iterate through files
for item in files:
    if item['type'] == 'blob':      # It's a file
        filename = item['name']
        filepath = item['path']
```

### 1.3 File Content API

```python
# Read file content
file = project.files.get(file_path='README.md', ref='main')

# Decode content
content = file.decode().decode('utf-8')

# Returns raw file content as string
```

### 1.4 Branches API

```python
# List all branches
branches = project.branches.list(all=True)

# Returns: List of branch objects
for branch in branches:
    branch_name = branch.name
    commit_id = branch.commit['id']
```

### 1.5 Tags API

```python
# Get tags (with pagination)
tags = project.tags.list(per_page=1)

# Returns: List of tag objects
# Used to check if project has any tags
has_tags = len(tags) > 0
```

### 1.6 User API (GitLab Client)

```python
# Get user by username
user = client.users.get_by_username('john_doe')

# Get user by ID
user = client.users.get_by_userid(123)

# User object contains:
user['id']           # User ID
user['name']         # Display name
user['username']     # Username
user['avatar_url']   # Profile picture URL
user['web_url']      # Profile page URL
```

---

## 2️⃣ STREAMLIT FRAMEWORK - COMPLETE REFERENCE

### 2.1 Page Configuration & Layout

```python
st.set_page_config(page_title="My App", layout="wide")

st.title("Main Title")                    # Large title
st.header("Header")                       # Section header
st.subheader("Subheader")                 # Subsection header
st.markdown("# Markdown formatted text")  # Rich text

st.divider()                              # Visual separator
```

### 2.2 Sidebar Components

```python
mode = st.sidebar.radio("Select Mode", ["Option A", "Option B"])

st.sidebar.warning("⚠️ Warning message")
st.sidebar.success("✅ Success message")

if st.sidebar.button("Click me"):
    st.write("Button was clicked!")
```

### 2.3 User Input Components

```python
# Text input
project_path = st.text_input("Enter project path")

# Text area (multiline)
code = st.text_area("Enter code", height=300)

# Dropdown selection
branch = st.selectbox("Select branch", ["main", "develop", "staging"])

# Checkbox
agree = st.checkbox("I agree to terms")

# Button
if st.button("Submit"):
    st.write("Processing...")
```

### 2.4 Data Display Components

```python
# Display text
st.write("Simple text")
st.text("Monospace text")

# Display code
st.code("python code", language="python")

# Display dataframe
st.dataframe(df, use_container_width=True)

# Display table
st.table(data)

# Metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Label", 42, "+10%")
```

### 2.5 Status & Messages

```python
st.success("✅ Operation completed!")
st.error("❌ Error occurred!")
st.warning("⚠️ Warning!")
st.info("ℹ️ Information")
```

### 2.6 Layout Components

```python
# Two columns
col1, col2 = st.columns(2)
with col1:
    st.write("Column 1")
with col2:
    st.write("Column 2")

# Expander (collapsible)
with st.expander("Click to expand"):
    st.write("Hidden content")

# Container
with st.container():
    st.write("Grouped content")

# Tabs
tab1, tab2 = st.tabs(["Tab 1", "Tab 2"])
with tab1:
    st.write("Content 1")
with tab2:
    st.write("Content 2")
```

### 2.7 Advanced Features

```python
# Caching (avoid recomputation)
@st.cache_data(ttl=60)
def expensive_function():
    return compute_something()

# Session state (persist across reruns)
st.session_state.count = st.session_state.get('count', 0) + 1

# Progress tracking
progress_bar = st.progress(0)
for i in range(100):
    progress_bar.progress(i + 1)

# Spinner (loading indicator)
with st.spinner('Loading...'):
    time.sleep(2)
```

### 2.8 File Operations

```python
# File upload
uploaded_file = st.file_uploader("Choose file")

# File download
st.download_button(
    label="Download file",
    data=file_bytes,
    file_name="report.xlsx",
    mime="application/octet-stream"
)
```

### 2.9 Custom HTML & CSS

```python
# Render HTML
st.markdown("""
    <div style="background-color: #f0f2f6; padding: 20px;">
        <h2 style="color: #1f77b4;">Custom HTML</h2>
    </div>
""", unsafe_allow_html=True)

# Progress bar with custom styling
progress_html = f"""
<div style="width: 100%; height: 20px; background-color: #e0e0e0; border-radius: 5px;">
    <div style="width: {score}%; height: 100%; background-color: #4caf50;"></div>
</div>
"""
st.markdown(progress_html, unsafe_allow_html=True)
```

---

## 3️⃣ CORE FUNCTIONS - DETAILED DOCUMENTATION

### 3.1 File Reading Functions

#### `read_file_content(project, file_path, ref)`

```python
@st.cache_data(ttl=60)
def read_file_content(_project, file_path, ref):
    """
    Read file content from repository with 60-second caching.

    Args:
        _project: GitLab project object (underscore = excluded from hash)
        file_path: Path to file (e.g., 'README.md')
        ref: Branch/tag reference (default: 'main')

    Returns:
        str: File content as UTF-8 string, or None if not found

    Example:
        content = read_file_content(project, 'README.md', 'main')
        if content:
            print(content)
    """
    try:
        file = _project.files.get(file_path=file_path, ref=ref)
        return file.decode().decode("utf-8")
    except Exception:
        return None
```

### 3.2 Network & Retry Functions

#### `get_project_with_retries(gl_client, path_or_id, retries=3, backoff=1)`

```python
def get_project_with_retries(gl_client, path_or_id, retries=3, backoff=1):
    """
    Fetch project from GitLab with automatic retry on network errors.

    Args:
        gl_client: GitLab client instance
        path_or_id: Project path (e.g., 'group/project') or numeric ID
        retries: Maximum retry attempts (default: 3)
        backoff: Base backoff multiplier (default: 1)

    Returns:
        Project object on success

    Raises:
        GitlabGetError: If project not found (404) or after max retries

    Behavior:
        - Retry on: ConnectionResetError, RequestException, RemoteDisconnected
        - No retry on: 404 (project not found)
        - Backoff: exponential (1s, 2s, 4s)

    Example:
        try:
            project = get_project_with_retries(gl, 'tools/compliance-checker')
            print(f"Found: {project.name}")
        except Exception as e:
            print(f"Error: {e}")
    """
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            return gl_client.projects.get(
                int(path_or_id) if str(path_or_id).isdigit() else path_or_id
            )
        except GitlabGetError as e:
            last_exc = e
            if getattr(e, "response", None) is not None and e.response.status_code == 404:
                raise  # Re-raise 404 immediately
            if attempt == retries:
                raise
        except (ConnectionResetError, ConnectionAbortedError,
                requests.exceptions.RequestException, OSError,
                http.client.RemoteDisconnected) as e:
            last_exc = e
            if attempt == retries:
                raise
            sleep_for = backoff * (2 ** (attempt - 1))
            time.sleep(sleep_for)

    if last_exc:
        raise last_exc
```

### 3.3 Compliance Check Functions

#### `check_project_compliance(project, branch=None)`

```python
def check_project_compliance(project, branch=None):
    """
    Main compliance check orchestrator function.

    Performs all compliance checks on a project:
    - README existence and quality score
    - Required files (CONTRIBUTING, CHANGELOG, LICENSE)
    - License type validation (AGPLv3)
    - Configuration files (.gitignore, pyproject.toml, uv.lock)
    - VSCode configuration
    - Issue and MR templates
    - Project metadata

    Args:
        project: GitLab project object
        branch: Repository branch to check (default: project's default_branch)

    Returns:
        dict: Comprehensive compliance report with keys:
            - 'README.md': bool
            - 'CONTRIBUTING.md': bool
            - 'CHANGELOG': bool
            - 'LICENSE': bool
            - 'license_valid': bool (is AGPLv3)
            - 'license_status': str ('valid', 'gnu_other', 'invalid')
            - 'readme_status': str ('present', 'empty', 'missing')
            - 'readme_quality_score': int (0-100)
            - 'readme_sections': list
            - '.gitignore': bool
            - 'pyproject.toml': bool
            - 'uv_lock_exists': bool
            - 'vscode_settings': bool
            - 'vscode_ruff_in_extensions': bool
            - 'issue_templates_folder': bool
            - 'merge_request_templates_folder': bool
            - ... and more
    """
    # Implementation calls all check functions
    # Returns comprehensive report dictionary
```

### 3.4 Language Detection Functions

#### `classify_repository_files(file_paths)`

```python
def classify_repository_files(file_paths):
    """
    Classify files into categories and detect programming languages.

    Args:
        file_paths: List of file paths from repository

    Returns:
        dict with keys:
            - 'python_files': list of .py files
            - 'js_files': list of JavaScript/TypeScript files
            - 'java_files': list of .java files
            - 'go_files': list of .go files
            - 'rust_files': list of .rs files
            - 'csharp_files': list of .cs/.csproj files
            - 'detected_languages': ['Python', 'Java', 'Go', ...]
            - 'common_requirements': [requirements.txt, package.json, ...]
            - 'project_files': [README.md, CONTRIBUTING.md, ...]
            - 'tech_files': [Dockerfile, .gitlab-ci.yml, ...]

    Example:
        files = ['app.py', 'main.java', 'src/main.go', 'README.md']
        result = classify_repository_files(files)
        print(result['detected_languages'])  # ['Go', 'Java', 'Python']
    """
    res = {
        "detected_languages": [],
        "python_files": [],
        "js_files": [],
        "java_files": [],
        "go_files": [],
        "rust_files": [],
        "csharp_files": [],
        # ... more categories
    }

    # Loop through files and match extensions
    for file_path in file_paths:
        if file_path.lower().endswith(".py"):
            res["python_files"].append(file_path)
            if "Python" not in res["detected_languages"]:
                res["detected_languages"].append("Python")
        # ... similar for other languages

    return res
```

### 3.5 README Quality Scoring

#### `calculate_readme_quality_score(content)`

```python
def calculate_readme_quality_score(content):
    """
    Calculate README quality score (0-100) using multi-criteria analysis.

    Scoring Breakdown (100 points max):

    Content Length (15 pts):
        - >500 chars: 15 pts
        - >300 chars: 10 pts
        - >100 chars: 5 pts

    Essential Sections (60 pts):
        - Installation: 10 pts
        - Usage: 10 pts
        - Getting Started: 10 pts
        - Setup: 5 pts
        - Features: 10 pts
        - Contributing: 5 pts
        - License: 10 pts

    Code Examples (10 pts):
        - Has code blocks (```): 10 pts
        - Has inline code (`): 5 pts

    Links/References (5 pts):
        - Contains URLs or markdown links

    Structure (10 pts):
        - ≥5 headings: 10 pts
        - ≥3 headings: 5 pts

    Args:
        content: README file content as string

    Returns:
        int: Score 0-100 (capped at 100)

    Example:
        readme = "# Project\n## Installation\npip install...\n## Usage\n..."
        score = calculate_readme_quality_score(readme)
        print(f"Score: {score}/100")  # Score: 50/100
    """
    if not content or not content.strip():
        return 0

    score = 0

    # Content length check
    if len(content.strip()) > 500:
        score += 15
    # ... more scoring logic

    return min(score, 100)
```

#### `render_readme_quality_progress_bar(score)`

```python
def render_readme_quality_progress_bar(score):
    """
    Render HTML progress bar for README quality score in Streamlit.

    Color Coding:
    - 85-100 (Excellent): Green (#00d084)
    - 70-84 (Good): Yellow-Green (#a3e635)
    - 50-69 (Fair): Amber (#fbbf24)
    - 25-49 (Poor): Orange (#f97316)
    - 0-24 (Very Poor): Red (#ef4444)

    Args:
        score: Score value 0-100

    Returns:
        None (renders HTML directly in Streamlit)

    Example:
        score = 75
        render_readme_quality_progress_bar(score)
        # Displays: [████████████░░░░░░░░░░░░░░]
    """
    # Determine color based on score
    if score >= 85:
        color = "#00d084"
        label = "Excellent"
    # ... more color logic

    # Generate HTML
    progress_html = f"""
    <div style="margin: 10px 0;">
        <div style="display: flex; justify-content: space-between;">
            <span>README Quality Score</span>
            <span>{score}/100 ({label})</span>
        </div>
        <div style="width: 100%; height: 25px; background-color: #e5e7eb;">
            <div style="width: {score}%; height: 100%; background-color: {color};"></div>
        </div>
    </div>
    """
    st.markdown(progress_html, unsafe_allow_html=True)
```

### 3.6 License Validation

#### `check_license_content(project, branch='main')`

```python
def check_license_content(project, branch="main"):
    """
    Validate license type using official headers and dates.

    Supported Licenses:
    - "valid": AGPLv3 (exact match with official date: Nov 19, 2007)
    - "gnu_other": GPLv3, LGPLv3, or other GNU licenses
    - "invalid": MIT, Apache, or other non-GNU licenses

    Args:
        project: GitLab project object
        branch: Repository branch

    Returns:
        str: One of 'valid', 'gnu_other', 'invalid', 'not_found'

    Validation Logic:
    1. Reads LICENSE or LICENSE.md
    2. Checks for AGPLv3 markers:
        - Contains "affero"
        - Contains "general public license"
        - Contains "version 3"
        - Contains exact date "19 november 2007"
    3. If all match → "valid" (AGPLv3)
    4. Else if contains other GNU licenses → "gnu_other"
    5. Else → "invalid"
    """
    # Implementation checks license markers
    pass
```

### 3.7 Export Functions

#### `reports_to_csv(rows)`

```python
def reports_to_csv(rows):
    """
    Convert compliance report rows to CSV format.

    Args:
        rows: List of report dictionaries

    Returns:
        str: CSV-formatted string (semicolon separated)

    CSV Columns:
        project_id, path, branch, python_count, js_count,
        common_requirements, project_files, tech_files,
        license_status, license_valid, readme_status, readme_notes

    Example:
        rows = [
            {
                'project_id': 1,
                'path': 'group/project',
                'python_count': 5,
                ...
            }
        ]
        csv_content = reports_to_csv(rows)
        # Returns CSV string ready to download
    """
    pass
```

#### `reports_to_excel(rows)`

```python
def reports_to_excel(rows):
    """
    Convert compliance report rows to Excel format.

    Args:
        rows: List of report dictionaries

    Returns:
        bytes: Excel file content (XLSX format)

    Features:
        - Uses pandas for data manipulation
        - Creates single sheet named 'Report'
        - Tries openpyxl engine first, falls back to xlsxwriter
        - Professional formatting and layout

    Raises:
        RuntimeError: If pandas or Excel engine not available

    Example:
        rows = [report1, report2, ...]
        excel_bytes = reports_to_excel(rows)
        st.download_button(
            "Download",
            data=excel_bytes,
            file_name="report.xlsx"
        )
    """
    pass
```

---

## 4️⃣ WORKFLOW DIAGRAMS

### 4.1 Single Project Analysis Flow

```
User Input (project path)
       ↓
extract_path_from_url() → Normalize path
       ↓
get_project_with_retries() → Fetch from GitLab (with retry)
       ↓
get_project_branches() → Get available branches
       ↓
User selects branch
       ↓
check_project_compliance() → Run all checks
       ├→ read_file_content(README.md)
       │  ├→ calculate_readme_quality_score() → 0-100
       │  └→ Store score in report
       ├→ check_license_content() → valid/gnu_other/invalid
       ├→ check_vscode_settings() → Check .vscode files
       ├→ check_templates_presence() → Check templates
       └→ Store all results in report dict
       ↓
list_all_files() → Get all repository files
       ↓
classify_repository_files() → Detect languages
       ├→ Add python_files: [...]
       ├→ Add java_files: [...]
       ├→ Add detected_languages: ['Python', 'Java', ...]
       └→ Add file counts
       ↓
Combine report + classification
       ↓
render_project_compliance_ui() → Display results
       ├→ Show ✅/❌ for each check
       ├→ render_readme_quality_progress_bar() → Visual bar
       ├→ Display detected languages
       ├→ Show file counts
       └→ get_suggestions_for_missing_items() → Suggestions
       ↓
User can download report
       ├→ reports_to_excel() → Excel
       └→ reports_to_csv() → CSV
```

### 4.2 Batch Analysis Flow

```
User enables batch mode
       ↓
User enters 10 project paths
       ↓
FOR EACH project:
    ├→ get_project_with_retries()
    ├→ check_project_compliance()
    ├→ classify_repository_files()
    └→ Append to results list
       ↓
Aggregate all results
       ↓
Display summary table
       ├→ Project ID, Path, Branch
       ├→ File counts (Python, Java, etc.)
       ├→ License status
       ├→ README quality
       └→ Language detection
       ↓
Show detailed reports per project
       ├→ Expandable sections
       └→ Individual compliance UI
       ↓
Generate reports
       ├→ reports_to_excel() → Complete spreadsheet
       └→ reports_to_csv() → CSV with all data
       ↓
User downloads report
```

---

## 5️⃣ API RESPONSE EXAMPLES

### 5.1 Compliance Report Object

```python
{
    # File existence checks
    "README.md": True,
    "CONTRIBUTING.md": True,
    "CHANGELOG": True,
    "LICENSE": True,

    # License validation
    "license_status": "valid",           # 'valid', 'gnu_other', 'invalid'
    "license_valid": True,

    # README analysis
    "readme_status": "present",          # 'present', 'empty', 'missing'
    "readme_quality_score": 85,          # 0-100
    "readme_sections": ["installation", "usage", "contributing", "license"],
    "readme_needs_improvement": False,

    # Configuration files
    ".gitignore": True,
    "pyproject.toml": True,
    "uv_lock_exists": True,

    # VSCode configuration
    "vscode_settings": True,
    "vscode_ruff_in_extensions": True,
    "vscode_extensions_exists": True,
    "vscode_launch_exists": True,
    "vscode_tasks_exists": True,

    # Templates
    "issue_templates_folder": True,
    "issue_template_files": ["Bug.md", "Feature.md", "Default.md"],
    "merge_request_templates_folder": True,
    "merge_request_template_files": ["Bug.md", "Default.md"],

    # Metadata
    "description_present": True,
    "tags_present": True,

    # Language detection
    "python_count": 5,
    "js_count": 0,
    "java_count": 0,
    "go_count": 0,
    "rust_count": 0,
    "csharp_count": 0,
    "detected_languages_list": ["Python"],

    # File classifications
    "common_requirements_list": ["requirements.txt", "pyproject.toml"],
    "project_files_list": ["README.md", "CONTRIBUTING.md", "src/", "tests/"],
    "tech_files_list": [".gitignore", ".vscode/settings.json", "Dockerfile"]
}
```

### 5.2 Classification Object

```python
{
    "detected_languages": ["Python", "JavaScript/TypeScript", "Java"],
    "python_files": [
        "app.py",
        "src/main.py",
        "tests/test_compliance.py"
    ],
    "js_files": [
        "server.js",
        "src/components.tsx"
    ],
    "java_files": [
        "src/Main.java"
    ],
    "go_files": [],
    "rust_files": [],
    "csharp_files": [],
    "common_requirements": [
        "requirements.txt",
        "package.json",
        "pyproject.toml"
    ],
    "project_files": [
        "README.md",
        "CONTRIBUTING.md",
        "docs/setup.md"
    ],
    "tech_files": [
        ".gitignore",
        "Dockerfile",
        ".vscode/settings.json"
    ]
}
```

---

## 6️⃣ ERROR HANDLING PATTERNS

### 6.1 Network Error Handling

```python
# Caught errors (with retry)
- ConnectionResetError
- ConnectionAbortedError
- requests.exceptions.RequestException
- OSError
- http.client.RemoteDisconnected

# Not retried (immediate failure)
- GitlabGetError (404 - project not found)
- Timeout errors after max retries
```

### 6.2 File Read Errors

```python
try:
    file = project.files.get(file_path=file_path, ref=ref)
    return file.decode().decode("utf-8")
except Exception:
    return None  # Returns None if file not found
```

### 6.3 API Validation

```python
# Check if user found
if not user_info:
    st.error("User not found or error via client")
    st.stop()

# Check if project accessible
if error in report:
    st.error(report["error"])
    st.stop()
```

---

## 7️⃣ PERFORMANCE OPTIMIZATION

### 7.1 Caching

```python
# Cache with 60-second TTL
@st.cache_data(ttl=60)
def read_file_content(_project, file_path, ref):
    # This function result is cached
    pass

# Benefits:
# - Reduces API calls
# - Faster subsequent runs
# - Less strain on GitLab API
# - Improves user experience
```

### 7.2 Session State

```python
# Use session state to avoid recomputation
if st.session_state.get("project_compliance_run"):
    # Already computed, use cached result
    st.session_state["project_compliance_run"] = False
    # Process results
```

### 7.3 Batch Processing

```python
# Process multiple projects sequentially
for line in lines:
    try:
        proj = get_project_with_retries(gl, line)
        # Process project
    except Exception as e:
        # Log error and continue
        rows.append(error_row)
        continue
```

---

## 8️⃣ SECURITY CONSIDERATIONS

### 8.1 Token Management

```python
# Priority order for getting token:
TOKEN = st.secrets.get("GITLAB_TOKEN") or os.getenv("GITLAB_TOKEN")
URL = st.secrets.get("GITLAB_URL") or os.getenv("GITLAB_URL")

# Never hardcode tokens
# Use .streamlit/secrets.toml or environment variables
# Keep .streamlit/secrets.toml in .gitignore
```

### 8.2 API Scope

```python
# Personal access token should have:
- read_api scope (for reading project/user data)
- NOT write access (unless needed)
- NOT admin access (unless needed)
```

### 8.3 Input Validation

```python
# Validate user input
def extract_path_from_url(input_str):
    try:
        path = urlparse(input_str).path.strip("/")
        return path[:-4] if path.endswith(".git") else path
    except Exception:
        return input_str.strip()  # Return as-is if parsing fails
```

---

## 🎓 LEARNING RESOURCES

- **Python-GitLab Documentation:** https://python-gitlab.readthedocs.io/
- **Streamlit Documentation:** https://docs.streamlit.io/
- **GitLab API Reference:** https://docs.gitlab.com/ee/api/
- **ReportLab Documentation:** https://www.reportlab.com/docs/

---

## 📝 COMMON USE CASES

### Use Case 1: Check Project Before Release
```python
1. Run single project analysis
2. Check README quality score (target: 80+)
3. Verify all compliance items are ✅
4. Fix any ❌ items
5. Re-run to confirm all fixed
6. Generate Excel report for stakeholders
```

### Use Case 2: Audit Multiple Projects
```python
1. Export project list from GitLab
2. Paste into batch mode
3. Run batch analysis
4. Review summary table
5. Download Excel report
6. Present results to management
```

### Use Case 3: CI/CD Integration
```python
# Could be called from GitLab CI/CD:
python generate_compliance_report.py
# Returns JSON or CSV that CI/CD can parse
# Fail job if compliance score < threshold
```

---

**Generated:** February 5, 2026
**Version:** 1.0.0
**Status:** Complete & Production Ready ✅
