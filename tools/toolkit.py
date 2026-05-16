from typing import Callable, Any
from utils.logger import logger


def _normalize_arguments(kwargs: dict) -> dict:
    """Normaliza argumentos de tool calls mal formados por el modelo"""
    normalized = {}
    for key, value in kwargs.items():
        # Si el valor es un dict con 'description' y 'type', probablemente el modelo
        # está devolviendo el schema en lugar del valor real
        if isinstance(value, dict) and "description" in value and "type" in value:
            normalized[key] = value.get("description", str(value))
            logger.debug(f"Argumento '{key}' normalizado desde schema a valor: '{normalized[key]}'")
        else:
            normalized[key] = value
    return normalized


class Tool:
    def __init__(self, name: str, description: str, parameters: dict, handler: Callable):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler

    def execute(self, **kwargs) -> str:
        try:
            logger.agent_action("TOOL_CALL", f"{self.name} | args: {kwargs}")
            normalized = _normalize_arguments(kwargs)
            result = self.handler(**normalized)
            logger.agent_action("TOOL_RESULT", f"{self.name} | result: {str(result)[:100]}")
            return result if isinstance(result, str) else str(result)
        except Exception as e:
            logger.error(f"Error ejecutando {self.name}: {e}")
            logger.debug(f"Args recibidos: {kwargs}")
            return f"Error: {str(e)}"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


class Toolkit:
    def __init__(self):
        self.tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self.tools[tool.name] = tool
        logger.info(f"Herramienta registrada: {tool.name}")

    def get(self, name: str) -> Tool:
        return self.tools.get(name)

    def get_all_tools(self) -> list:
        return [tool.to_dict() for tool in self.tools.values()]

    def execute(self, tool_name: str, **kwargs) -> str:
        tool = self.get(tool_name)
        if not tool:
            return f"Herramienta no encontrada: {tool_name}"
        return tool.execute(**kwargs)