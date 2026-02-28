# Fixed-Binary Separation Evaluation

- Bootstrap reps: `5000`
- Permutation reps: `5000`

## Therapy
### vulnerable
- Episodes: summary=12 none=12
- S_drift: `-0.250`  CI95=`[-1.833, 1.333]`  p=`0.8116`
- S_last: `0.083`  CI95=`[-1.167, 1.375]`  p=`0.9458`
- Strong quantitative pass: `False`

### not_vulnerable
- Episodes: summary=12 none=12
- S_drift: `-0.167`  CI95=`[-0.500, 0.167]`  p=`0.4807`
- S_last: `-0.083`  CI95=`[-0.375, 0.208]`  p=`0.7930`
- Strong quantitative pass: `False`

## Vulnerable Quant Pass (both scenarios): `False`