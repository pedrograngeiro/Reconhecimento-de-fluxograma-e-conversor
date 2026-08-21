"""Conversor de fluxogramas a partir de imagens e PDFs."""

from .models import BBox, Detection, Edge, FlowchartGraph, Node
from .pipeline import ConversionConfig, ConversionResult, FlowchartConverter

__all__ = [
    "BBox",
    "ConversionConfig",
    "ConversionResult",
    "Detection",
    "Edge",
    "FlowchartConverter",
    "FlowchartGraph",
    "Node",
]

__version__ = "0.1.0"
