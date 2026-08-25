#!/usr/bin/env python3
"""
CLI for GI Bleed Urgent Triage Agent.
Provides GBS, Rockall, AIMS65, and combined triage scoring.
"""
import sys
from gibleed_sentinel import main

if __name__ == "__main__":
    sys.exit(main())
