import os
import sys
import time
from fastapi import FastAPI, Response, status
from fastapi.responses import PlainTextResponse

# --- Configuration and Environment Setup ---

# Read the file path from an environment variable set by run.sh
FILE_PATH = os.environ.get("FILE_TO_SERVE")

if not FILE_PATH or not os.path.exists(FILE_PATH):
    print(
        f"🚨 FATAL ERROR: File not found at path specified by FILE_TO_SERVE.",
        file=sys.stderr,
    )
    sys.exit(1)


# --- Core Logic: The File Indexer ---

class LineIndexer:
    """
    Efficiently indexes a large file to provide random access to its lines.
    
    This class scans the file once upon initialization to build an in-memory
    index of the starting byte offset of each line. This allows for very fast
    O(1) lookup of any line's position, avoiding slow, sequential reads for
    each request.
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.offsets = []
        self._build_index()

    def _build_index(self):
        """
        Scans the file and records the starting byte offset of each line.
        This is a one-time cost at server startup.
        """
        print(f"⏳ Indexing '{self.filepath}'. This may take a moment for large files...")
        start_time = time.time()
        # Open in binary mode ('rb') for accurate byte offsets with tell()
        with open(self.filepath, "rb") as f:
            offset = 0
            while True:
                self.offsets.append(offset)
                line = f.readline()
                if not line:
                    # Reached end of file
                    break
                offset = f.tell()
        
        end_time = time.time()
        print(
            f"✅ Indexing complete. Found {self.line_count():,} lines in "
            f"{end_time - start_time:.2f} seconds."
        )

    def line_count(self) -> int:
        """Returns the total number of lines in the file."""
        return len(self.offsets)

    def get_line(self, line_index: int) -> str | None:
        """
        Retrieves a specific line by its index using the pre-built offset map.
        Returns the line text or None if the index is out of bounds.
        """
        if not 0 <= line_index < self.line_count():
            return None

        with open(self.filepath, "r", encoding="ascii") as f:
            # seek() is a highly efficient OS-level operation
            f.seek(self.offsets[line_index])
            line = f.readline()
            # Remove the trailing newline character for clean output
            return line.rstrip('\n')

# --- FastAPI Application Setup ---

# Create the indexer instance once when the application starts.
# This global instance will be shared across all requests.
indexer = LineIndexer(FILE_PATH)

app = FastAPI(
    title="Efficient Line Server",
    description="A REST server to serve lines from a text file efficiently.",
)

@app.get(
    "/lines/{line_index}",
    response_class=PlainTextResponse,
    responses={
        200: {"description": "The requested line text.", "content": {"text/plain": {}}},
        413: {"description": "Line index is out of the file's bounds."},
    },
)
def serve_line(line_index: int, response: Response):
    """
    Retrieves a specific line from the file.
    
    - **line_index**: The 0-based index of the line to retrieve.
    """
    # FastAPI automatically validates that line_index is an integer.
    # We subtract 1 because the spec implies 1-based indexing for users,
    # while our system uses 0-based indexing. If the prompt implies 0-based,
    # this subtraction should be removed. Assuming 0-based for implementation.
    
    line = indexer.get_line(line_index)

    if line is None:
        # Per specification, return 413 if the line is beyond the end of the file.
        # A 404 Not Found would also be a conventional choice.
        response.status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        return f"Error: Line index {line_index} is out of bounds. File has {indexer.line_count()} lines (0-indexed)."
    
    return line

@app.get("/", include_in_schema=False)
def root():
    return {
        "message": "Welcome to the Line Server!",
        "file_being_served": FILE_PATH,
        "total_lines": indexer.line_count(),
        "api_docs": "/docs"
    }
