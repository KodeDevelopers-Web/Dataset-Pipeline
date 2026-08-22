"""
Language Detection Utility

Automatically detects programming language from code snippets using:
1. File extension hints
2. Keywords and syntax patterns
3. Shebangs (#! declarations)
4. Common library imports

This module provides high-confidence language detection for code samples.
"""

import re
from typing import Optional
from schemas import SUPPORTED_LANGUAGES


# Language-specific keywords for pattern matching
LANGUAGE_KEYWORDS = {
    "python": {
        "keywords": {"def", "import", "from", "class", "if __name__", "async", "await"},
        "patterns": [r"^#!/usr/bin/python", r"^#!/usr/bin/env python"],
    },
    "javascript": {
        "keywords": {"function", "const", "let", "var", "import", "export", "async"},
        "patterns": [r"^#!/usr/bin/node", r"^#!/usr/bin/env node"],
    },
    "typescript": {
        "keywords": {"interface", "type", "enum", "as const", ": string", ": number"},
        "patterns": [r"\.ts\b", r"typescript"],
    },
    "java": {
        "keywords": {"public class", "import java", "void main", "package"},
        "patterns": [r"public\s+class\s+\w+"],
    },
    "csharp": {
        "keywords": {"using", "namespace", "public class", "static void Main"},
        "patterns": [r"using\s+System"],
    },
    "cpp": {
        "keywords": {"#include", "std::", "cout", "cin", "vector", "template"},
        "patterns": [r"#include\s*[<\"]"],
    },
    "c": {
        "keywords": {"#include <stdio.h>", "void main", "malloc", "printf"},
        "patterns": [r"#include\s*[<\"].*\.h[>\"]"],
    },
    "go": {
        "keywords": {"package main", "import", "func", "defer", "go "},
        "patterns": [r"^package main", r"^import\s+[(\"]"],
    },
    "rust": {
        "keywords": {"fn", "use", "let", "mut", "impl", "trait", "cargo"},
        "patterns": [r"fn\s+\w+\s*\("],
    },
    "php": {
        "keywords": {"<?php", "namespace", "use", "function", "$this", "echo"},
        "patterns": [r"<\?php", r"\$\w+"],
    },
    "ruby": {
        "keywords": {"def ", "end", "require", "class ", "attr_accessor"},
        "patterns": [r"^#!/usr/bin/ruby", r"^#!/usr/bin/env ruby"],
    },
    "bash": {
        "keywords": {"#!/bin/bash", "#!/bin/sh", "echo", "if", "for", "while"},
        "patterns": [r"^#!/bin/bash", r"^#!/bin/sh"],
    },
    "sql": {
        "keywords": {"SELECT", "FROM", "WHERE", "INSERT", "UPDATE", "DELETE"},
        "patterns": [r"^\s*SELECT\s+", r"^\s*INSERT\s+INTO"],
    },
    "html": {
        "keywords": {"<!DOCTYPE", "<html", "<head", "<body", "<div"},
        "patterns": [r"<!DOCTYPE", r"<html"],
    },
    "css": {
        "keywords": {".class", "#id", "@media", "@keyframes", "!important"},
        "patterns": [r"\.[\w-]+\s*{", r"#[\w-]+\s*{"],
    },
    "kotlin": {
        "keywords": {"fun", "class", "package", "val", "var", "suspend"},
        "patterns": [r"^package\s+", r"fun\s+\w+\s*\("],
    },
    "swift": {
        "keywords": {"func", "class", "struct", "enum", "protocol", "var", "let"},
        "patterns": [r"import\s+Foundation"],
    },
    "objective-c": {
        "keywords": {"@interface", "@implementation", "@property", "alloc", "init"},
        "patterns": [r"@interface\s+\w+", r"#import\s+[<\"]"],
    },
}

# File extension to language mapping
EXTENSION_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".java": "java",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".go": "go",
    ".rs": "rust",
    ".php": "php",
    ".rb": "ruby",
    ".sh": "bash",
    ".bash": "bash",
    ".sql": "sql",
    ".html": "html",
    ".css": "css",
    ".kt": "kotlin",
    ".swift": "swift",
    ".m": "objective-c",
    ".mm": "objective-c",
    ".scala": "scala",
    ".scala.html": "scala",
    ".pl": "perl",
    ".lua": "lua",
    ".hs": "haskell",
    ".ml": "ocaml",
    ".ex": "elixir",
    ".exs": "elixir",
    ".erl": "erlang",
    ".clj": "clojure",
    ".cljs": "clojure",
    ".fs": "fsharp",
    ".fsx": "fsharp",
    ".r": "r",
    ".jl": "julia",
    ".m": "matlab",
    ".dart": "dart",
    ".s": "assembly",
    ".asm": "assembly",
    ".f": "fortran",
    ".f90": "fortran",
    ".f95": "fortran",
    ".cob": "cobol",
    ".groovy": "groovy",
}


