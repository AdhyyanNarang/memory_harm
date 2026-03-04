#!/usr/bin/env python3
"""Convenience script to run experiments."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.sim import main

if __name__ == "__main__":
    main()
