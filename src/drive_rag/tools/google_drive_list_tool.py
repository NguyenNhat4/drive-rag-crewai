# src/my_project/tools/google_drive_tools.py

from typing import List, Dict, Optional
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
# Use path relative to current file location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FOLDER = os.path.join(BASE_DIR, "credentials")
# Path where token and credentials are stored after setup
TOKEN_FILE = os.path.join(CREDENTIALS_FOLDER, "token.pickle")
CREDENTIALS_FILE = os.path.join(CREDENTIALS_FOLDER, "credentials.json")
SCOPES = [
    'https://www.googleapis.com/auth/drive.metadata.readonly',
    'https://www.googleapis.com/auth/drive.readonly'  # For downloading
]

# Create credentials folder if not exists
os.makedirs(CREDENTIALS_FOLDER, exist_ok=True)


def get_drive_service():
    """
    Authenticate and return Google Drive service.
    Reusable across multiple functions.
    """
    creds = None
    
    # Load saved credentials
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # Refresh or create new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            logger.info("Starting OAuth flow...")
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save credentials
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
        logger.info("Credentials saved")
    
    return build('drive', 'v3', credentials=creds)


def list_google_drive_files(
    folder_id: Optional[str] = None,
    mime_types: Optional[List[str]] = None,
    include_trashed: bool = False,
    max_results: Optional[int] = None
) -> List[Dict]:
    """
    List files from Google Drive with comprehensive metadata.
    
    Args:
        folder_id: Optional folder ID to search in (for pilot scope)
        mime_types: Optional list of MIME types to filter
                   e.g., ['application/pdf', 'application/vnd.google-apps.document']
        include_trashed: Whether to include deleted files (default: False)
        max_results: Maximum number of files to return (None = all)
    
    Returns:
        List[Dict]: List of file metadata dictionaries
        
    Example:
        # Get all PDFs from QMS folder
        files = list_google_drive_files(
            folder_id="1abc123xyz",
            mime_types=["application/pdf"]
        )
    """
    try:
        service = get_drive_service()
        
        # Build query
        query_parts = []
        
        if folder_id:
            query_parts.append(f"'{folder_id}' in parents")
        
        if mime_types:
            mime_query = " or ".join([f"mimeType='{mt}'" for mt in mime_types])
            query_parts.append(f"({mime_query})")
        
        if not include_trashed:
            query_parts.append("trashed=false")
        
        query = " and ".join(query_parts) if query_parts else None
        
        logger.info(f"Query: {query}")
        
        # Fields to retrieve - COMPREHENSIVE!
        fields = """
            nextPageToken,
            files(
                id,
                name,
                mimeType,
                createdTime,
                modifiedTime,
                size,
                version,
                webViewLink,
                webContentLink,
                iconLink,
                thumbnailLink,
                trashed,
                starred,
                shared,
                owners(emailAddress, displayName),
                lastModifyingUser(emailAddress, displayName),
                sharingUser(emailAddress, displayName),
                permissions(id, emailAddress, role, type),
                parents,
                properties,
                appProperties
            )
        """.replace('\n', '').replace(' ', '')
        
        # Pagination to get ALL files
        all_files = []
        page_token = None
        page_count = 0
        
        while True:
            page_count += 1
            logger.info(f"Fetching page {page_count}...")
            
            results = service.files().list(
                q=query,
                pageSize=100,  # Max per page
                fields=fields,
                pageToken=page_token,
                supportsAllDrives=True,  # Include Shared Drives
                includeItemsFromAllDrives=True
            ).execute()
            
            items = results.get('files', [])
            all_files.extend(items)
            
            logger.info(f"Page {page_count}: {len(items)} files")
            
            # Check if we've hit max_results
            if max_results and len(all_files) >= max_results:
                all_files = all_files[:max_results]
                break
            
            # Check for next page
            page_token = results.get('nextPageToken')
            if not page_token:
                break
        
        logger.info(f"Total files retrieved: {len(all_files)}")
        
        # Transform to structured metadata
        structured_files = []
        for item in all_files:
            metadata = _extract_file_metadata(item, service)
            structured_files.append(metadata)
        
        return structured_files
        
    except Exception as e:
        logger.error(f"Error listing Drive files: {e}")
        raise


