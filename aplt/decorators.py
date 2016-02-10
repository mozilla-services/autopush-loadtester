"""Scenario decorators"""


def restart(tries=3):
    """Restarts a scenario `times` amount that uncaught exceptions are
    thrown"""
    def _restart_decorator(f):
        f._retries = tries
        return f
    return _restart_decorator
