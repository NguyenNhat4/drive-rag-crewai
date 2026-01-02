from crewai.tools import BaseTool
from typing import Type, Optional, List
from pydantic import BaseModel, Field
from .google_drive_list_tool import (
    list_google_drive_files,
    get_pilot_folder_files,
    download_file_content
)
import json


class GoogleDriveListInput(BaseModel):
    """Input schema for GoogleDriveListTool."""
    folder_id: Optional[str] = Field(
        default=None,
        description="Google Drive folder ID to search in. Leave empty to search all accessible files."
    )
    mime_types: Optional[List[str]] = Field(
        default=None,
        description="List of MIME types to filter (e.g., ['application/pdf', 'application/vnd.google-apps.document'])"
    )
    max_results: Optional[int] = Field(
        default=100,
        description="Maximum number of files to return. Default is 100."
    )


class GoogleDriveListTool(BaseTool):
    name: str = "Google Drive File Lister"
    description: str = (
        "Lists files from Google Drive with comprehensive metadata including "
        "file names, IDs, web view links, download links, MIME types, sizes, "
        "creation/modification dates, owner information, and permissions. "
        "Useful for discovering and accessing files in Google Drive folders. "
        "Can filter by folder ID and MIME types."
    )
    args_schema: Type[BaseModel] = GoogleDriveListInput

    def _run(
        self,
        folder_id: Optional[str] = None,
        mime_types: Optional[List[str]] = None,
        max_results: Optional[int] = 100
    ) -> str:
        """
        Execute the Google Drive file listing.

        Returns:
            JSON string with list of files and their metadata
        """
        try:
            files = list_google_drive_files(
                folder_id=folder_id,
                mime_types=mime_types,
                include_trashed=False,
                max_results=max_results
            )

            # Format output for better readability
            result = {
                "total_files": len(files),
                "files": [
                    {
                        "filename": f["filename"],
                        "file_id": f["file_id"],
                        "mime_type": f["mime_type"],
                        "web_view_link": f["web_view_link"],
                        "download_link": f.get("download_link"),
                        "size_bytes": f.get("file_size_bytes"),
                        "created_time": f["created_time"],
                        "modified_time": f["modified_time"],
                        "owner_email": f.get("owner_email"),
                        "shared": f.get("shared", False),
                        "parent_folder": f.get("parent_folder_name", "Root"),
                    }
                    for f in files
                ]
            }

            return json.dumps(result, indent=2, ensure_ascii=False)

        except Exception as e:
            return json.dumps({
                "error": str(e),
                "message": "Failed to list Google Drive files. Make sure service account credentials are configured."
            }, indent=2)


class GoogleDrivePilotFolderInput(BaseModel):
    """Input schema for GoogleDrivePilotFolderTool."""
    folder_id: str = Field(
        ...,
        description="Google Drive folder ID to retrieve files from (e.g., '1vx3kBsi64do_BZPiGwM0G_0fCqZtkgrY')"
    )


class GoogleDrivePilotFolderTool(BaseTool):
    name: str = "Google Drive Pilot Folder Scanner"
    description: str = (
        "Retrieves all common document files (PDFs, Google Docs, Word, Excel) "
        "from a specific Google Drive folder. Returns comprehensive metadata "
        "including file names, IDs, links, sizes, and permissions. "
        "Useful for scanning specific project folders or QMS document repositories."
    )
    args_schema: Type[BaseModel] = GoogleDrivePilotFolderInput

    def _run(self, folder_id: str) -> str:
        """
        Execute the pilot folder scan.

        Returns:
            JSON string with list of files from the specified folder
        """
        try:
            files = get_pilot_folder_files(folder_id)

            result = {
                "folder_id": folder_id,
                "total_files": len(files),
                "files": [
                    {
                        "filename": f["filename"],
                        "file_id": f["file_id"],
                        "mime_type": f["mime_type"],
                        "web_view_link": f["web_view_link"],
                        "download_link": f.get("download_link"),
                        "size_bytes": f.get("file_size_bytes"),
                        "modified_time": f["modified_time"],
                        "owner_email": f.get("owner_email"),
                    }
                    for f in files
                ]
            }

            return json.dumps(result, indent=2, ensure_ascii=False)

        except Exception as e:
            return json.dumps({
                "error": str(e),
                "message": "Failed to scan pilot folder. Verify folder ID and service account permissions."
            }, indent=2)


class GoogleDriveDownloadInput(BaseModel):
    """Input schema for GoogleDriveDownloadTool."""
    file_id: str = Field(
        ...,
        description="Google Drive file ID to download"
    )
    mime_type: str = Field(
        ...,
        description="MIME type of the file (e.g., 'application/pdf', 'application/vnd.google-apps.document')"
    )


class GoogleDriveDownloadTool(BaseTool):
    name: str = "Google Drive File Downloader"
    description: str = (
        "Downloads file content from Google Drive by file ID. "
        "Supports regular files (PDFs, Word docs) and Google Workspace files "
        "(Google Docs, Sheets, Slides) which are automatically exported to PDF format. "
        "Returns the file size and download status."
    )
    args_schema: Type[BaseModel] = GoogleDriveDownloadInput

    def _run(self, file_id: str, mime_type: str) -> str:
        """
        Download file from Google Drive.

        Returns:
            JSON string with download status and file size
        """
        try:
            content = download_file_content(file_id, mime_type)

            result = {
                "status": "success",
                "file_id": file_id,
                "mime_type": mime_type,
                "size_bytes": len(content),
                "message": f"Successfully downloaded {len(content)} bytes"
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e),
                "message": "Failed to download file. Verify file ID and permissions."
            }, indent=2)
