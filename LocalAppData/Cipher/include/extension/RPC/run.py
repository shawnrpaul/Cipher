from .rpc import RPC


def run(*args, **kwargs) -> RPC:
    return RPC(*args, **kwargs)
