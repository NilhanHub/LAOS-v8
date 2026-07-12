# Test policy

Required layers include unit, integration, end-to-end, adversarial, concurrency, migration, interruption/recovery, filesystem/path, malicious archive, tamper, clean-install, extracted-release, and real-agent evaluation tests where applicable.

Every confirmed defect receives an executable regression before it is marked fixed. Tests must verify side effects and absence of forbidden behaviour, not only return values. A skipped, timed-out, flaky, or unavailable test is not a pass. Hidden verification remains outside builder write authority.
