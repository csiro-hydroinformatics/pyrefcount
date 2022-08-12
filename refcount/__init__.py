try:
    # New format
    # > Python3.7 ish
    from importlib.metadata import version # type: ignore
    __version__ = version("refcount")
except:
    # Older format
    # Older backport version
    try:
        from importlib_metadata import version # type: ignore
        __version__ = version("refcount")
    except:
        # Can't work out how to import version - set to Unknown
        __version__ = "Unknown - import error"
