"""
GitHub Projects Operations

Provides project board management:
- Create project boards
- Add issues to projects
- Update project cards
- Query project state
"""

from typing import Any, Dict, List, Optional

from .client import GitHubClient


class ProjectOperations:
    """
    GitHub Projects operations (Projects V2)

    Handles project board operations including creation,
    item management, and field updates.
    """

    def __init__(self, client: GitHubClient):
        """
        Initialize project operations

        Args:
            client: GitHubClient instance
        """
        self.client = client

    async def create_project(
        self,
        owner: str,
        repo: Optional[str] = None,
        title: str = "New Project",
        body: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new project using GraphQL (Projects V2)

        Args:
            owner: Organization or user login
            repo: Optional repository name (for repo projects)
            title: Project title
            body: Project description

        Returns:
            Created project data
        """
        # Get owner ID
        owner_query = """
        query($login: String!) {
          user(login: $login) {
            id
          }
          organization(login: $login) {
            id
          }
        }
        """

        owner_data = await self.client.graphql(owner_query, {"login": owner})
        owner_id = owner_data.get("user", {}).get("id") or owner_data.get("organization", {}).get("id")

        # Create project
        mutation = """
        mutation($ownerId: ID!, $title: String!) {
          createProjectV2(input: {ownerId: $ownerId, title: $title}) {
            projectV2 {
              id
              title
              url
              number
            }
          }
        }
        """

        variables = {
            "ownerId": owner_id,
            "title": title,
        }

        result = await self.client.graphql(mutation, variables)
        return result.get("createProjectV2", {}).get("projectV2", {})

    async def get_project(
        self,
        project_number: int,
        owner: str,
    ) -> Dict[str, Any]:
        """
        Get project details

        Args:
            project_number: Project number
            owner: Owner login

        Returns:
            Project data
        """
        query = """
        query($login: String!, $number: Int!) {
          user(login: $login) {
            projectV2(number: $number) {
              id
              title
              url
              number
              shortDescription
              public
              closed
              createdAt
              updatedAt
            }
          }
          organization(login: $login) {
            projectV2(number: $number) {
              id
              title
              url
              number
              shortDescription
              public
              closed
              createdAt
              updatedAt
            }
          }
        }
        """

        variables = {"login": owner, "number": project_number}
        result = await self.client.graphql(query, variables)

        return result.get("user", {}).get("projectV2") or result.get("organization", {}).get("projectV2", {})

    async def add_issue_to_project(
        self,
        project_id: str,
        issue_id: str,
    ) -> Dict[str, Any]:
        """
        Add an issue to a project

        Args:
            project_id: Project node ID
            issue_id: Issue node ID

        Returns:
            Created project item
        """
        mutation = """
        mutation($projectId: ID!, $contentId: ID!) {
          addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
            item {
              id
            }
          }
        }
        """

        variables = {
            "projectId": project_id,
            "contentId": issue_id,
        }

        result = await self.client.graphql(mutation, variables)
        return result.get("addProjectV2ItemById", {}).get("item", {})

    async def add_pr_to_project(
        self,
        project_id: str,
        pr_id: str,
    ) -> Dict[str, Any]:
        """
        Add a pull request to a project

        Args:
            project_id: Project node ID
            pr_id: PR node ID

        Returns:
            Created project item
        """
        # Same mutation as add_issue_to_project
        return await self.add_issue_to_project(project_id, pr_id)

    async def update_project_item_field(
        self,
        project_id: str,
        item_id: str,
        field_id: str,
        value: Any,
    ) -> Dict[str, Any]:
        """
        Update a project item field

        Args:
            project_id: Project node ID
            item_id: Project item ID
            field_id: Field ID
            value: New field value

        Returns:
            Updated project item
        """
        mutation = """
        mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: ProjectV2FieldValue!) {
          updateProjectV2ItemFieldValue(
            input: {projectId: $projectId, itemId: $itemId, fieldId: $fieldId, value: $value}
          ) {
            projectV2Item {
              id
            }
          }
        }
        """

        variables = {
            "projectId": project_id,
            "itemId": item_id,
            "fieldId": field_id,
            "value": value,
        }

        result = await self.client.graphql(mutation, variables)
        return result.get("updateProjectV2ItemFieldValue", {}).get("projectV2Item", {})

    async def get_project_items(
        self,
        project_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get items in a project

        Args:
            project_id: Project node ID
            limit: Maximum items to fetch

        Returns:
            List of project items
        """
        query = """
        query($projectId: ID!, $limit: Int!) {
          node(id: $projectId) {
            ... on ProjectV2 {
              items(first: $limit) {
                nodes {
                  id
                  type
                  content {
                    ... on Issue {
                      id
                      title
                      number
                      state
                      url
                    }
                    ... on PullRequest {
                      id
                      title
                      number
                      state
                      url
                    }
                  }
                  fieldValues(first: 10) {
                    nodes {
                      ... on ProjectV2ItemFieldTextValue {
                        text
                        field {
                          ... on ProjectV2FieldCommon {
                            name
                          }
                        }
                      }
                      ... on ProjectV2ItemFieldSingleSelectValue {
                        name
                        field {
                          ... on ProjectV2FieldCommon {
                            name
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """

        variables = {"projectId": project_id, "limit": limit}
        result = await self.client.graphql(query, variables)

        node = result.get("node", {})
        items = node.get("items", {}).get("nodes", [])

        return items

    async def get_project_fields(
        self,
        project_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get project fields

        Args:
            project_id: Project node ID

        Returns:
            List of project fields
        """
        query = """
        query($projectId: ID!) {
          node(id: $projectId) {
            ... on ProjectV2 {
              fields(first: 20) {
                nodes {
                  ... on ProjectV2Field {
                    id
                    name
                    dataType
                  }
                  ... on ProjectV2SingleSelectField {
                    id
                    name
                    options {
                      id
                      name
                    }
                  }
                }
              }
            }
          }
        }
        """

        variables = {"projectId": project_id}
        result = await self.client.graphql(query, variables)

        node = result.get("node", {})
        fields = node.get("fields", {}).get("nodes", [])

        return fields

    async def create_status_field(
        self,
        project_id: str,
        name: str = "Status",
        options: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Create a status field in a project

        Args:
            project_id: Project node ID
            name: Field name
            options: List of option dicts with 'name' and optional 'color'

        Returns:
            Created field data
        """
        if options is None:
            options = [
                {"name": "Todo"},
                {"name": "In Progress"},
                {"name": "Done"},
            ]

        mutation = """
        mutation($projectId: ID!, $name: String!, $options: [ProjectV2SingleSelectFieldOptionInput!]!) {
          createProjectV2Field(
            input: {projectId: $projectId, dataType: SINGLE_SELECT, name: $name, singleSelectOptions: $options}
          ) {
            projectV2Field {
              ... on ProjectV2SingleSelectField {
                id
                name
                options {
                  id
                  name
                }
              }
            }
          }
        }
        """

        # Convert options to proper format
        field_options = [{"name": opt["name"]} for opt in options]

        variables = {
            "projectId": project_id,
            "name": name,
            "options": field_options,
        }

        result = await self.client.graphql(mutation, variables)
        return result.get("createProjectV2Field", {}).get("projectV2Field", {})

    async def get_issue_node_id(
        self,
        owner: str,
        repo: str,
        issue_number: int,
    ) -> str:
        """
        Get issue node ID for use in Projects V2

        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number

        Returns:
            Issue node ID
        """
        query = """
        query($owner: String!, $repo: String!, $number: Int!) {
          repository(owner: $owner, name: $repo) {
            issue(number: $number) {
              id
            }
          }
        }
        """

        variables = {"owner": owner, "repo": repo, "number": issue_number}
        result = await self.client.graphql(query, variables)

        return result.get("repository", {}).get("issue", {}).get("id", "")

    async def get_pr_node_id(
        self,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> str:
        """
        Get PR node ID for use in Projects V2

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number

        Returns:
            PR node ID
        """
        query = """
        query($owner: String!, $repo: String!, $number: Int!) {
          repository(owner: $owner, name: $repo) {
            pullRequest(number: $number) {
              id
            }
          }
        }
        """

        variables = {"owner": owner, "repo": repo, "number": pr_number}
        result = await self.client.graphql(query, variables)

        return result.get("repository", {}).get("pullRequest", {}).get("id", "")

    async def delete_project_item(
        self,
        project_id: str,
        item_id: str,
    ) -> Dict[str, Any]:
        """
        Remove an item from a project

        Args:
            project_id: Project node ID
            item_id: Project item ID

        Returns:
            Deletion result
        """
        mutation = """
        mutation($projectId: ID!, $itemId: ID!) {
          deleteProjectV2Item(input: {projectId: $projectId, itemId: $itemId}) {
            deletedItemId
          }
        }
        """

        variables = {"projectId": project_id, "itemId": item_id}
        result = await self.client.graphql(mutation, variables)

        return result.get("deleteProjectV2Item", {})
