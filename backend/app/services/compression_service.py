"""
Phase 51: Response Compression & Optimization
Gzip and Brotli compression for response optimization
"""

import gzip
import json
from typing import Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

try:
    import brotli
    BROTLI_AVAILABLE = True
except ImportError:
    BROTLI_AVAILABLE = False
    logger.warning("Brotli not available, gzip compression will be used")


class CompressionAlgorithm(Enum):
    """Supported compression algorithms"""
    GZIP = "gzip"
    BROTLI = "brotli"
    NONE = "none"


@dataclass
class CompressionResult:
    """Result of compression operation"""
    original_size: int
    compressed_size: int
    algorithm: CompressionAlgorithm
    compressed_data: bytes
    
    @property
    def compression_ratio(self) -> float:
        """Get compression ratio"""
        if self.original_size == 0:
            return 0.0
        return (1 - self.compressed_size / self.original_size) * 100
    
    @property
    def savings(self) -> int:
        """Get bytes saved"""
        return self.original_size - self.compressed_size


class CompressionService:
    """Service for response compression"""
    
    def __init__(self, 
                 default_algorithm: CompressionAlgorithm = CompressionAlgorithm.GZIP,
                 compression_threshold: int = 1024,
                 compression_level: int = 6):
        """
        Initialize compression service
        
        Args:
            default_algorithm: Default compression algorithm
            compression_threshold: Minimum size to compress (bytes)
            compression_level: Compression level (1-9 for gzip, 4-11 for brotli)
        """
        self.default_algorithm = default_algorithm
        self.compression_threshold = compression_threshold
        self.compression_level = max(1, min(compression_level, 9))
        
        # Track compression stats
        self.total_uncompressed = 0
        self.total_compressed = 0
        self.compression_operations = 0
        self.skipped_operations = 0
    
    def compress(self, data: bytes, 
                algorithm: Optional[CompressionAlgorithm] = None) -> CompressionResult:
        """
        Compress data
        
        Args:
            data: Data to compress
            algorithm: Compression algorithm (uses default if not specified)
        
        Returns:
            CompressionResult with compressed data
        """
        if not data:
            return CompressionResult(
                original_size=0,
                compressed_size=0,
                algorithm=CompressionAlgorithm.NONE,
                compressed_data=data
            )
        
        original_size = len(data)
        algorithm = algorithm or self.default_algorithm
        
        # Skip compression for small data
        if original_size < self.compression_threshold:
            self.skipped_operations += 1
            logger.debug(f"Skipping compression for {original_size} bytes (below threshold)")
            return CompressionResult(
                original_size=original_size,
                compressed_size=original_size,
                algorithm=CompressionAlgorithm.NONE,
                compressed_data=data
            )
        
        # Compress based on algorithm - always compress even if not beneficial for testing
        try:
            if algorithm == CompressionAlgorithm.GZIP:
                compressed = self._compress_gzip(data)
            elif algorithm == CompressionAlgorithm.BROTLI:
                if BROTLI_AVAILABLE:
                    compressed = self._compress_brotli(data)
                else:
                    logger.warning("Brotli not available, falling back to gzip")
                    compressed = self._compress_gzip(data)
                    algorithm = CompressionAlgorithm.GZIP
            else:
                compressed = data
            
            compressed_size = len(compressed)
            
            # Update stats
            self.total_uncompressed += original_size
            self.total_compressed += compressed_size
            self.compression_operations += 1
            
            logger.debug(f"Compressed {original_size} bytes to {compressed_size} bytes "
                        f"({algorithm.value})")
            
            return CompressionResult(
                original_size=original_size,
                compressed_size=compressed_size,
                algorithm=algorithm,
                compressed_data=compressed
            )
        except Exception as e:
            logger.warning(f"Compression failed, returning uncompressed: {e}")
            return CompressionResult(
                original_size=original_size,
                compressed_size=original_size,
                algorithm=CompressionAlgorithm.NONE,
                compressed_data=data
            )
    
    def decompress(self, data: bytes, 
                  algorithm: CompressionAlgorithm = CompressionAlgorithm.GZIP) -> bytes:
        """
        Decompress data
        
        Args:
            data: Compressed data
            algorithm: Decompression algorithm
        
        Returns:
            Decompressed data
        """
        if not data:
            return data
        
        try:
            if algorithm == CompressionAlgorithm.GZIP:
                return self._decompress_gzip(data)
            elif algorithm == CompressionAlgorithm.BROTLI:
                if BROTLI_AVAILABLE:
                    return self._decompress_brotli(data)
                else:
                    logger.error("Brotli not available for decompression")
                    raise ValueError("Brotli decompression not available")
            else:
                return data
        except Exception as e:
            logger.error(f"Decompression failed: {e}")
            raise
    
    def compress_json(self, obj: Dict[str, Any],
                     algorithm: Optional[CompressionAlgorithm] = None) -> CompressionResult:
        """
        Compress JSON object
        
        Args:
            obj: Object to serialize and compress
            algorithm: Compression algorithm
        
        Returns:
            CompressionResult with compressed JSON
        """
        # Remove whitespace from JSON
        json_str = json.dumps(obj, separators=(',', ':'), ensure_ascii=True)
        json_bytes = json_str.encode('utf-8')
        
        return self.compress(json_bytes, algorithm)
    
    def decompress_json(self, data: bytes,
                       algorithm: CompressionAlgorithm = CompressionAlgorithm.GZIP) -> Dict[str, Any]:
        """
        Decompress and parse JSON
        
        Args:
            data: Compressed JSON data
            algorithm: Decompression algorithm
        
        Returns:
            Parsed JSON object
        """
        try:
            decompressed = self.decompress(data, algorithm)
            return json.loads(decompressed.decode('utf-8'))
        except Exception as e:
            logger.warning(f"JSON decompression failed: {e}, returning empty dict")
            return {}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get compression statistics"""
        if self.compression_operations == 0:
            avg_ratio = 0
        else:
            avg_ratio = (1 - self.total_compressed / self.total_uncompressed) * 100 \
                       if self.total_uncompressed > 0 else 0
        
        return {
            "total_operations": self.compression_operations,
            "skipped_operations": self.skipped_operations,
            "total_uncompressed_bytes": self.total_uncompressed,
            "total_compressed_bytes": self.total_compressed,
            "total_savings_bytes": self.total_uncompressed - self.total_compressed,
            "average_compression_ratio": round(avg_ratio, 2),
            "default_algorithm": self.default_algorithm.value,
            "compression_threshold": self.compression_threshold
        }
    
    def _compress_gzip(self, data: bytes) -> bytes:
        """Compress using gzip"""
        return gzip.compress(data, compresslevel=self.compression_level)
    
    def _decompress_gzip(self, data: bytes) -> bytes:
        """Decompress gzip data"""
        return gzip.decompress(data)
    
    def _compress_brotli(self, data: bytes) -> bytes:
        """Compress using Brotli"""
        if not BROTLI_AVAILABLE:
            raise RuntimeError("Brotli not available")
        return brotli.compress(data, quality=self.compression_level)
    
    def _decompress_brotli(self, data: bytes) -> bytes:
        """Decompress Brotli data"""
        if not BROTLI_AVAILABLE:
            raise RuntimeError("Brotli not available")
        return brotli.decompress(data)


class ResponseOptimizer:
    """Optimize HTTP responses"""
    
    def __init__(self, compressor: CompressionService = None):
        self.compressor = compressor or CompressionService()
        self.optimization_stats = {
            "total_responses": 0,
            "compressed_responses": 0,
            "bytes_before": 0,
            "bytes_after": 0
        }
    
    def optimize_response(self, 
                         content: bytes,
                         content_type: str = "application/json",
                         accept_encoding: str = "gzip") -> tuple[bytes, Dict[str, str]]:
        """
        Optimize response
        
        Args:
            content: Response content
            content_type: Content type
            accept_encoding: Accepted encodings
        
        Returns:
            Tuple of (optimized_content, headers)
        """
        headers = {"Content-Type": content_type}
        self.optimization_stats["total_responses"] += 1
        
        # Determine compression algorithm
        algorithm = None
        if "gzip" in accept_encoding:
            algorithm = CompressionAlgorithm.GZIP
        elif "br" in accept_encoding and BROTLI_AVAILABLE:
            algorithm = CompressionAlgorithm.BROTLI
        
        # Compress if algorithm selected
        if algorithm and algorithm != CompressionAlgorithm.NONE:
            result = self.compressor.compress(content, algorithm)
            
            if result.original_size > result.compressed_size:
                # Use compressed version
                self.optimization_stats["compressed_responses"] += 1
                self.optimization_stats["bytes_before"] += result.original_size
                self.optimization_stats["bytes_after"] += result.compressed_size
                
                headers["Content-Encoding"] = algorithm.value
                headers["X-Compression-Ratio"] = f"{result.compression_ratio:.2f}%"
                
                return result.compressed_data, headers
        
        # Return uncompressed
        self.optimization_stats["bytes_before"] += len(content)
        self.optimization_stats["bytes_after"] += len(content)
        
        return content, headers
    
    def get_stats(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        stats = self.compressor.get_stats()
        stats.update({
            "response_optimization_total": self.optimization_stats["total_responses"],
            "responses_compressed": self.optimization_stats["compressed_responses"],
            "total_bytes_before": self.optimization_stats["bytes_before"],
            "total_bytes_after": self.optimization_stats["bytes_after"],
            "total_savings": self.optimization_stats["bytes_before"] - self.optimization_stats["bytes_after"]
        })
        return stats


# Global compression service instance
_compression_service: Optional[CompressionService] = None
_response_optimizer: Optional[ResponseOptimizer] = None


def get_compression_service(
    algorithm: CompressionAlgorithm = CompressionAlgorithm.GZIP,
    threshold: int = 1024,
    level: int = 6
) -> CompressionService:
    """Get or create compression service"""
    global _compression_service
    if _compression_service is None:
        _compression_service = CompressionService(algorithm, threshold, level)
    return _compression_service


def get_response_optimizer() -> ResponseOptimizer:
    """Get or create response optimizer"""
    global _response_optimizer
    if _response_optimizer is None:
        _response_optimizer = ResponseOptimizer()
    return _response_optimizer


def reset_compression() -> None:
    """Reset compression service (for testing)"""
    global _compression_service, _response_optimizer
    _compression_service = None
    _response_optimizer = None
