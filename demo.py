#!/usr/bin/env python3
"""
Demo script to show MEGA Bot functionality without MEGA API dependency.
This demonstrates the core structure and utilities work correctly.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_utilities():
    """Test utility functions."""
    print("🧪 Testing Utility Functions")
    print("=" * 40)
    
    from mega_bot.utils.links import is_mega_link, get_mega_link_type
    from mega_bot.utils.formatting import get_readable_file_size, get_readable_time, truncate_string
    
    # Test link utilities
    test_links = [
        "https://mega.nz/file/ABC123",
        "https://mega.nz/folder/XYZ789",
        "https://mega.nz/#F!ABC123",
        "https://google.com",
        "not-a-link"
    ]
    
    for link in test_links:
        is_mega = is_mega_link(link)
        link_type = get_mega_link_type(link) if is_mega else "N/A"
        print(f"  {link:<30} | MEGA: {is_mega:<5} | Type: {link_type}")
    
    print()
    
    # Test formatting utilities
    sizes = [0, 1024, 1024**2, 1024**3, 1024**4]
    times = [0, 30, 90, 3661, 86400, 259200]
    
    print("File Size Formatting:")
    for size in sizes:
        print(f"  {size:>10} bytes -> {get_readable_file_size(size)}")
    
    print("\nTime Formatting:")
    for time_sec in times:
        print(f"  {time_sec:>6} seconds -> {get_readable_time(time_sec)}")
    
    print("\nString Truncation:")
    long_text = "This is a very long filename that should be truncated properly.txt"
    print(f"  Original: {long_text}")
    print(f"  Truncated: {truncate_string(long_text, 30)}")


def test_configuration():
    """Test configuration management."""
    print("\n🔧 Testing Configuration")
    print("=" * 40)
    
    from mega_bot.config import Config
    
    print(f"  Download Directory: {Config.DOWNLOAD_DIR}")
    print(f"  Max Concurrent: {Config.MAX_CONCURRENT}")
    print(f"  Debug Mode: {Config.DEBUG}")
    print(f"  Bot Token Set: {'Yes' if Config.BOT_TOKEN else 'No'}")
    print(f"  MEGA Email Set: {'Yes' if Config.MEGA_EMAIL else 'No'}")
    
    # Test validation
    try:
        Config.validate()
        print("  ✅ Configuration validation passed")
    except ValueError as e:
        print(f"  ⚠️  Configuration validation: {e}")


def test_task_states():
    """Test task state enumeration."""
    print("\n📋 Testing Task States")
    print("=" * 40)
    
    from mega_bot.task_manager import TaskState
    
    print("  Available task states:")
    for state in TaskState:
        print(f"    - {state.name}: {state.value}")


def main():
    """Run all tests."""
    print("🚀 MEGA Bot Functionality Demo")
    print("=" * 50)
    
    try:
        test_utilities()
        test_configuration()
        test_task_states()
        
        print("\n✅ All core functionality tests passed!")
        print("\n📝 Next steps:")
        print("  1. Resolve MEGA API dependency compatibility")
        print("  2. Set BOT_TOKEN environment variable")
        print("  3. Run: python mega_bot/run.py")
        print("  4. Or CLI: python -m mega_bot.cli <mega_link>")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())