def detect_from_extension(filename: str) -> Optional[str]:
    """
    Detect language from file extension.
    
    Args:
        filename: Name of the file
        
    Returns:
        Language name or None if not detected
    """
    if not filename:
        return None
    
    filename_lower = filename.lower()
    
    # Check exact extensions
    for ext, lang in EXTENSION_MAP.items():
        if filename_lower.endswith(ext):
            return lang
    
    # Check without extension
    if "." in filename:
        _, ext = filename_lower.rsplit(".", 1)
        if ext in ("py", "js", "ts", "java", "cs", "cpp", "c", "go", "rs"):
            return EXTENSION_MAP.get("." + ext)
    
    return None


def detect_from_shebang(code: str) -> Optional[str]:
    """
    Detect language from shebang (#!) line.
    
    Args:
        code: First few lines of code
        
    Returns:
        Language name or None if not detected
    """
    if not code:
        return None
    
    first_line = code.split("\n")[0].lower()
    
    if first_line.startswith("#!"):
        if "python" in first_line:
            return "python"
        if "node" in first_line or "javascript" in first_line:
            return "javascript"
        if "bash" in first_line or "sh" in first_line:
            return "bash"
        if "ruby" in first_line:
            return "ruby"
        if "perl" in first_line:
            return "perl"
    
    return None


def detect_from_keywords(code: str) -> Optional[str]:
    """
    Detect language using keyword patterns.
    
    Args:
        code: Source code
        
    Returns:
        Language name or None if not detected
    """
    if not code:
        return None
    
    code_lower = code.lower()
    code_lines = code.split("\n")
    
    # Score each language based on keyword matches
    scores = {}
    
    for lang, patterns in LANGUAGE_KEYWORDS.items():
        score = 0
        
        # Check keywords
        for keyword in patterns.get("keywords", set()):
            if keyword in code_lower:
                score += 2
        
        # Check regex patterns
        for pattern in patterns.get("patterns", []):
            try:
                if re.search(pattern, code, re.MULTILINE | re.IGNORECASE):
                    score += 3
            except:
                pass
        
        if score > 0:
            scores[lang] = score
    
    # Return language with highest score if threshold met
    if scores:
        best_lang = max(scores, key=scores.get)
        if scores[best_lang] >= 2:
            return best_lang
    
    return None


def detect_language(
    code: str,
    filename: str = "",
    context_hint: str = "",
) -> str:
    """
    Detect programming language from code with multiple strategies.
    
    Uses a priority order:
    1. Shebang line
    2. File extension
    3. Keyword matching
    4. Context hint
    5. Default to "unknown"
    
    Args:
        code: Source code
        filename: Optional filename (for extension detection)
        context_hint: Optional hint about language (e.g., from metadata)
        
    Returns:
        Language name (lowercase) or "unknown" if not detected
    """
    
    # Strategy 1: Shebang
    if code:
        detected = detect_from_shebang(code)
        if detected:
            return detected
    
    # Strategy 2: File extension
    if filename:
        detected = detect_from_extension(filename)
        if detected:
            return detected
    
    # Strategy 3: Keywords
    if code and len(code) > 20:
        detected = detect_from_keywords(code)
        if detected:
            return detected
    
    # Strategy 4: Context hint
    if context_hint:
        hint = context_hint.lower().strip()
        if hint in SUPPORTED_LANGUAGES:
            return hint
    
    return "unknown"


def normalize_language(lang: str) -> str:
    """
    Normalize language name to canonical form.
    
    Handles common aliases and variations.
    
    Args:
        lang: Language name (any case)
        
    Returns:
        Canonical language name (lowercase) or "unknown"
    """
    if not lang:
        return "unknown"
    
    lang_lower = lang.lower().strip()
    
    # Direct match
    if lang_lower in SUPPORTED_LANGUAGES:
        return lang_lower
    
    # Common aliases
    aliases = {
        "py": "python",
        "js": "javascript",
        "ts": "typescript",
        "cs": "csharp",
        "cpp": "cpp",
        "c++": "cpp",
        "cc": "cpp",
        "cxx": "cpp",
        "rb": "ruby",
        "sh": "bash",
        "kts": "kotlin",
        "swift": "swift",
        "m": "objective-c",
        "objc": "objective-c",
        "scala": "scala",
        "pl": "perl",
        "lua": "lua",
        "hs": "haskell",
        "ml": "ocaml",
        "ex": "elixir",
        "erl": "erlang",
        "clj": "clojure",
        "fs": "fsharp",
        "r": "r",
        "jl": "julia",
        "mat": "matlab",
        "dart": "dart",
        "asm": "assembly",
        "f": "fortran",
        "cob": "cobol",
        "groovy": "groovy",
    }
    
    if lang_lower in aliases:
        return aliases[lang_lower]
    
    return "unknown"
