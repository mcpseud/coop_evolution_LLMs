#!/usr/bin/env python3
"""
Setup utility for LLM Game Theory Simulation System
Helps create initial configuration files and verify setup
"""

import os
import sys
from pathlib import Path
from config_loader import ConfigLoader


def create_directories():
    """Create necessary directories for the simulation"""
    directories = ['output', 'configs', 'results']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}/")


def create_example_files():
    """Create example configuration files"""
    config_loader = ConfigLoader()
    
    # Create agent configuration template
    agents_file = Path('configs/agents_template.csv')
    config_loader.save_agent_template(agents_file)
    print(f"✓ Created agent template: {agents_file}")
    
    # Create experiment configuration template  
    experiment_file = Path('configs/experiment_template.csv')
    config_loader.save_experiment_template(experiment_file)
    print(f"✓ Created experiment template: {experiment_file}")


def check_dependencies():
    """Check if required dependencies are installed"""
    print("\nChecking dependencies...")
    
    dependencies = {
        'openai': 'OpenAI API library',
        'numpy': 'NumPy for random distributions'
    }
    
    missing = []
    
    for module, description in dependencies.items():
        try:
            __import__(module)
            print(f"✓ {description} ({module}) is installed")
        except ImportError:
            print(f"✗ {description} ({module}) is NOT installed")
            missing.append(module)
    
    if missing:
        print(f"\nPlease install missing dependencies:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    return True


def check_api_key():
    """Check if OpenAI API key is configured"""
    print("\nChecking OpenAI API key...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    
    if api_key:
        print("✓ OpenAI API key found in environment")
        print(f"  Key starts with: {api_key[:8]}...")
    else:
        print("✗ OpenAI API key NOT found")
        print("  Set it with: export OPENAI_API_KEY='your-key-here'")
        print("  Or pass it with: --api-key parameter when running")
        return False
    
    return True


def verify_files():
    """Verify all required Python files are present"""
    print("\nChecking required files...")
    
    required_files = [
        'game_theory_main.py',
        'simulation_engine.py',
        'agent_class.py',
        'game_manager.py',
        'scenarios_manager.py',
        'config_loader.py',
        'data_logger.py'
    ]
    
    missing = []
    
    for file in required_files:
        if Path(file).exists():
            print(f"✓ Found {file}")
        else:
            print(f"✗ Missing {file}")
            missing.append(file)
    
    if missing:
        print(f"\nPlease ensure all files are in the current directory")
        return False
    
    return True


def print_quick_start():
    """Print quick start instructions"""
    print("\n" + "="*60)
    print("QUICK START GUIDE")
    print("="*60)
    
    print("\n1. Edit configuration files:")
    print("   - configs/agents_template.csv (define agent strategies)")
    print("   - configs/experiment_template.csv (set experiment parameters)")
    
    print("\n2. Run a simulation:")
    print("   python main.py --agents configs/agents_template.csv \\")
    print("                  --config configs/experiment_template.csv \\")
    print("                  --output results/my_experiment/")
    
    print("\n3. For testing without API calls:")
    print("   python main.py --agents configs/agents_template.csv \\")
    print("                  --config configs/experiment_template.csv \\")
    print("                  --output results/test/ --dry-run")
    
    print("\n4. View results in the output directory")
    print("\nFor detailed instructions, see README.md")
    print("="*60)


def main():
    """Main setup routine"""
    print("LLM Game Theory Simulation System - Setup")
    print("="*60)
    
    # Create directories
    print("\nCreating directories...")
    create_directories()
    
    # Check files
    if not verify_files():
        print("\n⚠️  Some files are missing. Please ensure all files are downloaded.")
        sys.exit(1)
    
    # Create example configurations
    print("\nCreating example configuration files...")
    create_example_files()
    
    # Check dependencies
    if not check_dependencies():
        print("\n⚠️  Please install missing dependencies before running simulations.")
    
    # Check API key
    check_api_key()
    
    # Print quick start guide
    print_quick_start()
    
    print("\n✓ Setup complete! You're ready to run simulations.")


if __name__ == "__main__":
    main()
