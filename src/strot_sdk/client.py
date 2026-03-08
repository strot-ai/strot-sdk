"""
STROT SDK — HTTP Client

Central HTTP client for all STROT API calls.
Handles authentication, error handling, and response parsing.
"""
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests

from .config import StrotConfig
from .types import DeployResult, ExecutionResult, QueryResult, Resource

logger = logging.getLogger(__name__)


class StrotAPIError(Exception):
    """Error from the STROT API."""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class StrotClient:
    """HTTP client for the STROT platform API.

    All API calls are org-scoped. The org slug is read from the
    credentials profile and prepended to API paths automatically.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        org: Optional[str] = None,
        profile: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_base_delay: float = 1.0,
    ):
        self.config = StrotConfig(url=url, api_key=api_key, profile=profile)
        self.org = org or self.config.org
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay
        self._session = requests.Session()
        if self.config.api_key:
            self._session.headers["Authorization"] = f"Key {self.config.api_key}"
        self._session.headers["Content-Type"] = "application/json"
        self._session.headers["User-Agent"] = "strot-sdk/0.1.0"

    def _url(self, path: str) -> str:
        """Build full org-scoped URL from path.

        If org slug is set, paths like /api/queries become
        /<org_slug>/api/queries for multi-tenant routing.
        """
        base = self.config.url.rstrip("/")
        if self.org:
            return f"{base}/{self.org}{path}"
        return f"{base}{path}"

    def _request(self, method: str, path: str, **kwargs) -> Any:
        """Make an authenticated API request with retry for transient errors."""
        import time

        self.config.validate()
        url = self._url(path)
        kwargs.setdefault("timeout", self.timeout)

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = self._session.request(method, url, **kwargs)
            except requests.ConnectionError as e:
                last_error = StrotAPIError(
                    f"Cannot connect to STROT instance at {self.config.url}"
                )
                if attempt < self.max_retries:
                    delay = self.retry_base_delay * (2 ** attempt)
                    logger.warning(
                        "Connection error, retrying in %.1fs (%d/%d)...",
                        delay, attempt + 1, self.max_retries,
                    )
                    time.sleep(delay)
                    continue
                raise last_error
            except requests.Timeout as e:
                last_error = StrotAPIError(
                    f"Request timed out after {self.timeout}s"
                )
                if attempt < self.max_retries:
                    delay = self.retry_base_delay * (2 ** attempt)
                    logger.warning(
                        "Timeout, retrying in %.1fs (%d/%d)...",
                        delay, attempt + 1, self.max_retries,
                    )
                    time.sleep(delay)
                    continue
                raise last_error

            # 5xx — retry
            if resp.status_code >= 500 and attempt < self.max_retries:
                delay = self.retry_base_delay * (2 ** attempt)
                logger.warning(
                    "Server error %d, retrying in %.1fs (%d/%d)...",
                    resp.status_code, delay, attempt + 1, self.max_retries,
                )
                time.sleep(delay)
                continue

            # 4xx — don't retry, raise immediately
            if resp.status_code >= 400:
                try:
                    body = resp.json()
                    msg = body.get("message", body.get("error", resp.text))
                except Exception:
                    body = None
                    msg = resp.text
                raise StrotAPIError(msg, status_code=resp.status_code, response=body)

            # Success
            if resp.status_code == 204:
                return None

            try:
                return resp.json()
            except Exception:
                return resp.text

        # Should not reach here, but just in case
        raise last_error or StrotAPIError("Request failed after retries")

    def get(self, path: str, **kwargs) -> Any:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, data: Any = None, **kwargs) -> Any:
        return self._request("POST", path, json=data, **kwargs)

    def put(self, path: str, data: Any = None, **kwargs) -> Any:
        return self._request("PUT", path, json=data, **kwargs)

    def delete(self, path: str, **kwargs) -> Any:
        return self._request("DELETE", path, **kwargs)

    # ── Resource Discovery ──────────────────────────────────────

    def list_queries(self) -> List[Resource]:
        """List all saved queries."""
        data = self.get("/api/queries")
        results = data.get("results", data) if isinstance(data, dict) else data
        return [
            Resource(
                id=q["id"],
                name=q.get("name", ""),
                type="query",
                description=q.get("description", ""),
                metadata={
                    "data_source_id": q.get("data_source_id"),
                    "query": q.get("query", ""),
                    "schedule": q.get("schedule"),
                },
            )
            for q in results
        ]

    def list_data_sources(self) -> List[Resource]:
        """List all data sources."""
        data = self.get("/api/data_sources")
        return [
            Resource(
                id=ds["id"],
                name=ds.get("name", ""),
                type="data_source",
                description=ds.get("type", ""),
                metadata={
                    "type": ds.get("type"),
                    "syntax": ds.get("syntax", "sql"),
                },
            )
            for ds in data
        ]

    def list_tools(self) -> List[Resource]:
        """List all Arena code functions (tools/agents)."""
        data = self.get("/api/arena/code-functions")
        items = data.get("results", data) if isinstance(data, dict) else data
        return [
            Resource(
                id=t["id"],
                name=t.get("name", ""),
                type=t.get("function_type", "tool"),
                description=t.get("description", ""),
                metadata={
                    "function_type": t.get("function_type"),
                    "language": t.get("language", "python"),
                    "category": t.get("category", "custom"),
                },
            )
            for t in items
        ]

    # ── Query Execution ─────────────────────────────────────────

    def execute_query(self, query_id: int, params: Optional[Dict] = None) -> QueryResult:
        """Execute a saved query by ID."""
        data = self.post("/api/query_results", data={
            "query_id": query_id,
            "parameters": params or {},
            "max_age": 0,
        })
        # Handle async job polling
        if "job" in data:
            return self._poll_job(data["job"]["id"])
        return self._parse_query_result(data)

    def execute_sql(
        self,
        data_source_id: int,
        sql: str,
        params: Optional[Dict] = None,
    ) -> QueryResult:
        """Execute raw SQL against a data source."""
        data = self.post("/api/query_results", data={
            "data_source_id": data_source_id,
            "query": sql,
            "parameters": params or {},
            "max_age": 0,
        })
        if "job" in data:
            return self._poll_job(data["job"]["id"])
        return self._parse_query_result(data)

    def _poll_job(self, job_id: str, max_wait: int = 120) -> QueryResult:
        """Poll a query job until completion."""
        import time
        start = time.time()
        while time.time() - start < max_wait:
            data = self.get(f"/api/jobs/{job_id}")
            status = data.get("job", {}).get("status")
            if status in (3, 4):  # FINISHED or FAILED
                qr_id = data.get("job", {}).get("query_result_id")
                if qr_id:
                    result = self.get(f"/api/query_results/{qr_id}")
                    return self._parse_query_result(result)
                error = data.get("job", {}).get("error", "Query execution failed")
                raise StrotAPIError(error)
            time.sleep(1)
        raise StrotAPIError(f"Query timed out after {max_wait}s")

    @staticmethod
    def _parse_query_result(data: Dict) -> QueryResult:
        """Parse API response into QueryResult."""
        qr = data.get("query_result", data)
        qr_data = qr.get("data", {})
        return QueryResult(
            columns=qr_data.get("columns", []),
            rows=qr_data.get("rows", []),
            row_count=len(qr_data.get("rows", [])),
            query_id=qr.get("query_id"),
            data_source_id=qr.get("data_source_id"),
        )

    # ── Code Execution ──────────────────────────────────────────

    def run_code(
        self,
        code: str,
        language: str = "python",
        params: Optional[Dict] = None,
        file_contents: Optional[Dict[str, str]] = None,
    ) -> ExecutionResult:
        """Execute code on the STROT instance."""
        data = self.post("/api/arena/run-code", data={
            "code": code,
            "language": language,
            "params": params or {},
            "file_contents": file_contents or {},
        })
        return ExecutionResult(
            success=data.get("success", False),
            data=data.get("result"),
            error=data.get("error"),
            execution_time_ms=data.get("execution_time_ms"),
        )

    # ── LLM Proxy ───────────────────────────────────────────────

    def llm_complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        """Generate an LLM completion via STROT proxy."""
        data = self.post("/api/arena/llm/complete", data={
            "prompt": prompt,
            "system_prompt": system_prompt,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
        })
        return data.get("content", "")

    def llm_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        """Send a chat conversation to the LLM via STROT proxy."""
        data = self.post("/api/arena/llm/chat", data={
            "messages": messages,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
        })
        return data.get("content", "")

    def llm_transform(
        self,
        data_input: Any,
        instruction: str,
        output_format: str = "json",
    ) -> Any:
        """Transform data using LLM via STROT proxy."""
        data = self.post("/api/arena/llm/transform", data={
            "data": data_input,
            "instruction": instruction,
            "output_format": output_format,
        })
        return data.get("result")

    def llm_classify(self, text: str, categories: List[str]) -> str:
        """Classify text into one of the given categories."""
        data = self.post("/api/arena/llm/classify", data={
            "text": text,
            "categories": categories,
        })
        return data.get("category", "")

    def llm_extract(self, text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured data from text."""
        data = self.post("/api/arena/llm/extract", data={
            "text": text,
            "schema": schema,
        })
        return data.get("result", {})

    # ── Destinations ────────────────────────────────────────────

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: Optional[str] = None,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send an email via STROT."""
        return self.post("/api/arena/destinations/email", data={
            "to": to,
            "subject": subject,
            "body": body,
            "html": html,
            "cc": cc,
            "bcc": bcc,
        })

    def send_slack(
        self,
        channel: str,
        message: str,
        blocks: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Send a Slack message via STROT."""
        return self.post("/api/arena/destinations/slack", data={
            "channel": channel,
            "message": message,
            "blocks": blocks,
        })

    def send_webhook(
        self,
        url: str,
        data_payload: Any,
        headers: Optional[Dict[str, str]] = None,
        method: str = "POST",
    ) -> Dict[str, Any]:
        """Send a webhook request via STROT."""
        return self.post("/api/arena/destinations/webhook", data={
            "url": url,
            "data": data_payload,
            "headers": headers,
            "method": method,
        })

    # ── Deploy ──────────────────────────────────────────────────

    def deploy_function(
        self,
        name: str,
        code: str,
        function_type: str = "tool",
        description: str = "",
        category: str = "custom",
        language: str = "python",
        file_contents: Optional[Dict[str, str]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> DeployResult:
        """Deploy a function/agent to the STROT instance."""
        # Check if function with this name already exists
        existing = self._find_function_by_name(name)

        payload = {
            "name": name,
            "code": code,
            "function_type": function_type,
            "description": description,
            "category": category,
            "language": language,
            "file_contents": file_contents or {},
        }
        if config:
            payload["config"] = config

        if existing:
            # Update existing
            data = self.put(f"/api/arena/code-functions/{existing['id']}", data=payload)
            return DeployResult(
                success=True,
                id=existing["id"],
                name=name,
                url=f"{self.config.url}/arena/{existing['id']}",
                action="updated",
            )
        else:
            # Create new
            data = self.post("/api/arena/code-functions", data=payload)
            new_id = data.get("id")
            return DeployResult(
                success=True,
                id=new_id,
                name=name,
                url=f"{self.config.url}/arena/{new_id}" if new_id else None,
                action="created",
            )

    def _find_function_by_name(self, name: str) -> Optional[Dict]:
        """Find an existing code function by name."""
        try:
            data = self.get("/api/arena/code-functions")
            items = data.get("results", data) if isinstance(data, dict) else data
            for item in items:
                if item.get("name") == name:
                    return item
        except Exception:
            pass
        return None

    def deploy_orchestration(
        self,
        name: str,
        dsl: Dict[str, Any],
        description: str = "",
    ) -> DeployResult:
        """Deploy a Cortex pipeline (orchestration) to the STROT instance."""
        existing = self._find_orchestration_by_name(name)

        payload = {
            "name": name,
            "description": description,
            "dsl": dsl,
        }

        if existing:
            data = self.put(f"/api/cortex/orchestrations/{existing['id']}", data=payload)
            return DeployResult(
                success=True,
                id=existing["id"],
                name=name,
                url=f"{self.config.url}/cortex/{existing['id']}",
                action="updated",
            )
        else:
            data = self.post("/api/cortex/orchestrations", data=payload)
            new_id = data.get("id")
            return DeployResult(
                success=True,
                id=new_id,
                name=name,
                url=f"{self.config.url}/cortex/{new_id}" if new_id else None,
                action="created",
            )

    def _find_orchestration_by_name(self, name: str) -> Optional[Dict]:
        """Find an existing orchestration by name."""
        try:
            data = self.get("/api/cortex/orchestrations")
            items = data.get("results", data) if isinstance(data, dict) else data
            for item in items:
                if item.get("name") == name:
                    return item
        except Exception:
            pass
        return None

    def deploy_page(
        self,
        name: str,
        layout: Dict[str, Any],
        description: str = "",
    ) -> DeployResult:
        """Deploy a page/dashboard to the STROT instance."""
        existing = self._find_page_by_name(name)

        payload = {
            "name": name,
            "description": description,
            "layout": layout,
            "type": layout.get("type", "dashboard"),
        }

        if existing:
            data = self.put(f"/api/pages/{existing['id']}", data=payload)
            return DeployResult(
                success=True,
                id=existing["id"],
                name=name,
                url=f"{self.config.url}/pages/{existing['id']}",
                action="updated",
            )
        else:
            data = self.post("/api/pages", data=payload)
            new_id = data.get("id")
            return DeployResult(
                success=True,
                id=new_id,
                name=name,
                url=f"{self.config.url}/pages/{new_id}" if new_id else None,
                action="created",
            )

    def _find_page_by_name(self, name: str) -> Optional[Dict]:
        """Find an existing page by name."""
        try:
            data = self.get("/api/pages")
            items = data.get("results", data) if isinstance(data, dict) else data
            for item in items:
                if item.get("name") == name:
                    return item
        except Exception:
            pass
        return None

    # ── Auth (used by CLI) ──────────────────────────────────────

    def whoami(self) -> Dict[str, Any]:
        """Get current user and org info via the org-scoped session endpoint."""
        data = self.get("/api/session")
        user = data.get("user", {})
        return {
            "id": user.get("id"),
            "name": user.get("name", ""),
            "email": user.get("email", ""),
            "permissions": user.get("permissions", []),
            "org": {
                "slug": data.get("org_slug", self.org or ""),
            },
        }

    def check_auth(self) -> bool:
        """Check if authentication is valid."""
        try:
            self.whoami()
            return True
        except Exception:
            return False
