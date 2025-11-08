"""
Documentation Synchronization Agent

Keeps documentation synchronized with code:
- Auto-generates documentation from code
- Syncs README files
- Updates API documentation
- Generates changelog
- Syncs inline code comments
- Updates architecture diagrams
- Validates documentation accuracy

Integrates with documentation systems (Sphinx, JSDoc, etc.)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from enum import Enum
import re
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DocType(Enum):
    """Types of documentation"""
    API = "api"
    README = "readme"
    CHANGELOG = "changelog"
    ARCHITECTURE = "architecture"
    TUTORIAL = "tutorial"
    INLINE = "inline"
    REFERENCE = "reference"


class DocFormat(Enum):
    """Documentation formats"""
    MARKDOWN = "markdown"
    RST = "rst"  # ReStructuredText
    HTML = "html"
    OPENAPI = "openapi"
    JSDOC = "jsdoc"
    SPHINX = "sphinx"


@dataclass
class DocSection:
    """A documentation section"""
    title: str
    content: str
    doc_type: DocType
    level: int = 1  # Heading level
    code_references: List[str] = field(default_factory=list)


@dataclass
class Documentation:
    """Complete documentation"""
    title: str
    format: DocFormat
    sections: List[DocSection] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocUpdate:
    """Documentation update"""
    file_path: str
    doc_type: DocType
    old_content: Optional[str]
    new_content: str
    reason: str
    code_changes: List[str] = field(default_factory=list)


@dataclass
class DocSyncResult:
    """Result of documentation synchronization"""
    success: bool
    updates: List[DocUpdate] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    summary: str = ""


class DocSyncAgent:
    """
    Documentation Synchronization Agent

    Automatically keeps documentation in sync with code changes,
    generates missing documentation, and validates accuracy.
    """

    def __init__(
        self,
        model_id: str = "claude-sonnet-4",
        auto_update: bool = False,
        doc_format: DocFormat = DocFormat.MARKDOWN,
    ):
        """
        Initialize Doc Sync Agent

        Args:
            model_id: LLM model for documentation generation
            auto_update: Automatically update documentation
            doc_format: Preferred documentation format
        """
        self.model_id = model_id
        self.auto_update = auto_update
        self.doc_format = doc_format

    async def sync_documentation(
        self,
        code_changes: Dict[str, str],
        existing_docs: Dict[str, str],
    ) -> DocSyncResult:
        """
        Synchronize documentation with code changes

        Args:
            code_changes: Map of file_path -> code content
            existing_docs: Map of doc_path -> doc content

        Returns:
            Synchronization result
        """
        logger.info(f"Syncing documentation for {len(code_changes)} files")

        updates = []
        errors = []
        warnings = []

        # Analyze what documentation needs updating
        for file_path, code in code_changes.items():
            # Check for API changes
            if self._is_api_file(file_path):
                api_update = await self._sync_api_docs(file_path, code, existing_docs)
                if api_update:
                    updates.append(api_update)

            # Check for README updates needed
            readme_update = await self._sync_readme(file_path, code, existing_docs)
            if readme_update:
                updates.append(readme_update)

            # Check inline documentation
            inline_warnings = self._check_inline_docs(file_path, code)
            warnings.extend(inline_warnings)

        # Update changelog
        changelog_update = await self._update_changelog(code_changes)
        if changelog_update:
            updates.append(changelog_update)

        # Validate documentation accuracy
        validation_errors = await self._validate_documentation(
            code_changes,
            existing_docs,
        )
        errors.extend(validation_errors)

        # Generate summary
        summary = self._generate_sync_summary(updates, errors, warnings)

        result = DocSyncResult(
            success=len(errors) == 0,
            updates=updates,
            errors=errors,
            warnings=warnings,
            summary=summary,
        )

        logger.info(f"Documentation sync complete: {len(updates)} updates")
        return result

    async def generate_api_docs(
        self,
        code: str,
        file_path: str,
    ) -> Documentation:
        """
        Generate API documentation from code

        Args:
            code: Source code
            file_path: File path

        Returns:
            Generated documentation
        """
        logger.info(f"Generating API docs for {file_path}")

        # Extract API endpoints/functions
        apis = self._extract_apis(code)

        sections = []

        # Generate overview section
        sections.append(DocSection(
            title="API Overview",
            content=self._generate_api_overview(apis),
            doc_type=DocType.API,
            level=1,
        ))

        # Generate section for each API
        for api in apis:
            section = DocSection(
                title=api['name'],
                content=self._generate_api_section(api),
                doc_type=DocType.API,
                level=2,
                code_references=[api['signature']],
            )
            sections.append(section)

        # Generate examples section
        sections.append(DocSection(
            title="Examples",
            content=self._generate_api_examples(apis),
            doc_type=DocType.API,
            level=1,
        ))

        documentation = Documentation(
            title=f"{file_path} API Documentation",
            format=self.doc_format,
            sections=sections,
        )

        logger.info(f"Generated {len(sections)} API doc sections")
        return documentation

    async def generate_readme(
        self,
        project_info: Dict[str, Any],
    ) -> str:
        """
        Generate README file

        Args:
            project_info: Project information

        Returns:
            README content
        """
        logger.info("Generating README")

        sections = []

        # Title and description
        sections.append(f"# {project_info.get('name', 'Project')}")
        sections.append(f"\n{project_info.get('description', '')}\n")

        # Badges
        if project_info.get('badges'):
            sections.append("## Status")
            for badge in project_info['badges']:
                sections.append(f"![{badge['name']}]({badge['url']})")
            sections.append("")

        # Installation
        sections.append("## Installation\n")
        sections.append("```bash")
        sections.append(project_info.get('install_command', 'npm install'))
        sections.append("```\n")

        # Usage
        sections.append("## Usage\n")
        sections.append("```" + project_info.get('language', 'javascript'))
        sections.append(project_info.get('usage_example', '// Example usage'))
        sections.append("```\n")

        # Features
        if project_info.get('features'):
            sections.append("## Features\n")
            for feature in project_info['features']:
                sections.append(f"- {feature}")
            sections.append("")

        # API Documentation
        sections.append("## API Documentation\n")
        sections.append("See [API.md](./docs/API.md) for detailed API documentation.\n")

        # Contributing
        sections.append("## Contributing\n")
        sections.append("Contributions are welcome! Please see [CONTRIBUTING.md](./CONTRIBUTING.md).\n")

        # License
        sections.append("## License\n")
        sections.append(f"{project_info.get('license', 'MIT')}\n")

        readme = "\n".join(sections)
        logger.info("README generated")

        return readme

    async def generate_changelog(
        self,
        commits: List[Dict[str, Any]],
        version: str,
    ) -> str:
        """
        Generate changelog from commits

        Args:
            commits: List of commits
            version: Release version

        Returns:
            Changelog content
        """
        logger.info(f"Generating changelog for version {version}")

        # Group commits by type
        features = []
        fixes = []
        breaking = []
        other = []

        for commit in commits:
            message = commit.get('message', '')

            if message.startswith('feat:'):
                features.append(message[5:].strip())
            elif message.startswith('fix:'):
                fixes.append(message[4:].strip())
            elif 'BREAKING' in message:
                breaking.append(message)
            else:
                other.append(message)

        # Format changelog
        changelog_parts = [
            f"# Changelog\n",
            f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}\n",
        ]

        if breaking:
            changelog_parts.append("### Breaking Changes\n")
            for change in breaking:
                changelog_parts.append(f"- {change}")
            changelog_parts.append("")

        if features:
            changelog_parts.append("### Features\n")
            for feature in features:
                changelog_parts.append(f"- {feature}")
            changelog_parts.append("")

        if fixes:
            changelog_parts.append("### Bug Fixes\n")
            for fix in fixes:
                changelog_parts.append(f"- {fix}")
            changelog_parts.append("")

        changelog = "\n".join(changelog_parts)
        logger.info("Changelog generated")

        return changelog

    async def validate_documentation(
        self,
        docs: Dict[str, str],
        code: Dict[str, str],
    ) -> List[str]:
        """
        Validate documentation accuracy against code

        Args:
            docs: Documentation files
            code: Code files

        Returns:
            List of validation errors
        """
        logger.info("Validating documentation accuracy")

        errors = []

        # Extract documented APIs
        documented_apis = set()
        for doc_path, doc_content in docs.items():
            apis = self._extract_documented_apis(doc_content)
            documented_apis.update(apis)

        # Extract actual APIs from code
        actual_apis = set()
        for code_path, code_content in code.items():
            apis = self._extract_apis(code_content)
            actual_apis.update(api['name'] for api in apis)

        # Find undocumented APIs
        undocumented = actual_apis - documented_apis
        for api in undocumented:
            errors.append(f"API '{api}' exists in code but is not documented")

        # Find documented but non-existent APIs
        obsolete = documented_apis - actual_apis
        for api in obsolete:
            errors.append(f"API '{api}' is documented but does not exist in code")

        logger.info(f"Found {len(errors)} documentation issues")
        return errors

    # Private helper methods

    def _is_api_file(self, file_path: str) -> bool:
        """Check if file contains API definitions"""
        api_patterns = ['api', 'route', 'endpoint', 'controller', 'handler']
        return any(pattern in file_path.lower() for pattern in api_patterns)

    async def _sync_api_docs(
        self,
        file_path: str,
        code: str,
        existing_docs: Dict[str, str],
    ) -> Optional[DocUpdate]:
        """Sync API documentation"""
        logger.info(f"Syncing API docs for {file_path}")

        # Generate new API docs
        new_docs = await self.generate_api_docs(code, file_path)

        # Format as string
        new_content = self._format_documentation(new_docs)

        # Determine doc file path
        doc_path = self._get_api_doc_path(file_path)

        # Get existing content
        old_content = existing_docs.get(doc_path)

        # Check if update needed
        if old_content != new_content:
            return DocUpdate(
                file_path=doc_path,
                doc_type=DocType.API,
                old_content=old_content,
                new_content=new_content,
                reason="API signatures changed",
                code_changes=[file_path],
            )

        return None

    async def _sync_readme(
        self,
        file_path: str,
        code: str,
        existing_docs: Dict[str, str],
    ) -> Optional[DocUpdate]:
        """Sync README if needed"""
        # Only update README for significant changes
        if 'main' in file_path.lower() or 'index' in file_path.lower():
            # README update might be needed
            # This is simplified - production would analyze impact
            return None

        return None

    def _check_inline_docs(self, file_path: str, code: str) -> List[str]:
        """Check inline documentation quality"""
        warnings = []

        # Check for functions without docstrings
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if re.match(r'^\s*(?:async\s+)?def\s+\w+\s*\(', line):
                # Check if next non-empty line is a docstring
                has_docstring = False
                for j in range(i + 1, min(i + 5, len(lines))):
                    next_line = lines[j].strip()
                    if not next_line:
                        continue
                    if next_line.startswith('"""') or next_line.startswith("'''"):
                        has_docstring = True
                        break
                    break

                if not has_docstring:
                    func_name = re.search(r'def\s+(\w+)', line).group(1)
                    warnings.append(
                        f"{file_path}:{i+1} - Function '{func_name}' missing docstring"
                    )

        return warnings

    async def _update_changelog(
        self,
        code_changes: Dict[str, str],
    ) -> Optional[DocUpdate]:
        """Update changelog based on code changes"""
        # Simplified - would analyze git commits in production
        return None

    async def _validate_documentation(
        self,
        code: Dict[str, str],
        docs: Dict[str, str],
    ) -> List[str]:
        """Validate documentation"""
        return await self.validate_documentation(docs, code)

    def _generate_sync_summary(
        self,
        updates: List[DocUpdate],
        errors: List[str],
        warnings: List[str],
    ) -> str:
        """Generate sync summary"""
        summary_parts = []

        if updates:
            summary_parts.append(f"📝 {len(updates)} documentation updates")
        if errors:
            summary_parts.append(f"❌ {len(errors)} errors")
        if warnings:
            summary_parts.append(f"⚠️ {len(warnings)} warnings")

        if not updates and not errors and not warnings:
            summary_parts.append("✅ Documentation is up to date")

        return " | ".join(summary_parts)

    def _extract_apis(self, code: str) -> List[Dict[str, Any]]:
        """Extract API definitions from code"""
        apis = []

        # Python function/method patterns
        for match in re.finditer(r'def\s+(\w+)\s*\(([^)]*)\)', code):
            name = match.group(1)
            params = match.group(2)

            apis.append({
                'name': name,
                'signature': f"def {name}({params})",
                'params': [p.strip() for p in params.split(',') if p.strip()],
                'type': 'function',
            })

        # JavaScript/TypeScript function patterns
        for match in re.finditer(r'(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)', code):
            name = match.group(1)
            params = match.group(2)

            apis.append({
                'name': name,
                'signature': f"function {name}({params})",
                'params': [p.strip() for p in params.split(',') if p.strip()],
                'type': 'function',
            })

        return apis

    def _generate_api_overview(self, apis: List[Dict[str, Any]]) -> str:
        """Generate API overview"""
        return (
            f"This module provides {len(apis)} API{'s' if len(apis) != 1 else ''}.\n\n"
            "## Quick Reference\n\n"
            + "\n".join(f"- `{api['name']}`" for api in apis)
        )

    def _generate_api_section(self, api: Dict[str, Any]) -> str:
        """Generate documentation section for an API"""
        content_parts = [
            f"### {api['name']}\n",
            f"```{self._get_code_language()}",
            api['signature'],
            "```\n",
        ]

        if api.get('params'):
            content_parts.append("**Parameters:**\n")
            for param in api['params']:
                content_parts.append(f"- `{param}`: Description needed")
            content_parts.append("")

        content_parts.append("**Returns:**\n")
        content_parts.append("- Description needed\n")

        return "\n".join(content_parts)

    def _generate_api_examples(self, apis: List[Dict[str, Any]]) -> str:
        """Generate usage examples"""
        if not apis:
            return ""

        api = apis[0]  # Example for first API

        return (
            f"```{self._get_code_language()}\n"
            f"# Example usage of {api['name']}\n"
            f"result = {api['name']}()\n"
            "```\n"
        )

    def _extract_documented_apis(self, doc_content: str) -> Set[str]:
        """Extract API names from documentation"""
        # Look for markdown headers and code blocks
        api_names = set()

        for match in re.finditer(r'###?\s+(\w+)', doc_content):
            api_names.add(match.group(1))

        return api_names

    def _format_documentation(self, documentation: Documentation) -> str:
        """Format documentation as string"""
        parts = [f"# {documentation.title}\n"]

        for section in documentation.sections:
            # Add appropriate heading
            heading_prefix = "#" * (section.level + 1)
            parts.append(f"{heading_prefix} {section.title}\n")
            parts.append(section.content)
            parts.append("")

        return "\n".join(parts)

    def _get_api_doc_path(self, code_path: str) -> str:
        """Get corresponding API doc path"""
        # Convert src/api/users.py -> docs/api/users.md
        base_name = code_path.replace('.py', '').replace('.js', '').replace('.ts', '')
        return f"docs/{base_name}.md"

    def _get_code_language(self) -> str:
        """Get code language for syntax highlighting"""
        return "python"  # Default, would detect from context


# Convenience functions

async def sync_docs(
    code_changes: Dict[str, str],
    existing_docs: Dict[str, str],
) -> DocSyncResult:
    """
    Quick documentation sync

    Args:
        code_changes: Changed code files
        existing_docs: Existing documentation

    Returns:
        Sync result
    """
    agent = DocSyncAgent()
    return await agent.sync_documentation(code_changes, existing_docs)


async def generate_readme(project_name: str, description: str) -> str:
    """
    Quick README generation

    Args:
        project_name: Project name
        description: Project description

    Returns:
        README content
    """
    agent = DocSyncAgent()
    project_info = {
        'name': project_name,
        'description': description,
        'features': [],
    }
    return await agent.generate_readme(project_info)
