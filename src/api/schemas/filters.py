"""Pydantic schemas for filters module."""

from pydantic import BaseModel, Field


class FilterStatus(BaseModel):
    """Status of a single filter."""

    enabled: bool = Field(..., description="Whether the filter is currently enabled")
    description: str = Field(..., description="Human-readable description of the filter")
    details: dict = Field(
        default_factory=dict,
        description="Additional filter-specific details (e.g., MACD state, indicators)",
    )


class FiltersResponse(BaseModel):
    """Response containing all filters' status."""

    filters: dict[str, FilterStatus] = Field(
        ..., description="Dictionary of filter name to FilterStatus"
    )
    all_enabled: bool = Field(..., description="Whether all filters are enabled")
    any_enabled: bool = Field(..., description="Whether any filter is enabled")
    total_count: int = Field(..., description="Total number of registered filters")
    enabled_count: int = Field(..., description="Number of currently enabled filters")


class ToggleFilterRequest(BaseModel):
    """Request to toggle a filter on/off."""

    enabled: bool = Field(..., description="True to enable filter, False to disable")


class ToggleFilterResponse(BaseModel):
    """Response after toggling a filter."""

    filter: str = Field(..., description="Name of the filter that was toggled")
    enabled: bool = Field(..., description="New enabled state of the filter")
    message: str = Field(..., description="Success message")
    details: dict = Field(default_factory=dict, description="Additional filter-specific details")


class BulkFilterResponse(BaseModel):
    """Response after bulk enable/disable operation."""

    message: str = Field(..., description="Success message")
    filters: list[str] = Field(..., description="List of affected filter names")


class MACDTriggerRequest(BaseModel):
    """Request to control MACD trigger."""

    activated: bool = Field(..., description="True to activate MACD trigger, False to deactivate")


class MACDTriggerResponse(BaseModel):
    """Response after controlling MACD trigger."""

    message: str = Field(..., description="Success message")
    activated: bool = Field(..., description="New activation state")
    persisted: bool = Field(..., description="Whether state was persisted to database")
    details: dict = Field(default_factory=dict, description="Current MACD state and indicators")
