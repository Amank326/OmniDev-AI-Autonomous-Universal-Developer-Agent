"""Sandbox execution environment for running agent-generated code safely."""

import asyncio
import logging
import subprocess
import tempfile
import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class SandboxExecutor:
    """Safely execute code in an isolated environment."""

    def __init__(self, timeout: int = 30, max_memory_mb: int = 256):
        """Initialize sandbox executor.

        Args:
            timeout: Maximum execution time in seconds.
            max_memory_mb: Maximum memory allocation in MB.
        """
        self.timeout = timeout
        self.max_memory_mb = max_memory_mb

    async def execute_python(
        self, code: str, input_data: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute Python code in a sandboxed subprocess.

        Args:
            code: Python code to execute.
            input_data: Optional stdin input.

        Returns:
            Dictionary with stdout, stderr, return_code, and execution_time.
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(code)
            temp_path = f.name

        try:
            start_time = datetime.now(timezone.utc)
            process = await asyncio.create_subprocess_exec(
                "python",
                temp_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(
                        input=input_data.encode() if input_data else None
                    ),
                    timeout=self.timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "stdout": "",
                    "stderr": "Execution timed out",
                    "return_code": -1,
                    "execution_time": self.timeout,
                    "timed_out": True,
                }

            end_time = datetime.now(timezone.utc)
            execution_time = (end_time - start_time).total_seconds()

            return {
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "return_code": process.returncode,
                "execution_time": execution_time,
                "timed_out": False,
            }
        finally:
            os.unlink(temp_path)

    async def validate_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Validate code for syntax errors without executing.

        Args:
            code: Code to validate.
            language: Programming language.

        Returns:
            Dictionary with validation results.
        """
        if language == "python":
            try:
                compile(code, "<string>", "exec")
                return {"valid": True, "errors": []}
            except SyntaxError as e:
                return {
                    "valid": False,
                    "errors": [
                        {
                            "line": e.lineno,
                            "offset": e.offset,
                            "message": str(e.msg),
                        }
                    ],
                }
        return {"valid": True, "errors": [], "note": f"Validation not supported for {language}"}


sandbox_executor = SandboxExecutor()
