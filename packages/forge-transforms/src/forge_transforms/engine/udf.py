"""
User-Defined Functions (UDFs)

Provides the framework for defining and registering custom functions
that can be used in SQL transforms.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable

import pyarrow as pa


@dataclass
class UDFMetadata:
    """Metadata for a user-defined function.

    Attributes:
        name: The function name.
        description: Human-readable description.
        input_types: List of input Arrow data types.
        return_type: The return Arrow data type.
        is_deterministic: Whether the function is deterministic.
        volatility: Function volatility (immutable, stable, volatile).
    """

    name: str
    description: str = ""
    input_types: list[pa.DataType] = field(default_factory=list)
    return_type: pa.DataType = field(default_factory=lambda: pa.utf8())
    is_deterministic: bool = True
    volatility: str = "immutable"


class UserDefinedFunction(ABC):
    """Abstract base class for user-defined functions.

    Provides the interface for implementing custom scalar and aggregate
    functions that can be registered with the DataFusion engine.

    Example:
        ```python
        class UpperCase(ScalarUDF):
            @property
            def metadata(self) -> UDFMetadata:
                return UDFMetadata(
                    name="upper_case",
                    description="Convert string to uppercase",
                    input_types=[pa.utf8()],
                    return_type=pa.utf8(),
                )

            def evaluate(self, *args: pa.Array) -> pa.Array:
                import pyarrow.compute as pc
                return pc.utf8_upper(args[0])

        engine.register_udf("upper_case", UpperCase())
        ```
    """

    @property
    @abstractmethod
    def metadata(self) -> UDFMetadata:
        """Get the function metadata."""
        ...

    @property
    def name(self) -> str:
        """Get the function name."""
        return self.metadata.name

    @property
    def return_type(self) -> pa.DataType:
        """Get the return type."""
        return self.metadata.return_type


class ScalarUDF(UserDefinedFunction):
    """Base class for scalar user-defined functions.

    Scalar UDFs operate on a single row at a time and return a single value
    per input row.

    Example:
        ```python
        class AddOne(ScalarUDF):
            @property
            def metadata(self) -> UDFMetadata:
                return UDFMetadata(
                    name="add_one",
                    input_types=[pa.int64()],
                    return_type=pa.int64(),
                )

            def evaluate(self, *args: pa.Array) -> pa.Array:
                import pyarrow.compute as pc
                return pc.add(args[0], 1)
        ```
    """

    @abstractmethod
    def evaluate(self, *args: pa.Array) -> pa.Array:
        """Evaluate the function on Arrow arrays.

        Args:
            *args: Input Arrow arrays, one per input column.

        Returns:
            Arrow array with the computed results.
        """
        ...

    def __call__(self, *args: Any) -> Any:
        """Execute the function."""
        return self.evaluate(*args)


class AggregateUDF(UserDefinedFunction):
    """Base class for aggregate user-defined functions.

    Aggregate UDFs operate on multiple rows and produce a single aggregated
    result. They follow an accumulator pattern with create, update, merge,
    and finalize operations.

    Example:
        ```python
        class CustomSum(AggregateUDF):
            @property
            def metadata(self) -> UDFMetadata:
                return UDFMetadata(
                    name="custom_sum",
                    input_types=[pa.float64()],
                    return_type=pa.float64(),
                )

            def create_accumulator(self) -> dict[str, Any]:
                return {"total": 0.0}

            def update(self, acc: dict[str, Any], *args: pa.Array) -> None:
                import pyarrow.compute as pc
                acc["total"] += pc.sum(args[0]).as_py()

            def merge(self, acc1: dict[str, Any], acc2: dict[str, Any]) -> dict[str, Any]:
                return {"total": acc1["total"] + acc2["total"]}

            def finalize(self, acc: dict[str, Any]) -> Any:
                return acc["total"]
        ```
    """

    @abstractmethod
    def create_accumulator(self) -> dict[str, Any]:
        """Create an initial accumulator state.

        Returns:
            Initial accumulator state dictionary.
        """
        ...

    @abstractmethod
    def update(self, accumulator: dict[str, Any], *args: pa.Array) -> None:
        """Update the accumulator with new values.

        Args:
            accumulator: The current accumulator state.
            *args: Input Arrow arrays to aggregate.
        """
        ...

    @abstractmethod
    def merge(
        self,
        accumulator1: dict[str, Any],
        accumulator2: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge two accumulators.

        Used for parallel aggregation where partial results need to be combined.

        Args:
            accumulator1: First accumulator state.
            accumulator2: Second accumulator state.

        Returns:
            Merged accumulator state.
        """
        ...

    @abstractmethod
    def finalize(self, accumulator: dict[str, Any]) -> Any:
        """Finalize the accumulator to produce the result.

        Args:
            accumulator: The final accumulator state.

        Returns:
            The aggregated result value.
        """
        ...

    def __call__(self, *args: Any) -> Any:
        """Execute the aggregation."""
        acc = self.create_accumulator()
        self.update(acc, *args)
        return self.finalize(acc)


