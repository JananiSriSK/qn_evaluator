# Environment Setup Instructions

## Python Version Requirement

**Python 3.10 is required** for this academic project due to:
- ML library compatibility: PyTorch, Transformers, and FAISS have stable Windows support on Python 3.10
- Academic reproducibility: Python 3.10 ensures consistent behavior across evaluation environments
- Dependency stability: Avoids version conflicts common with newer Python versions

## Setup Commands

### 1. Create Python 3.10 Virtual Environment
```bash
# Ensure Python 3.10 is installed
python3.10 -m venv venv

# Or if python3.10 is your default python:
python -m venv venv
```

### 2. Activate Virtual Environment
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Verify Installation
```bash
python -c "import torch, transformers, sentence_transformers, faiss; print('All dependencies installed successfully')"
```

### 5. Run Application
```bash
python main.py
```

## Troubleshooting

If installation fails:
1. Ensure Python 3.10 is being used: `python --version`
2. Clear pip cache: `pip cache purge`
3. Install dependencies one by one to identify conflicts

## Academic Note

This setup uses stable, production-ready versions suitable for academic evaluation and ensures reproducible results across different systems.