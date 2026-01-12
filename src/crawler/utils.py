"""
Utility functions for crawler module.
"""
import random


# Common User-Agents for rotating
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


def get_random_user_agent() -> str:
    """Return a random User-Agent string."""
    return random.choice(USER_AGENTS)


def get_proxy() -> dict | None:
    """
    Get proxy configuration if available.
    
    Returns:
        Proxy dict or None if no proxy configured
    """
    # TODO: Implement proxy rotation
    return None


def save_checkpoint(state: dict, filepath: str) -> None:
    """
    Save crawler state for resume functionality.
    
    Args:
        state: Current crawler state
        filepath: Path to save checkpoint
    """
    # TODO: Implement checkpoint saving
    pass


def load_checkpoint(filepath: str) -> dict | None:
    """
    Load crawler state from checkpoint.
    
    Args:
        filepath: Path to checkpoint file
        
    Returns:
        Saved state dict or None
    """
    # TODO: Implement checkpoint loading
    pass
