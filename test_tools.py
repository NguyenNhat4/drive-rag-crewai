"""
Test script to verify Google Drive tools are working correctly.
"""

from drive_rag.tools import (
    GoogleDriveListTool,
    GoogleDrivePilotFolderTool,
    GoogleDriveDownloadTool
)

def test_tool_initialization():
    """Test that all tools can be initialized"""
    print("Testing tool initialization...")

    try:
        list_tool = GoogleDriveListTool()
        print(f"[OK] GoogleDriveListTool: {list_tool.name}")

        pilot_tool = GoogleDrivePilotFolderTool()
        print(f"[OK] GoogleDrivePilotFolderTool: {pilot_tool.name}")

        download_tool = GoogleDriveDownloadTool()
        print(f"[OK] GoogleDriveDownloadTool: {download_tool.name}")

        print("\n[SUCCESS] All tools initialized successfully!\n")
        return True
    except Exception as e:
        print(f"\n[ERROR] Error initializing tools: {e}\n")
        return False


def test_pilot_folder_tool():
    """Test the pilot folder tool with a real folder ID"""
    print("Testing GoogleDrivePilotFolderTool...")
    print("=" * 60)

    # Use the folder ID from your code
    FOLDER_ID = "1St1U-CjWbHbYOLoZztyCwpxD9Ahn-_uV"

    try:
        tool = GoogleDrivePilotFolderTool()
        result = tool._run(folder_id=FOLDER_ID)

        print(f"Result (first 500 chars):\n{result[:500]}...")
        print("\n[SUCCESS] Pilot folder tool test successful!\n")
        return True
    except FileNotFoundError as e:
        print(f"\n[WARNING] Service account credentials not found:")
        print(f"   {e}")
        print("\nPlease follow these steps:")
        print("1. Create a service account in Google Cloud Console")
        print("2. Download the JSON key file")
        print("3. Rename it to 'service-account.json'")
        print("4. Place it in: src/drive_rag/credentials/service-account.json\n")
        return False
    except Exception as e:
        print(f"\n[ERROR] Error testing pilot folder tool: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("Google Drive Tools Test Suite")
    print("=" * 60)
    print()

    # Test 1: Tool initialization
    if not test_tool_initialization():
        return

    # Test 2: Actual API call (requires credentials)
    print("Testing actual Google Drive API connection...")
    print("This requires service-account.json to be configured.\n")

    test_pilot_folder_tool()

    print("=" * 60)
    print("Testing complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. If credentials are not set up, see SETUP.md")
    print("2. Run 'crewai run' to use the crew")
    print("3. Run 'crewai studio' to use tools in CrewAI Studio")
    print("4. See CREWAI_STUDIO_GUIDE.md for usage examples")


if __name__ == "__main__":
    main()
