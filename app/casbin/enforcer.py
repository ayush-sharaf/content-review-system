import os

import casbin

_BASE = os.path.dirname(__file__)
MODEL_PATH = os.path.join(_BASE, "model.conf")
POLICY_PATH = os.path.join(_BASE, "policy.csv")


def build_enforcer():
    """Load the casbin enforcer from the model and policy files."""
    return casbin.Enforcer(MODEL_PATH, POLICY_PATH)
