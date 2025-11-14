"""
Minimal stub module to satisfy langchain_core's debug checks.

The real LangChain package is not required for this project because we use
langchain-core directly. However, langchain_core.globals.get_debug imports
`langchain` to read the `debug` attribute.  Creating this lightweight stub
prevents AttributeError without pulling in the entire LangChain dependency.
"""

debug = False
verbose = False

__all__ = ["debug", "verbose"]

