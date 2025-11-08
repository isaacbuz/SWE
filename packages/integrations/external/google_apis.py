"""
Google APIs Client

Provides integration with Google Workspace APIs:
- Google Sheets API (read data for evidence)
- Google Drive API (upload artifacts)
- BigQuery API (analytics queries)
- OAuth 2.0 authentication
"""

import json
from typing import Any, Dict, List, Optional, Callable
from urllib.parse import urlencode

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


class GoogleAPIsClient:
    """
    Google APIs client with OAuth 2.0 authentication

    Supports Sheets, Drive, and BigQuery APIs for
    data collection and artifact management.
    """

    def __init__(
        self,
        token_getter: Optional[Callable[[], str]] = None,
        credentials_file: Optional[str] = None,
        scopes: Optional[List[str]] = None,
    ):
        """
        Initialize Google APIs client

        Args:
            token_getter: Function that returns OAuth access token
            credentials_file: Path to service account JSON credentials
            scopes: OAuth scopes to request
        """
        self.token_getter = token_getter
        self.credentials_file = credentials_file
        self.scopes = scopes or [
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/bigquery",
        ]

        # API base URLs
        self.sheets_base = "https://sheets.googleapis.com/v4"
        self.drive_base = "https://www.googleapis.com/drive/v3"
        self.bigquery_base = "https://bigquery.googleapis.com/bigquery/v2"

    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        if self.token_getter:
            token = self.token_getter()
        elif self.credentials_file:
            # Use service account
            token = self._get_service_account_token()
        else:
            raise ValueError("No authentication method provided")

        return {"Authorization": f"Bearer {token}"}

    def _get_service_account_token(self) -> str:
        """
        Get access token from service account credentials

        Returns:
            OAuth access token
        """
        # In production, use google-auth library
        # This is a simplified implementation
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request

        credentials = service_account.Credentials.from_service_account_file(
            self.credentials_file,
            scopes=self.scopes,
        )

        credentials.refresh(Request())
        return credentials.token

    # Google Sheets API

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=30))
    async def read_sheet(
        self,
        spreadsheet_id: str,
        range_a1: str,
    ) -> Dict[str, Any]:
        """
        Read data from Google Sheet

        Args:
            spreadsheet_id: Spreadsheet ID
            range_a1: Range in A1 notation (e.g., "Sheet1!A1:D10")

        Returns:
            Sheet data with values
        """
        url = f"{self.sheets_base}/spreadsheets/{spreadsheet_id}/values/{range_a1}"
        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()

    async def read_sheet_as_records(
        self,
        spreadsheet_id: str,
        range_a1: str,
        header_row: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Read Google Sheet as list of dictionaries

        Args:
            spreadsheet_id: Spreadsheet ID
            range_a1: Range in A1 notation
            header_row: Index of header row (0-based)

        Returns:
            List of records as dictionaries
        """
        data = await self.read_sheet(spreadsheet_id, range_a1)
        values = data.get("values", [])

        if not values or len(values) <= header_row:
            return []

        headers = values[header_row]
        records = []

        for row in values[header_row + 1:]:
            # Pad row to match header length
            padded_row = row + [""] * (len(headers) - len(row))
            record = dict(zip(headers, padded_row))
            records.append(record)

        return records

    async def get_spreadsheet_metadata(
        self,
        spreadsheet_id: str,
    ) -> Dict[str, Any]:
        """
        Get spreadsheet metadata

        Args:
            spreadsheet_id: Spreadsheet ID

        Returns:
            Spreadsheet metadata
        """
        url = f"{self.sheets_base}/spreadsheets/{spreadsheet_id}"
        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()

    async def append_to_sheet(
        self,
        spreadsheet_id: str,
        range_a1: str,
        values: List[List[Any]],
        value_input_option: str = "USER_ENTERED",
    ) -> Dict[str, Any]:
        """
        Append data to Google Sheet

        Args:
            spreadsheet_id: Spreadsheet ID
            range_a1: Range in A1 notation
            values: 2D array of values to append
            value_input_option: How to interpret values ("RAW" or "USER_ENTERED")

        Returns:
            Append result
        """
        url = f"{self.sheets_base}/spreadsheets/{spreadsheet_id}/values/{range_a1}:append"
        headers = self._get_headers()
        params = {"valueInputOption": value_input_option}
        payload = {"values": values}

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=headers, params=params, json=payload)
            response.raise_for_status()
            return response.json()

    # Google Drive API

    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        mime_type: str = "application/octet-stream",
        folder_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload file to Google Drive

        Args:
            file_content: File content as bytes
            filename: File name
            mime_type: File MIME type
            folder_id: Optional parent folder ID

        Returns:
            Created file metadata
        """
        # Create file metadata
        metadata = {"name": filename}
        if folder_id:
            metadata["parents"] = [folder_id]

        # Upload file (multipart)
        url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart"
        headers = self._get_headers()

        import io
        from email.mime.multipart import MIMEMultipart
        from email.mime.application import MIMEApplication
        from email.mime.text import MIMEText

        # Build multipart request
        multipart = MIMEMultipart("related")

        # Part 1: Metadata
        metadata_part = MIMEText(json.dumps(metadata), "json")
        multipart.attach(metadata_part)

        # Part 2: File content
        file_part = MIMEApplication(file_content, mime_type)
        multipart.attach(file_part)

        # Get boundary
        boundary = multipart.get_boundary()
        headers["Content-Type"] = f"multipart/related; boundary={boundary}"

        # Serialize multipart
        body = multipart.as_bytes()

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, headers=headers, content=body)
            response.raise_for_status()
            return response.json()

    async def list_files(
        self,
        query: Optional[str] = None,
        page_size: int = 100,
        order_by: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List files in Google Drive

        Args:
            query: Search query (e.g., "name contains 'report'")
            page_size: Number of files per page
            order_by: Order by field (e.g., "createdTime desc")

        Returns:
            List of files
        """
        url = f"{self.drive_base}/files"
        headers = self._get_headers()
        params = {"pageSize": page_size}

        if query:
            params["q"] = query
        if order_by:
            params["orderBy"] = order_by

        all_files = []
        page_token = None

        async with httpx.AsyncClient(timeout=30) as client:
            while True:
                if page_token:
                    params["pageToken"] = page_token

                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()

                all_files.extend(data.get("files", []))

                page_token = data.get("nextPageToken")
                if not page_token:
                    break

        return all_files

    async def download_file(
        self,
        file_id: str,
    ) -> bytes:
        """
        Download file from Google Drive

        Args:
            file_id: File ID

        Returns:
            File content as bytes
        """
        url = f"{self.drive_base}/files/{file_id}?alt=media"
        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.content

    async def create_folder(
        self,
        name: str,
        parent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create folder in Google Drive

        Args:
            name: Folder name
            parent_id: Optional parent folder ID

        Returns:
            Created folder metadata
        """
        url = f"{self.drive_base}/files"
        headers = self._get_headers()

        metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }

        if parent_id:
            metadata["parents"] = [parent_id]

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=headers, json=metadata)
            response.raise_for_status()
            return response.json()

    # BigQuery API

    async def query_bigquery(
        self,
        project_id: str,
        query: str,
        use_legacy_sql: bool = False,
        max_results: int = 1000,
    ) -> Dict[str, Any]:
        """
        Execute BigQuery query

        Args:
            project_id: GCP project ID
            query: SQL query
            use_legacy_sql: Use legacy SQL syntax
            max_results: Maximum rows to return

        Returns:
            Query results
        """
        url = f"{self.bigquery_base}/projects/{project_id}/queries"
        headers = self._get_headers()

        payload = {
            "query": query,
            "useLegacySql": use_legacy_sql,
            "maxResults": max_results,
        }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def query_bigquery_as_records(
        self,
        project_id: str,
        query: str,
        use_legacy_sql: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Execute BigQuery query and return as list of dictionaries

        Args:
            project_id: GCP project ID
            query: SQL query
            use_legacy_sql: Use legacy SQL syntax

        Returns:
            List of records as dictionaries
        """
        result = await self.query_bigquery(project_id, query, use_legacy_sql)

        schema = result.get("schema", {}).get("fields", [])
        rows = result.get("rows", [])

        records = []
        for row in rows:
            record = {}
            for i, field in enumerate(schema):
                field_name = field["name"]
                value = row["f"][i]["v"]
                record[field_name] = value
            records.append(record)

        return records

    async def list_datasets(
        self,
        project_id: str,
    ) -> List[Dict[str, Any]]:
        """
        List BigQuery datasets

        Args:
            project_id: GCP project ID

        Returns:
            List of datasets
        """
        url = f"{self.bigquery_base}/projects/{project_id}/datasets"
        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("datasets", [])

    async def list_tables(
        self,
        project_id: str,
        dataset_id: str,
    ) -> List[Dict[str, Any]]:
        """
        List tables in a BigQuery dataset

        Args:
            project_id: GCP project ID
            dataset_id: Dataset ID

        Returns:
            List of tables
        """
        url = f"{self.bigquery_base}/projects/{project_id}/datasets/{dataset_id}/tables"
        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("tables", [])
