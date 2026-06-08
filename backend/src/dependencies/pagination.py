from fastapi import Query


class PaginationParams:
    """Dependency injection helper for pagination and sorting queries."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number (1-indexed)"),
        limit: int = Query(10, ge=1, le=100, description="Number of results per page"),
        sort_by: str = Query("created_at", description="Field to sort results by"),
        sort_order: str = Query(
            "desc",
            pattern="^(asc|desc)$",
            description="Sort direction: 'asc' or 'desc'",
        ),
    ):
        self.page = page
        self.limit = limit
        self.sort_by = sort_by
        self.sort_order = sort_order

    @property
    def offset(self) -> int:
        """Calculate row offset for SQL queries."""
        return (self.page - 1) * self.limit
