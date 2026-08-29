"""Conversor de fluxogramas a partir de imagens e PDFs."""

from .models import BBox, Detection, Edge, FlowchartGraph, Node
from .pipeline import ConversionConfig, ConversionResult, FlowchartConverter
from .rendering import PublicationOptions, PublicationResult, publish_graph

__all__ = [
    "BBox",
    "ConversionConfig",
    "ConversionResult",
    "Detection",
    "Edge",
    "FlowchartConverter",
    "FlowchartGraph",
    "Node",
    "PublicationOptions",
    "PublicationResult",
    "publish_graph",
]

__version__ = "0.1.0"
