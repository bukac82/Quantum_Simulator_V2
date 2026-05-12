"""
FastAPI dependencies for the Quantum Computing API
"""

from fastapi import Depends
from config import job_storage, active_simulators

def get_job_storage():
    """Dependency to get job storage"""
    return job_storage

def get_active_simulators():
    """Dependency to get active simulators storage"""
    return active_simulators