class UDFRegistry:
    """Registry for managing user-defined functions.

    Provides a central location for registering, retrieving, and managing
    UDFs that can be used across transform sessions.

    Example:
        ```python
        registry = UDFRegistry()
        registry.register(MyScalarUDF())
        registry.register(MyAggregateUDF())

        udf = registry.get("my_scalar_udf")
        all_scalars = registry.get_scalar_udfs()
        ```
    """

    def __init__(self) -> None:
        """Initialize an empty UDF registry."""
        self._scalar_udfs: dict[str, ScalarUDF] = {}
        self._aggregate_udfs: dict[str, AggregateUDF] = {}

    def register(self, udf: UserDefinedFunction) -> None:
        """Register a UDF.

        Args:
            udf: The UDF to register.

        Raises:
            ValueError: If a UDF with the same name already exists.
        """
        name = udf.name

        if isinstance(udf, AggregateUDF):
            if name in self._aggregate_udfs:
                raise ValueError(f"Aggregate UDF '{name}' already registered")
            self._aggregate_udfs[name] = udf
        elif isinstance(udf, ScalarUDF):
            if name in self._scalar_udfs:
                raise ValueError(f"Scalar UDF '{name}' already registered")
            self._scalar_udfs[name] = udf
        else:
            raise TypeError(f"Unknown UDF type: {type(udf)}")

    def deregister(self, name: str) -> bool:
        """Deregister a UDF by name.

        Args:
            name: The UDF name to deregister.

        Returns:
            True if the UDF was found and removed, False otherwise.
        """
        if name in self._scalar_udfs:
            del self._scalar_udfs[name]
            return True
        if name in self._aggregate_udfs:
            del self._aggregate_udfs[name]
            return True
        return False

    def get(self, name: str) -> UserDefinedFunction | None:
        """Get a UDF by name.

        Args:
            name: The UDF name.

        Returns:
            The UDF if found, None otherwise.
        """
        return self._scalar_udfs.get(name) or self._aggregate_udfs.get(name)

    def get_scalar_udfs(self) -> list[ScalarUDF]:
        """Get all registered scalar UDFs."""
        return list(self._scalar_udfs.values())

    def get_aggregate_udfs(self) -> list[AggregateUDF]:
        """Get all registered aggregate UDFs."""
        return list(self._aggregate_udfs.values())

    def list_names(self) -> list[str]:
        """Get all registered UDF names."""
        return list(self._scalar_udfs.keys()) + list(self._aggregate_udfs.keys())

    def clear(self) -> None:
        """Clear all registered UDFs."""
        self._scalar_udfs.clear()
        self._aggregate_udfs.clear()


def create_scalar_udf(
    name: str,
    func: Callable[..., pa.Array],
    input_types: list[pa.DataType],
    return_type: pa.DataType,
    description: str = "",
) -> ScalarUDF:
    """Factory function to create a scalar UDF from a callable.

    Args:
        name: The function name.
        func: The callable that implements the function.
        input_types: List of input Arrow data types.
        return_type: The return Arrow data type.
        description: Optional description.

    Returns:
        A ScalarUDF instance.

    Example:
        ```python
        def my_double(arr: pa.Array) -> pa.Array:
            import pyarrow.compute as pc
            return pc.multiply(arr, 2)

        udf = create_scalar_udf(
            name="double",
            func=my_double,
            input_types=[pa.int64()],
            return_type=pa.int64(),
        )
        ```
    """

    class FunctionBasedScalarUDF(ScalarUDF):
        @property
        def metadata(self) -> UDFMetadata:
            return UDFMetadata(
                name=name,
                description=description,
                input_types=input_types,
                return_type=return_type,
            )

        def evaluate(self, *args: pa.Array) -> pa.Array:
            return func(*args)

    return FunctionBasedScalarUDF()
