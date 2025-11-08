"""
Prompt Compression Utility

Reduces token usage by compressing prompts while preserving
semantic meaning and important information.
"""

import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class PromptCompressor:
    """
    Compress prompts to save tokens and reduce costs.

    Strategies:
    1. Remove redundant whitespace
    2. Abbreviate common programming terms
    3. Remove comments and docstrings (when appropriate)
    4. Truncate long code blocks
    5. Summarize repetitive content
    """

    def __init__(self, aggressive: bool = False):
        """
        Initialize compressor.

        Args:
            aggressive: Use aggressive compression (may lose some context)
        """
        self.aggressive = aggressive

        # Common programming term abbreviations
        self.abbreviations = {
            "function": "fn",
            "parameter": "param",
            "argument": "arg",
            "variable": "var",
            "initialize": "init",
            "configuration": "config",
            "implementation": "impl",
            "documentation": "doc",
            "repository": "repo",
            "directory": "dir",
            "reference": "ref",
            "description": "desc",
            "exception": "exc",
            "attribute": "attr",
            "information": "info",
            "application": "app",
        }

    def compress(self, text: str, preserve_code: bool = True) -> str:
        """
        Compress text to reduce token count.

        Args:
            text: Text to compress
            preserve_code: Whether to preserve code blocks

        Returns:
            Compressed text
        """
        if not text:
            return text

        # Extract and preserve code blocks
        code_blocks = []
        if preserve_code:
            text, code_blocks = self._extract_code_blocks(text)

        # Apply compression strategies
        compressed = text

        # 1. Normalize whitespace
        compressed = self._normalize_whitespace(compressed)

        # 2. Remove redundant punctuation
        compressed = self._remove_redundant_punctuation(compressed)

        # 3. Abbreviate common terms (if aggressive)
        if self.aggressive:
            compressed = self._abbreviate_terms(compressed)

        # 4. Remove filler words
        compressed = self._remove_filler_words(compressed)

        # Restore code blocks (with optional compression)
        if preserve_code:
            compressed = self._restore_code_blocks(compressed, code_blocks, compress_code=self.aggressive)

        return compressed.strip()

    def compress_messages(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Compress a list of messages.

        Args:
            messages: List of message dictionaries
            max_tokens: Optional target maximum tokens

        Returns:
            Compressed messages
        """
        compressed = []

        for msg in messages:
            compressed_msg = msg.copy()

            if "content" in msg and isinstance(msg["content"], str):
                compressed_msg["content"] = self.compress(msg["content"])

            compressed.append(compressed_msg)

        # If still over token limit, apply more aggressive strategies
        if max_tokens:
            from .token_counter import count_messages_tokens

            current_tokens = count_messages_tokens(compressed)
            if current_tokens > max_tokens:
                compressed = self._truncate_messages(compressed, max_tokens)

        return compressed

    def _extract_code_blocks(self, text: str) -> tuple:
        """Extract code blocks from text."""
        code_blocks = []
        pattern = r"```[\s\S]*?```|`[^`]+`"

        def replace_code(match):
            code_blocks.append(match.group(0))
            return f"__CODE_BLOCK_{len(code_blocks) - 1}__"

        text_without_code = re.sub(pattern, replace_code, text)
        return text_without_code, code_blocks

    def _restore_code_blocks(
        self,
        text: str,
        code_blocks: List[str],
        compress_code: bool = False
    ) -> str:
        """Restore code blocks to text."""
        for i, block in enumerate(code_blocks):
            if compress_code:
                block = self._compress_code_block(block)
            text = text.replace(f"__CODE_BLOCK_{i}__", block)
        return text

    def _compress_code_block(self, code: str) -> str:
        """Compress a code block."""
        # Remove comments
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)

        # Remove docstrings
        code = re.sub(r'"""[\s\S]*?"""', '', code)
        code = re.sub(r"'''[\s\S]*?'''", '', code)

        # Remove empty lines
        code = re.sub(r'\n\s*\n', '\n', code)

        # Normalize whitespace
        lines = code.split('\n')
        compressed_lines = []
        for line in lines:
            # Preserve minimal indentation
            stripped = line.lstrip()
            if stripped:
                indent = len(line) - len(stripped)
                # Reduce indentation to minimal
                compressed_lines.append(' ' * (indent // 2) + stripped)

        return '\n'.join(compressed_lines)

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text."""
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)

        # Replace multiple newlines with double newline
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

        # Remove trailing whitespace
        text = '\n'.join(line.rstrip() for line in text.split('\n'))

        return text

    def _remove_redundant_punctuation(self, text: str) -> str:
        """Remove redundant punctuation."""
        # Remove multiple exclamation/question marks
        text = re.sub(r'[!?]{2,}', '!', text)

        # Remove ellipsis variants
        text = re.sub(r'\.{3,}', '...', text)

        return text

    def _abbreviate_terms(self, text: str) -> str:
        """Abbreviate common terms."""
        for full, abbr in self.abbreviations.items():
            # Only replace whole words
            pattern = r'\b' + full + r'\b'
            text = re.sub(pattern, abbr, text, flags=re.IGNORECASE)

        return text

    def _remove_filler_words(self, text: str) -> str:
        """Remove common filler words that don't add meaning."""
        filler_words = [
            r'\bactually\b',
            r'\bbasically\b',
            r'\bjust\b',
            r'\bsimply\b',
            r'\breally\b',
            r'\bvery\b',
            r'\bquite\b',
            r'\bsomewhat\b',
            r'\bkind of\b',
            r'\bsort of\b',
        ]

        for filler in filler_words:
            text = re.sub(filler, '', text, flags=re.IGNORECASE)

        # Clean up double spaces created by removal
        text = re.sub(r' +', ' ', text)

        return text

    def _truncate_messages(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int
    ) -> List[Dict[str, Any]]:
        """Truncate messages to fit within token limit."""
        from .token_counter import count_messages_tokens

        # Keep system message and most recent messages
        if not messages:
            return messages

        # Always keep system message if present
        system_messages = [m for m in messages if m.get("role") == "system"]
        other_messages = [m for m in messages if m.get("role") != "system"]

        # Start with system messages
        result = system_messages.copy()
        current_tokens = count_messages_tokens(result)

        # Add messages from most recent backwards
        for msg in reversed(other_messages):
            msg_tokens = count_messages_tokens([msg])

            if current_tokens + msg_tokens <= max_tokens:
                result.insert(len(system_messages), msg)
                current_tokens += msg_tokens
            else:
                # Truncate this message's content to fit
                available_tokens = max_tokens - current_tokens
                if available_tokens > 100:  # Only if we have reasonable space
                    truncated_msg = self._truncate_message_content(msg, available_tokens)
                    result.insert(len(system_messages), truncated_msg)
                break

        return result

    def _truncate_message_content(
        self,
        message: Dict[str, Any],
        max_tokens: int
    ) -> Dict[str, Any]:
        """Truncate a message's content to fit token limit."""
        truncated = message.copy()
        content = message.get("content", "")

        # Approximate: 4 chars per token
        max_chars = max_tokens * 4

        if len(content) > max_chars:
            truncated["content"] = content[:max_chars] + "... [truncated]"

        return truncated

    def calculate_compression_ratio(self, original: str, compressed: str) -> float:
        """
        Calculate compression ratio.

        Args:
            original: Original text
            compressed: Compressed text

        Returns:
            Compression ratio (0-1, higher is better)
        """
        if not original:
            return 1.0

        return 1.0 - (len(compressed) / len(original))


# Global instance
_compressor = PromptCompressor()
_aggressive_compressor = PromptCompressor(aggressive=True)


# Convenience functions
def compress(text: str, preserve_code: bool = True, aggressive: bool = False) -> str:
    """Compress text."""
    compressor = _aggressive_compressor if aggressive else _compressor
    return compressor.compress(text, preserve_code)


def compress_messages(
    messages: List[Dict[str, Any]],
    max_tokens: Optional[int] = None,
    aggressive: bool = False
) -> List[Dict[str, Any]]:
    """Compress messages."""
    compressor = _aggressive_compressor if aggressive else _compressor
    return compressor.compress_messages(messages, max_tokens)


def calculate_savings(original: str, compressed: str) -> Dict[str, Any]:
    """Calculate compression savings."""
    from .token_counter import count_tokens

    original_tokens = count_tokens(original)
    compressed_tokens = count_tokens(compressed)

    return {
        "original_tokens": original_tokens,
        "compressed_tokens": compressed_tokens,
        "tokens_saved": original_tokens - compressed_tokens,
        "compression_ratio": 1.0 - (compressed_tokens / original_tokens) if original_tokens > 0 else 0,
    }
