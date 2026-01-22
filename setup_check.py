"""Check if Threads Scraper is set up correctly."""

import sys
import importlib.util


def check_python_version():
    """Check Python version."""
    version = sys.version_info
    if version < (3, 8):
        print(f"❌ Python {version.major}.{version.minor} detected. Python 3.8+ required.")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_package(package_name, import_name=None):
    """Check if a package is installed."""
    if import_name is None:
        import_name = package_name

    try:
        spec = importlib.util.find_spec(import_name)
        if spec is not None:
            print(f"✓ {package_name}")
            return True
        else:
            print(f"❌ {package_name} not found")
            return False
    except (ImportError, ModuleNotFoundError):
        print(f"❌ {package_name} not found")
        return False


def check_project_structure():
    """Check if project files exist."""
    import os
    required_files = [
        'src/main.py',
        'src/scraper/threads_scraper.py',
        'src/parsers/post_parser.py',
        'src/exporters/markdown_exporter.py',
        'requirements.txt',
        'README.md'
    ]

    all_exist = True
    for filepath in required_files:
        if os.path.exists(filepath):
            print(f"✓ {filepath}")
        else:
            print(f"❌ {filepath} missing")
            all_exist = False

    return all_exist


def main():
    """Run all checks."""
    print("\n" + "="*60)
    print("THREADS SCRAPER SETUP CHECK")
    print("="*60 + "\n")

    all_ok = True

    # Check Python version
    print("Checking Python version...")
    if not check_python_version():
        all_ok = False
    print()

    # Check required packages
    print("Checking required packages...")
    packages = [
        ('playwright', 'playwright'),
        ('python-dotenv', 'dotenv'),
        ('python-dateutil', 'dateutil'),
        ('colorlog', 'colorlog'),
        ('pytest', 'pytest'),
        ('pytest-asyncio', 'pytest_asyncio')
    ]

    for package_name, import_name in packages:
        if not check_package(package_name, import_name):
            all_ok = False
    print()

    # Check project structure
    print("Checking project structure...")
    if not check_project_structure():
        all_ok = False
    print()

    # Final result
    print("="*60)
    if all_ok:
        print("✓ ALL CHECKS PASSED")
        print("\nYou're ready to use the Threads Scraper!")
        print("\nNext steps:")
        print("1. Run: python -m src.main <username>")
        print("2. Complete manual login on first run")
        print("3. Check the 'output' folder for generated markdown")
    else:
        print("❌ SOME CHECKS FAILED")
        print("\nPlease fix the issues above.")
        print("\nTo install missing packages:")
        print("  pip install -r requirements.txt")
        print("\nTo install Playwright browsers:")
        print("  playwright install chromium")

    print("="*60 + "\n")

    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())
