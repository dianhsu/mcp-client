import os
import subprocess

from loguru import logger
from mcp.server.fastmcp import FastMCP


def register_script(mcp: FastMCP):
    """
    Registers a tool to run scripts in the appropriate shell based on the operating system.
    """
    cwd = os.getcwd()

    @mcp.tool()
    def set_cwd(path: str) -> str:
        """
        Sets the current working directory for running scripts.
        """
        nonlocal cwd
        if os.path.isdir(path):
            cwd = path
            return f"Workspace set to {cwd}"
        else:
            return f"Error: {path} is not a valid directory"

    @mcp.tool()
    def run_command(code: str) -> str:
        """
        Runs a script in the appropriate shell and returns the output.
        """
        if os.name == "nt":
            os.environ["COMSPEC"] = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
        # Run the PowerShell command
        process = subprocess.Popen(code, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=cwd, shell=True)

        # Get the output and error messages
        output, error = process.communicate()
        if process.returncode != 0:
            if "is not recognized as the name of a cmdlet, function, script file, or operable program." in error:
                process = subprocess.Popen(
                    code, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=cwd, shell=False
                )
                output, error = process.communicate()
                if process.returncode != 0:
                    return f"Error: {error}"
                return output
            return f"Error: {error}"

        return output
