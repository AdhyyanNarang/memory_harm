# Fixed-Binary Separation Evaluation

- Bootstrap reps: `5000`
- Permutation reps: `5000`

## Therapy
### vulnerable
- Episodes: summary=12 none=12
- S_drift: `-0.625`  CI95=`[-2.333, 1.042]`  p=`0.5265`
- S_last: `0.625`  CI95=`[-0.667, 1.876]`  p=`0.3951`
- Strong quantitative pass: `False`

### not_vulnerable
- Episodes: summary=12 none=12
- S_drift: `0.375`  CI95=`[0.042, 0.708]`  p=`0.0726`
- S_last: `0.375`  CI95=`[0.042, 0.708]`  p=`0.0704`
- Strong quantitative pass: `False`

## Vulnerable Quant Pass (both scenarios): `False`