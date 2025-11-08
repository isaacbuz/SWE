"""
Government APIs Client

Provides integration with government data sources:
- Data.gov catalog search
- GSA API Standards
- Public dataset queries
- Evidence corpus building
"""

from typing import Any, Dict, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


class GovernmentAPIsClient:
    """
    Government APIs client

    Provides access to government data sources for
    evidence collection and compliance checking.
    """

    def __init__(
        self,
        data_gov_api_key: Optional[str] = None,
        gsa_api_key: Optional[str] = None,
    ):
        """
        Initialize Government APIs client

        Args:
            data_gov_api_key: Data.gov API key
            gsa_api_key: GSA API key
        """
        self.data_gov_api_key = data_gov_api_key
        self.gsa_api_key = gsa_api_key

        # API base URLs
        self.data_gov_base = "https://catalog.data.gov/api/3"
        self.gsa_base = "https://api.gsa.gov"
        self.usa_gov_base = "https://api.usa.gov"

    # Data.gov API

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=30))
    async def search_datasets(
        self,
        query: str,
        limit: int = 100,
        offset: int = 0,
        organization: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Search Data.gov catalog

        Args:
            query: Search query
            limit: Maximum results to return
            offset: Result offset for pagination
            organization: Filter by organization
            tags: Filter by tags

        Returns:
            Search results with datasets
        """
        url = f"{self.data_gov_base}/action/package_search"

        params = {
            "q": query,
            "rows": limit,
            "start": offset,
        }

        # Build filter query
        fq_parts = []
        if organization:
            fq_parts.append(f"organization:{organization}")
        if tags:
            for tag in tags:
                fq_parts.append(f"tags:{tag}")

        if fq_parts:
            params["fq"] = " AND ".join(fq_parts)

        headers = {}
        if self.data_gov_api_key:
            headers["X-API-Key"] = self.data_gov_api_key

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()

    async def get_dataset(
        self,
        dataset_id: str,
    ) -> Dict[str, Any]:
        """
        Get dataset details

        Args:
            dataset_id: Dataset ID or name

        Returns:
            Dataset metadata
        """
        url = f"{self.data_gov_base}/action/package_show"
        params = {"id": dataset_id}

        headers = {}
        if self.data_gov_api_key:
            headers["X-API-Key"] = self.data_gov_api_key

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("result", {})

    async def list_organizations(
        self,
        all_fields: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        List government organizations

        Args:
            all_fields: Include all metadata fields

        Returns:
            List of organizations
        """
        url = f"{self.data_gov_base}/action/organization_list"
        params = {"all_fields": str(all_fields).lower()}

        headers = {}
        if self.data_gov_api_key:
            headers["X-API-Key"] = self.data_gov_api_key

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("result", [])

    async def list_tags(
        self,
    ) -> List[str]:
        """
        List all tags in catalog

        Returns:
            List of tag names
        """
        url = f"{self.data_gov_base}/action/tag_list"

        headers = {}
        if self.data_gov_api_key:
            headers["X-API-Key"] = self.data_gov_api_key

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("result", [])

    async def build_evidence_corpus(
        self,
        topics: List[str],
        limit_per_topic: int = 50,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Build evidence corpus from government datasets

        Args:
            topics: List of topics to search
            limit_per_topic: Maximum datasets per topic

        Returns:
            Dictionary mapping topics to datasets
        """
        corpus = {}

        for topic in topics:
            results = await self.search_datasets(
                query=topic,
                limit=limit_per_topic,
            )

            datasets = results.get("result", {}).get("results", [])
            corpus[topic] = datasets

        return corpus

    # GSA API

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=30))
    async def get_gsa_standards(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Query GSA API Standards

        Args:
            endpoint: API endpoint (e.g., "/systems/")
            params: Query parameters

        Returns:
            API response data
        """
        url = f"{self.gsa_base}/{endpoint.lstrip('/')}"
        headers = {}

        if self.gsa_api_key:
            headers["X-API-Key"] = self.gsa_api_key

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=headers, params=params or {})
            response.raise_for_status()
            return response.json()

    async def get_sam_entity(
        self,
        uei: str,
    ) -> Dict[str, Any]:
        """
        Get SAM.gov entity information

        Args:
            uei: Unique Entity Identifier (UEI)

        Returns:
            Entity data
        """
        # SAM.gov API endpoint
        url = "https://api.sam.gov/entity-information/v3/entities"
        params = {"ueiSAM": uei}

        headers = {}
        if self.gsa_api_key:
            headers["X-API-Key"] = self.gsa_api_key

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()

    async def search_contracts(
        self,
        query: Optional[str] = None,
        limit: int = 100,
        award_start_date: Optional[str] = None,
        award_end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search federal contracts (USAspending.gov)

        Args:
            query: Search query
            limit: Maximum results
            award_start_date: Start date (YYYY-MM-DD)
            award_end_date: End date (YYYY-MM-DD)

        Returns:
            List of contracts
        """
        url = "https://api.usaspending.gov/api/v2/search/spending_by_award"

        filters = {}
        if query:
            filters["keywords"] = [query]
        if award_start_date:
            filters["award_start_date"] = award_start_date
        if award_end_date:
            filters["award_end_date"] = award_end_date

        payload = {
            "filters": filters,
            "fields": [
                "Award ID",
                "Recipient Name",
                "Award Amount",
                "Award Date",
                "Description",
            ],
            "limit": limit,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])

    # Federal Register API

    async def search_federal_register(
        self,
        term: str,
        publication_date_gte: Optional[str] = None,
        publication_date_lte: Optional[str] = None,
        document_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search Federal Register

        Args:
            term: Search term
            publication_date_gte: Published on or after (YYYY-MM-DD)
            publication_date_lte: Published on or before (YYYY-MM-DD)
            document_type: Document type (RULE, PRORULE, NOTICE, PRESDOCU)

        Returns:
            Search results
        """
        url = "https://www.federalregister.gov/api/v1/documents.json"

        params = {
            "conditions[term]": term,
            "per_page": 100,
        }

        if publication_date_gte:
            params["conditions[publication_date][gte]"] = publication_date_gte
        if publication_date_lte:
            params["conditions[publication_date][lte]"] = publication_date_lte
        if document_type:
            params["conditions[type][]"] = document_type

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def get_federal_register_document(
        self,
        document_number: str,
    ) -> Dict[str, Any]:
        """
        Get Federal Register document

        Args:
            document_number: Document number

        Returns:
            Document data
        """
        url = f"https://www.federalregister.gov/api/v1/documents/{document_number}.json"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    # Census API

    async def query_census(
        self,
        dataset: str,
        variables: List[str],
        geography: str,
        year: Optional[int] = None,
    ) -> List[List[str]]:
        """
        Query Census Bureau API

        Args:
            dataset: Dataset name (e.g., "acs/acs5")
            variables: List of variable names
            geography: Geography specification (e.g., "state:*")
            year: Optional year

        Returns:
            Census data as list of rows
        """
        if year:
            url = f"https://api.census.gov/data/{year}/{dataset}"
        else:
            url = f"https://api.census.gov/data/{dataset}"

        params = {
            "get": ",".join(variables),
            "for": geography,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    # Evidence Collection

    async def collect_compliance_evidence(
        self,
        regulation_keywords: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Collect compliance evidence from multiple sources

        Args:
            regulation_keywords: Keywords related to regulations
            start_date: Start date for documents (YYYY-MM-DD)
            end_date: End date for documents (YYYY-MM-DD)

        Returns:
            Aggregated evidence from multiple sources
        """
        evidence = {
            "datasets": [],
            "regulations": [],
            "contracts": [],
        }

        # Search Data.gov for related datasets
        for keyword in regulation_keywords:
            datasets = await self.search_datasets(query=keyword, limit=20)
            evidence["datasets"].extend(
                datasets.get("result", {}).get("results", [])
            )

        # Search Federal Register for regulations
        for keyword in regulation_keywords:
            regulations = await self.search_federal_register(
                term=keyword,
                publication_date_gte=start_date,
                publication_date_lte=end_date,
            )
            evidence["regulations"].extend(regulations.get("results", []))

        # Search contracts if applicable
        if start_date and end_date:
            contracts = await self.search_contracts(
                award_start_date=start_date,
                award_end_date=end_date,
            )
            evidence["contracts"].extend(contracts)

        return evidence
