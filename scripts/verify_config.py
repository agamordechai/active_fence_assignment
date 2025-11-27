#!/usr/bin/env python3
"""
Quick verification script to test that LOG_LEVEL and RUN_MODE are working.
Run this to verify the configuration system is properly installed.
"""
import sys

print("\n" + "=" * 80)
print("🔍 Configuration System Verification")
print("=" * 80)

try:
    # Test 1: Import config module
    print("\n[1/4] Testing config module import...")
    from src.config import Config, setup_logging
    print("      ✅ Config module imported successfully")

    # Test 2: Check LOG_LEVEL
    print(f"\n[2/4] Testing LOG_LEVEL...")
    print(f"      Current value: {Config.LOG_LEVEL}")
    print(f"      Numeric value: {Config.get_log_level()}")
    if Config.LOG_LEVEL in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        print(f"      ✅ Valid LOG_LEVEL")
    else:
        print(f"      ❌ Invalid LOG_LEVEL (should be DEBUG/INFO/WARNING/ERROR/CRITICAL)")
        sys.exit(1)

    # Test 3: Check RUN_MODE
    print(f"\n[3/4] Testing RUN_MODE...")
    print(f"      Current value: {Config.RUN_MODE}")
    if Config.RUN_MODE in ['single', 'scheduler', 'continuous']:
        print(f"      ✅ Valid RUN_MODE")
    else:
        print(f"      ❌ Invalid RUN_MODE (should be single/scheduler/continuous)")
        sys.exit(1)

    # Test 4: Test logging setup
    print(f"\n[4/4] Testing logging setup...")
    logger = setup_logging()
    logger.info("Test INFO message")
    print(f"      ✅ Logging configured successfully")

    # Success!
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print("\n📋 Current Configuration:")
    Config.print_config()

    print("\n💡 Tips:")
    print("   • Change LOG_LEVEL in .env to control verbosity")
    print("   • Change RUN_MODE to control execution (single/scheduler/continuous)")
    print("   • Run 'python -m src.main' to start the application")
    print("\n" + "=" * 80 + "\n")

except ImportError as e:
    print(f"\n❌ Error importing config module: {e}")
    print("\nMake sure you're running from the project root directory:")
    print("  cd /path/to/active_fence_assignment")
    print("  python verify_config.py")
    sys.exit(1)

except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

