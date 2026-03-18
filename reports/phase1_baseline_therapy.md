# Fixed-Binary Separation Evaluation

- Bootstrap reps: `5000`
- Permutation reps: `5000`

## Therapy
### vulnerable
- Episodes: summary=12 none=12
- S_drift: `-1.625`  CI95=`[-3.500, 0.167]`  p=`0.1222`
- S_last: `0.083`  CI95=`[-1.208, 1.375]`  p=`0.9544`
- Strong quantitative pass: `False`

### not_vulnerable
- Episodes: summary=12 none=12
- S_drift: `0.333`  CI95=`[-0.001, 0.708]`  p=`0.1408`
- S_last: `0.458`  CI95=`[0.125, 0.833]`  p=`0.0324`
- Strong quantitative pass: `False`

## Vulnerable Quant Pass (both scenarios): `False`