def _extract_file_metadata(file_item: Dict, service) -> Dict:
    """
    Extract and structure file metadata.
    Internal helper function.
    """
    file_id = file_item.get('id')
    
    # Get parent folder info if exists
    parent_info = {}
    if 'parents' in file_item and file_item['parents']:
        parent_id = file_item['parents'][0]
        try:
            parent = service.files().get(
                fileId=parent_id,
                fields='id,name',
                supportsAllDrives=True
            ).execute()
            parent_info = {
                'parent_folder_id': parent.get('id'),
                'parent_folder_name': parent.get('name')
            }
        except:
            parent_info = {
                'parent_folder_id': parent_id,
                'parent_folder_name': 'Unknown'
            }
    
    # Extract owner info
    owners = file_item.get('owners', [])
    owner_email = owners[0].get('emailAddress') if owners else None
    
    # Extract last modifier
    modifier = file_item.get('lastModifyingUser', {})
    modifier_email = modifier.get('emailAddress')
    
    # Extract permissions (CRITICAL for compliance!)
    permissions = file_item.get('permissions', [])
    permission_list = [
        {
            'email': p.get('emailAddress'),
            'role': p.get('role'),
            'type': p.get('type')
        }
        for p in permissions
    ]
    
    # Build comprehensive metadata
    metadata = {
        # === IDENTITY ===
        'file_id': file_id,
        'filename': file_item.get('name'),
        'mime_type': file_item.get('mimeType'),
        
        # === LINKS ===
        'web_view_link': file_item.get('webViewLink'),
        'download_link': file_item.get('webContentLink'),
        'icon_link': file_item.get('iconLink'),
        'thumbnail_link': file_item.get('thumbnailLink'),
        
        # === TEMPORAL ===
        'created_time': file_item.get('createdTime'),
        'modified_time': file_item.get('modifiedTime'),
        'indexed_at': datetime.utcnow().isoformat() + 'Z',
        
        # === OWNERSHIP & PERMISSIONS ===
        'owner_email': owner_email,
        'modified_by_email': modifier_email,
        'permissions': permission_list,
        'shared': file_item.get('shared', False),
        
        # === ORGANIZATION ===
        **parent_info,
        
        # === TECHNICAL ===
        'file_size_bytes': int(file_item.get('size', 0)) if file_item.get('size') else None,
        'version': file_item.get('version'),
        'trashed': file_item.get('trashed', False),
        'starred': file_item.get('starred', False),
        
        # === CUSTOM PROPERTIES (if any) ===
        'properties': file_item.get('properties', {}),
        'app_properties': file_item.get('appProperties', {}),
        
        # === PLACEHOLDERS for later extraction ===
        'text_content': None,  # Fill after download
        'chunks': [],          # Fill after chunking
        'document_type': None, # Extract via LLM
        'case_id': None,       # Extract from filename/content
        'iso_clauses': [],     # Extract from content
        'approval_status': None
    }
    
    return metadata


def download_file_content(file_id: str, mime_type: str) -> bytes:
    """
    Download file content from Google Drive.
    
    Args:
        file_id: Google Drive file ID
        mime_type: MIME type of file
        
    Returns:
        bytes: File content
        
    Example:
        content = download_file_content(
            file_id="1abc123",
            mime_type="application/pdf"
        )
    """
    try:
        service = get_drive_service()
        
        # Google Docs need export, not download
        if mime_type.startswith('application/vnd.google-apps'):
            # Map Google MIME types to export formats
            export_map = {
                'application/vnd.google-apps.document': 'application/pdf',
                'application/vnd.google-apps.spreadsheet': 'application/pdf',
                'application/vnd.google-apps.presentation': 'application/pdf',
            }
            export_mime = export_map.get(mime_type, 'application/pdf')
            
            request = service.files().export_media(
                fileId=file_id,
                mimeType=export_mime
            )
        else:
            # Regular files - direct download
            request = service.files().get_media(fileId=file_id)
        
        # Execute download
        logger.info(f"Downloading file {file_id}...")
        content = request.execute()
        logger.info(f"Downloaded {len(content)} bytes")
        
        return content
        
    except Exception as e:
        logger.error(f"Error downloading file {file_id}: {e}")
        raise


def get_pilot_folder_files(folder_id: str) -> List[Dict]:
    """
    Convenience function for pilot scope.
    Get all files from specific folder (e.g., QMS Cases 2023).
    
    Args:
        folder_id: Google Drive folder ID
        
    Returns:
        List[Dict]: Files with metadata
        
    Example:
        # Get all files from QMS pilot folder
        files = get_pilot_folder_files("1abc_qms_folder_id")
    """
    logger.info(f"Getting files from pilot folder: {folder_id}")
    
    # Filter for common document types
    common_doc_types = [
        'application/pdf',
        'application/vnd.google-apps.document',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ]
    
    return list_google_drive_files(
        folder_id=folder_id,
        mime_types=common_doc_types,
        include_trashed=False
    )


# === USAGE EXAMPLES ===

if __name__ == "__main__":
    # Example 1: Get all files from pilot folder
    PILOT_FOLDER_ID = "1vx3kBsi64do_BZPiGwM0G_0fCqZtkgrY"  # Replace with actual folder ID
    
    files = get_pilot_folder_files(PILOT_FOLDER_ID)
    print(f"\nFound {len(files)} files")
    
    # Example 2: Print metadata for first file
    if files:
        first_file = files[0]
        print(f"\n=== Sample Metadata ===")
        print(f"Filename: {first_file['filename']}")
        print(f"File ID: {first_file['file_id']}")
        print(f"MIME Type: {first_file['mime_type']}")
        print(f"Size: {first_file['file_size_bytes']} bytes")
        print(f"Modified: {first_file['modified_time']}")
        print(f"Owner: {first_file['owner_email']}")
        print(f"Shared: {first_file['shared']}")
        print(f"Permissions: {len(first_file['permissions'])} users")
        
    # Example 3: Download first PDF
    pdf_files = [f for f in files if f['mime_type'] == 'application/pdf']
    if pdf_files:
        first_pdf = pdf_files[0]
        print(f"\nDownloading: {first_pdf['filename']}")
        content = download_file_content(
            first_pdf['file_id'],
            first_pdf['mime_type']
        )
        print(f"Downloaded {len(content)} bytes")