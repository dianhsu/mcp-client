"""
# File: server/main.py
# A simple example of running a FastMCP server
#
"""

import os

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("File Management Server", version="1.0.0")


@mcp.tool()
def list_all_files_and_directories_recursively(path: str) -> str:
    """
    Lists all files and directories recursively from the given path.
    """
    if not os.path.exists(path):
        return f"Error: {path} does not exist"

    result = []

    for root, dirs, files in os.walk(path):
        for name in dirs:
            result.append(os.path.join(root, name))
        for name in files:
            result.append(os.path.join(root, name))

    return "\n".join(result)


@mcp.tool()
def read_file(path: str) -> str:
    """
    Reads a file and returns its content.
    """
    try:
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return f"Error: {path} not found"


@mcp.tool()
def create_directory(path: str) -> str:
    """
    Creates a directory at the specified path.
    """
    try:
        os.makedirs(path, exist_ok=True)
        return f"Directory {path} created successfully"
    except Exception as e:
        return f"Error creating directory {path}: {str(e)}"


@mcp.tool()
def list_directories(path: str) -> str:
    """
    Lists directories in a given path.
    """
    try:
        directories = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
        return "\n".join(directories)
    except FileNotFoundError:
        return f"Error: {path} not found"
    except PermissionError:
        return f"Error: Permission denied for {path}"


@mcp.tool()
def list_files(path: str) -> str:
    """
    Lists files in a directory.
    """
    try:
        files = os.listdir(path)
        return "\n".join(files)
    except FileNotFoundError:
        return f"Error: {path} not found"
    except PermissionError:
        return f"Error: Permission denied for {path}"


@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Writes content to a file."""
    try:
        with open(path, "w", encoding="utf-8") as file:
            file.write(content)
        return f"File {path} written successfully"
    except Exception as e:
        return f"Error writing to {path}: {str(e)}"


# @mcp.tool()
# def set_cwd(path: str) -> str:
#     """
#     Sets the current working directory for running scripts.
#     """
#     global cwd  # pylint: disable=global-statement
#     if os.path.isdir(path):
#         cwd = path
#         return f"Workspace set to {cwd}"
#     else:
#         return f"Error: {path} is not a valid directory"


# @mcp.tool()
# def run_command(code: str) -> str:
#     """
#     Runs a script in the appropriate shell and returns the output.
#     """
#     if os.name == "nt":
#         os.environ["COMSPEC"] = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
#     # Run the PowerShell command
#     process = subprocess.Popen(code, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=cwd, shell=True)

#     # Get the output and error messages
#     output, error = process.communicate()
#     if process.returncode != 0:
#         if "is not recognized as the name of a cmdlet, function, script file, or operable program." in error:
#             process = subprocess.Popen(
#                 code, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=cwd, shell=False
#             )
#             output, error = process.communicate()
#             if process.returncode != 0:
#                 return f"Error: {error}"
#             return output
#         return f"Error: {error}"


def main():
    """Main function to run the FastMCP server with the weather example."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
