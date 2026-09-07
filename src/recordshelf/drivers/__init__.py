from ..models import ControllerConfig
from .base import Driver, NullDriver
from .opc import OpcDriver
from .wled import WledDriver


def make_driver(cfg: ControllerConfig) -> Driver:
    if cfg.type == "wled":
        return WledDriver(cfg)
    if cfg.type == "opc":
        return OpcDriver(cfg)
    return NullDriver(cfg)


__all__ = ["Driver", "NullDriver", "OpcDriver", "WledDriver", "make_driver"]
