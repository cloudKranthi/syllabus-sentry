import inspect
from typing import Any, Type, get_type_hints

from sqlalchemy.ext.asyncio import AsyncSession


class AutoContainer:

    def __init__(self, db: AsyncSession):
        self._instances: dict[Type, Any] = {
            AsyncSession: db,
        }

        self.db = db

    def get(self, cls: Type) -> Any:
        return self._get_or_create(cls)

    def _get_or_create(self, cls: Type) -> Any:

        # Already created → reuse same instance
        if cls in self._instances:
            return self._instances[cls]

        # Inspect constructor
        signature = inspect.signature(cls.__init__)
        type_hints = get_type_hints(cls.__init__)

        kwargs = {}

        for param_name, param in signature.parameters.items():

            # Skip self
            if param_name == "self":
                continue

            # If parameter has a default value,
            # let Python use that default.
            if param.default is not inspect.Parameter.empty:
                continue

            param_type = type_hints.get(param_name)

            if param_type is None:
                raise TypeError(
                    f"Cannot resolve dependency "
                    f"{cls.__name__}.{param_name}: "
                    f"missing type annotation"
                )

            # AsyncSession
            if param_type is AsyncSession:
                kwargs[param_name] = self.db

            # Already-created dependency
            elif param_type in self._instances:
                kwargs[param_name] = self._instances[param_type]

            # Another class → recursively create it
            elif inspect.isclass(param_type):
                kwargs[param_name] = self._get_or_create(param_type)

            else:
                raise TypeError(
                    f"Cannot resolve dependency "
                    f"{cls.__name__}.{param_name}: "
                    f"{param_type}"
                )

        # Create object
        instance = cls(**kwargs)

        # Cache it
        self._instances[cls] = instance

        return instance