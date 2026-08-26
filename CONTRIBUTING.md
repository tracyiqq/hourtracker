# Working on Hours Ledger

## Before you commit

```bash
cd src && python test_holidays.py
```

Seven checks, no dependencies. The most important one reproduces all 85 officially gazetted
holiday dates from the algorithm — if that breaks, the 323 projected dates cannot be trusted
either.

## Never edit index.html directly

It is generated. Edit `src/app_template.html`, then:

```bash
cd src && python build_app.py
```

The test suite fails if `index.html` has drifted from what the source builds, which catches a
hand-edit before it reaches a commit.

## Changing the rules

The calculation lives in one function, `compute()` in `src/app_template.html`. The order of
operations is deliberate and documented in the README — base hours, then the target percentage,
then every deduction. Changing that order changes what people owe, so update the README in the
same commit.

## Adding a gazetted year

When Hong Kong publishes a new year's holidays:

1. Move that year's rows from `PROJECTED` in `holidays_projected.py` into `GAZETTED` in
   `build_app.py`, correcting any date or name against gov.hk.
2. Rebuild and run the tests.
3. Note the correction in the README changelog if a projected date turned out wrong — that is
   useful evidence about how much to trust the remaining projections.

## Extending past 2046

Regenerate the projections with a wider range (see the README), rebuild, run the tests.
