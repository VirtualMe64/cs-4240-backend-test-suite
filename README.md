# CS 4240 Project 2 Test Suite
This repository helps run solutions for CS 4240 project 2 against a range of tests, as well as making it simple to add more.
## Instructions
1. Add all project files (including `run.sh` and `build.sh`) to `src`
2. Run `python3 test.py` from a unix system with SPIM installed. If needed, add the `-b` flag to build the code before running tests.
3. Read results from `logs`

## Adding Tests
Additional tests can be added by creating a new folder in `tests`

Tests must contain exactly one `.ir` file to be compiled and any number of pairs of `.in` and `.out` files