"""
QuantumSim2Q: A 2-qubit quantum simulator library using PyTorch

This library provides a simple interface for simulating 2-qubit quantum systems
with visualization capabilities.
"""

from simul import QuantumSimulator2Q
from .classes.plotter import QuantumPlotter
from .classes.gates import QuantumGates
from .classes.utils import QuantumUtils

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

__all__ = [
    "QuantumSimulator2Q",
    "QuantumPlotter", 
    "QuantumGates",
    "QuantumUtils"
]