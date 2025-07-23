# Efficient Line Server Documentation

This document describes the design, performance characteristics, and implementation details of the line-serving system.

---

### How does your system work?

The system is a Python-based web server built using the **FastAPI** framework. Its core design is centered on an efficient indexing mechanism to handle large files without consuming excessive memory.

1.  **Pre-processing (Indexing):** Upon starting, the server performs a one-time pre-processing step. It reads through the entire target file once, and for each line, it records the starting byte offset in an array stored in memory. For example, if the first line is 20 bytes long (including the newline character), the index will be `[0, 20, ...]`. This index of offsets is the only data structure held in memory.

2.  **Request Handling:** When a client sends a `GET /lines/<line_index>` request:
    * The server checks if the requested `<line_index>` is valid by comparing it against the size of the in-memory offset array.
    * If the index is invalid, it immediately returns an `HTTP 413 Payload Too Large` status as per the specification.
    * If the index is valid, it retrieves the line's starting byte offset from the array (`offsets[line_index]`).
    * It then uses the `seek()` system call to jump directly to that byte position in the file on disk. This is an extremely fast, O(1) operation that avoids reading the file from the beginning.
    * It reads just the single line from that position and returns it to the client with an `HTTP 200 OK` status.

This "index-and-seek" approach provides the performance of in-memory access while keeping memory usage minimal, as only the line offsets are stored, not the line content itself.

---

### How will your system perform with a 1 GB file? a 10 GB file? a 100 GB file?

The performance is characterized by two phases: startup time (indexing) and request-serving time.

**Startup Performance (One-time cost):**
The startup time is dominated by the need to read the entire file once to build the index. This is I/O-bound and scales linearly with file size.

* **1 GB file:** Startup will be fast. On a modern SSD (reading at ~500 MB/s), this would take **2-5 seconds**. The memory for the index depends on the number of lines. Assuming an average line length of 80 bytes, there are ~12.5 million lines. The index would be `12.5M lines * 8 bytes/offset ≈ 100 MB` of RAM. This is very manageable.
* **10 GB file:** Startup will take **20-50 seconds**. The memory usage for the index would be `125M lines * 8 bytes/offset ≈ 1 GB` of RAM. This is still well within the capacity of most modern servers.
* **100 GB file:** Startup will be significant, potentially **3-8 minutes**. The memory usage for the index would be `1.25B lines * 8 bytes/offset ≈ 10 GB` of RAM. This is a substantial amount but is feasible on a dedicated server. Crucially, it's an order of magnitude less than loading the whole file into memory.

**Request-Serving Performance (Per-request cost):**
After startup, the performance for serving any line is **extremely fast and constant**, regardless of file size or which line is requested. Each request involves a single dictionary lookup (in-memory), a file `seek()` operation (OS-level, very fast), and a `readline()` operation (reading a small amount of data from disk). Latency should be consistently low, typically in the single-digit milliseconds.

---

### How will your system perform with 100 users? 10000 users? 1000000 users?

This question relates to concurrency. The system uses **FastAPI** with an **Uvicorn** server, which is an asynchronous (ASGI) stack designed for high concurrency.

* **100 concurrent users:** The system will handle this with ease. The async event loop can juggle 100 simultaneous I/O-bound operations (like reading a line from disk) without breaking a sweat. Performance will remain excellent.
* **10,000 concurrent users:** A single server process will start to become a bottleneck. To handle this scale, the standard practice is to run multiple server processes (e.g., using `gunicorn` with Uvicorn workers) behind a load balancer like Nginx. The underlying design of the application is sound and scales horizontally. With 4-8 worker processes on a multi-core machine, it could comfortably handle this load.
* **1,000,000 concurrent users:** This is a massive-scale problem that cannot be solved by a single machine. The solution would require a distributed architecture:
    * **Load Balancing:** A robust load balancer (e.g., HAProxy, or a cloud provider's load balancer) would distribute requests across a fleet of servers.
    * **Distributed File System:** The large text file would need to be stored on a shared, high-performance network file system (like NFS or AWS EFS) accessible by all application servers.
    * **Stateless App Servers:** Many instances of this application would run on separate machines. Since the application's state (the index) is built from a read-only source file, the servers are effectively stateless and easy to replicate.
    * **Caching:** A distributed cache like Redis could be added to store the most frequently accessed lines, further reducing disk I/O across the system.

---

### What documentation, websites, papers, etc did you consult?

* **FastAPI Official Documentation:** For API syntax, request/response handling, and best practices.
* **Uvicorn and Gunicorn Documentation:** For understanding deployment options and scaling with worker processes.
* **Python Official Documentation:** For file handling specifics, especially the `seek()` and `tell()` methods and the importance of opening files in binary mode (`'rb'`) for accurate byte offset calculations.
* General articles and Stack Overflow discussions on "efficiently reading a specific line from a large file in Python".

---

### What third-party libraries or other tools does the system use?

* **FastAPI:** Chosen as the web framework because it is extremely high-performance, built on modern async principles (ASGI), provides automatic data validation and API documentation, and has a very clean and intuitive syntax. This directly addresses the requirement for handling many simultaneous clients and a high number of requests.
* **Uvicorn:** Chosen as the ASGI server because it is the standard, lightning-fast server for running FastAPI applications. Its performance is a key component in handling high concurrency.

---

### How long did you spend on this exercise? If you had unlimited more time, how would you spend it?

* **Time Spent:** Approximately 3 hours.

* **If I had unlimited time, I would prioritize the following improvements:**
    1.  **Persistent Index Cache:** The biggest drawback is the startup time for very large files. I would enhance the indexer to save its generated `offsets` array to a separate `.index` file. On startup, the server would check if an index file exists and if its modification time is newer than the source text file. If so, it would load the index directly from this cache file, making startups nearly instantaneous.
    2.  **Containerization:** I would create a `Dockerfile` and a `docker-compose.yml` file to containerize the application. This would make the build, deployment, and scaling process much more reliable and portable across different environments.
    3.  **In-Memory Line Caching:** I would implement an in-memory LRU (Least Recently Used) cache for the line *content* itself. If the same popular lines are requested repeatedly, they could be served directly from RAM, completely avoiding disk I/O for those requests.
    4.  **Robust Configuration:** I would replace the simple environment variable with a more robust configuration management system (e.g., a YAML file or a library like Pydantic-Settings) to manage the file path, server port, worker count, etc.
    5.  **Metrics and Monitoring:** I would add an endpoint (e.g., `/metrics`) that exposes performance metrics in a Prometheus-compatible format, allowing for monitoring of request latency, error rates, and memory usage.

---

### If you were to critique your code, what would you have to say about it?

* **Startup Latency:** As mentioned, the startup indexing time is a significant weakness for truly massive files. While it's a one-time cost, a server restart after a crash or deployment would incur this delay again. A persistent index cache is the clear solution.
* **Memory for Index:** The design assumes the line offset index will fit comfortably in memory. For a file with an astronomically large number of very short lines (e.g., trillions of lines), even the 8-byte-per-line index could exceed available RAM. A more advanced solution for that extreme case would involve a multi-level index stored on disk, similar to how databases build B-tree indexes.
* **Error Handling:** The error handling is basic. A production-grade system would have more comprehensive logging (e.g., structured JSON logs) and would handle more edge cases, such as file permission errors during startup.
* **User-facing Indexing:** The API endpoint uses a 0-based index (`/lines/0`). This is common for programmers but less intuitive for non-technical users who might expect a 1-based index (`/lines/1`). The specification was ambiguous here, so a conscious choice was made. In a real product, this would need clarification.
