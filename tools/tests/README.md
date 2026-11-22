Extra harness sections. Each `test_<name>.py` defines `check(seed, load_addon)`:
`lua = load_addon()` gives a fresh copy of the addon (logged in) in the lupa mock, with the
same globals as tools/test_harness.py's TEST code. Assert on failure and print one
"<name> section: all checks passed" line at the end. tools/test_harness.py runs them all.
