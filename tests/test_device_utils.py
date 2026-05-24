import torch
from photoarch.device_utils import get_optimal_device, get_device_dtype


class TestDeviceUtils:
    """Tests for device detection and selection utilities."""
    
    def test_get_optimal_device_returns_tuple(self):
        """Test that get_optimal_device returns a tuple of (str, torch.dtype)."""
        device, dtype = get_optimal_device()
        assert isinstance(device, str)
        assert isinstance(dtype, torch.dtype)
    
    def test_get_optimal_device_valid_device(self):
        """Test that get_optimal_device returns a valid device."""
        device, dtype = get_optimal_device()
        assert device in ["mps", "cuda", "cpu"]
    
    def test_get_optimal_device_mps_preferred(self):
        """Test that MPS is preferred when available (on Apple Silicon)."""
        device, dtype = get_optimal_device(prefer_mps=True)
        if torch.backends.mps.is_available():
            assert device == "mps"
            assert dtype == torch.float32
    
    def test_get_optimal_device_mps_skipped_when_not_preferred(self):
        """Test that MPS is skipped when prefer_mps=False."""
        device, dtype = get_optimal_device(prefer_mps=False)
        # Should return cuda or cpu (not mps)
        assert device in ["cuda", "cpu"]
    
    def test_get_optimal_device_cuda_fallback(self):
        """Test CUDA fallback when MPS is not preferred and available."""
        # This test will only be meaningful on CUDA systems
        device, dtype = get_optimal_device(prefer_mps=False)
        if torch.cuda.is_available():
            assert device == "cuda"
            assert dtype == torch.float16
    
    def test_get_optimal_device_cpu_fallback(self):
        """Test CPU is returned when no GPU is available."""
        # If we reach here and get "cpu", float32 should be returned
        device, dtype = get_optimal_device()
        if device == "cpu":
            assert dtype == torch.float32
    
    def test_get_device_dtype_cuda(self):
        """Test that CUDA returns float16."""
        dtype = get_device_dtype("cuda")
        assert dtype == torch.float16
    
    def test_get_device_dtype_cpu(self):
        """Test that CPU returns float32."""
        dtype = get_device_dtype("cpu")
        assert dtype == torch.float32
    
    def test_get_device_dtype_mps(self):
        """Test that MPS returns float32."""
        dtype = get_device_dtype("mps")
        assert dtype == torch.float32
    
    def test_get_device_dtype_consistency(self):
        """Test consistency between get_optimal_device and get_device_dtype."""
        device, optimal_dtype = get_optimal_device()
        manual_dtype = get_device_dtype(device)
        assert optimal_dtype == manual_dtype
