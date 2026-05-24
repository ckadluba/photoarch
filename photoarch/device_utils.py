"""
Utilities for detecting and selecting the optimal device for running models.
Supports Apple Metal Performance Shaders (MPS), CUDA, and CPU fallback.
"""

import logging
import torch
from typing import Literal

logger = logging.getLogger(__name__)


def get_optimal_device(prefer_mps: bool = True) -> tuple[str, torch.dtype]:
    """
    Detect and return the optimal device for running AI models.
    
    Attempts in order:
    1. Metal Performance Shaders (MPS) on Apple Silicon (if prefer_mps=True)
    2. CUDA if available
    3. CPU as fallback
    
    Returns:
        Tuple of (device_str, dtype) where:
        - device_str: "mps", "cuda", or "cpu"
        - dtype: torch.float32 for MPS/CPU, torch.float16 for CUDA
    """
    
    # Try MPS first (Apple Silicon)
    if prefer_mps and torch.backends.mps.is_available():
        logger.info("Using Apple Metal Performance Shaders (MPS) for GPU acceleration")
        return "mps", torch.float32
    
    # Try CUDA
    if torch.cuda.is_available():
        logger.info(f"Using CUDA device: {torch.cuda.get_device_name(0)}")
        return "cuda", torch.float16
    
    # Fallback to CPU
    logger.info("No GPU detected. Using CPU for inference (will be slower)")
    return "cpu", torch.float32


def get_device_dtype(device: str) -> torch.dtype:
    """
    Get the recommended dtype for a given device.
    
    Args:
        device: Device name ("mps", "cuda", or "cpu")
        
    Returns:
        torch.dtype: Recommended dtype for the device
    """
    if device == "cuda":
        return torch.float16
    return torch.float32
