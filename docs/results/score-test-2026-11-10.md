# Frozen model scored on test (generated 2026-11-10T03:17:35Z)

Model: blend-v1 (market + base rate, logistic) · freeze commit `bb92f3a` · corpus 921 transcripts ≤ 2026-10-14 (sha256 59814170f0db)

**Verdict: INCONCLUSIVE (model better on the point estimate, 95% CI crosses 0)**

| Model | events | markets | Brier model | Brier market | diff | 95% CI | log loss model | log loss market |
|---|---|---|---|---|---|---|---|---|
| frozen blend, test | 60 | 1640 | 0.1614 | 0.1631 | -0.0017 | [-0.0043, +0.0010] | 0.4882 | 0.4918 |
| base alone, test | 60 | 1640 | 0.2336 | 0.1631 | +0.0706 | [+0.0540, +0.0865] | 0.6596 | 0.4918 |

Base alone is reported only; the gate is on the frozen blend.

### Reliability, frozen blend (model | market)

| bin | n model | mean p | freq | n market | mean p | freq |
|---|---|---|---|---|---|---|
| 0.0-0.1 | 256 | 0.050 | 0.070 | 144 | 0.055 | 0.042 |
| 0.1-0.2 | 239 | 0.151 | 0.209 | 208 | 0.153 | 0.168 |
| 0.2-0.3 | 186 | 0.250 | 0.263 | 204 | 0.247 | 0.201 |
| 0.3-0.4 | 104 | 0.346 | 0.298 | 175 | 0.348 | 0.297 |
| 0.4-0.5 | 119 | 0.448 | 0.387 | 127 | 0.446 | 0.323 |
| 0.5-0.6 | 116 | 0.547 | 0.526 | 139 | 0.551 | 0.489 |
| 0.6-0.7 | 138 | 0.643 | 0.565 | 170 | 0.651 | 0.541 |
| 0.7-0.8 | 150 | 0.754 | 0.713 | 152 | 0.747 | 0.743 |
| 0.8-0.9 | 159 | 0.856 | 0.849 | 192 | 0.850 | 0.875 |
| 0.9-1.0 | 173 | 0.944 | 0.960 | 129 | 0.940 | 0.969 |

### By event type, frozen blend

| type | events | markets | Brier model | Brier market |
|---|---|---|---|---|
| address | 2 | 51 | 0.1585 | 0.1430 |
| bilateral | 7 | 143 | 0.2083 | 0.2100 |
| interview | 5 | 120 | 0.1737 | 0.1846 |
| press_conference | 2 | 50 | 0.1523 | 0.1632 |
| rally | 12 | 339 | 0.1821 | 0.1805 |
| remarks | 32 | 937 | 0.1458 | 0.1479 |
