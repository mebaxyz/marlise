"""
Health check and monitoring endpoints
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class DeepHealthResponse(BaseModel):
    """Deep health check response for entire service chain"""
    healthy: bool
    services: Dict[str, bool]
    timestamp: str
    error: str | None = None


@router.get("/api/health")
async def api_health():
    """Lightweight API health endpoint for the web client dev server to probe.

    This endpoint does not call session_manager; it simply reports that the
    adapter process is alive and able to service simple requests.
    """
    return {"service": "client_interface", "status": "ok"}


@router.get("/health/deep", response_model=DeepHealthResponse)
async def deep_health_check(request: Request):
    """
    Deep health check - verify entire service chain
    
    Tests communication through all layers:
    - Client Interface (this service)
    - Session Manager (via ZMQ)
    - Modhost Bridge (via session manager)
    - mod-host (via bridge)
    """
    results = {
        "client_interface": True,  # We're running if we got here
        "session_manager": False,
        "bridge": False,
        "mod_host": False,
    }
    error_message = None
    
    zmq_client = getattr(request.app.state, "zmq_client", None)
    
    if not zmq_client:
        error_message = "ZMQ client not available"
        return DeepHealthResponse(
            healthy=False,
            services=results,
            timestamp=datetime.now().isoformat(),
            error=error_message
        )
    
    try:
        # Test session manager with short timeout
        resp = await asyncio.wait_for(
            zmq_client.call("session_manager", "health_check", timeout=2.0),
            timeout=3.0
        )
        
        if isinstance(resp, dict):
            results["session_manager"] = resp.get("success", False) or resp.get("healthy", False)
            
            # Check bridge status from session manager response
            if resp.get("bridge_connected"):
                results["bridge"] = True
                
            # Check mod-host status from session manager response
            if resp.get("mod_host_connected"):
                results["mod_host"] = True
                
    except asyncio.TimeoutError:
        error_message = "Session manager health check timed out"
        logger.warning(error_message)
    except Exception as e:
        error_message = f"Health check error: {str(e)}"
        logger.exception("Error during deep health check: %s", e)
    
    # Overall health is true only if all critical services are up
    overall_healthy = all([
        results["client_interface"],
        results["session_manager"],
        results["bridge"],
    ])
    
    return DeepHealthResponse(
        healthy=overall_healthy,
        services=results,
        timestamp=datetime.now().isoformat(),
        error=error_message
    )


@router.get("/api/metrics")
async def get_metrics(request: Request):
    """
    Get service metrics for monitoring
    
    Returns metrics including:
    - Request counts
    - Error rates  
    - Resource usage
    """
    zmq_client = getattr(request.app.state, "zmq_client", None)
    
    metrics = {
        "client_interface": {
            "status": "up",
            "zmq_connected": zmq_client.is_connected() if zmq_client else False,
        }
    }
    
    # Try to get metrics from session manager
    if zmq_client:
        try:
            resp = await asyncio.wait_for(
                zmq_client.call("session_manager", "get_metrics", timeout=2.0),
                timeout=3.0
            )
            if isinstance(resp, dict):
                metrics["session_manager"] = resp
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning("Failed to get session manager metrics: %s", e)
            metrics["session_manager"] = {"error": str(e)}
    
    return metrics
