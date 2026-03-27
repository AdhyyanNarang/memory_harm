# Fixed-Binary Separation Evaluation

- Bootstrap reps: `5000`
- Permutation reps: `5000`

## Therapy
### vulnerable
- Episodes: summary=12 none=12
- S_drift: `-0.667`  CI95=`[-3.042, 1.583]`  p=`0.6209`
- S_last: `0.667`  CI95=`[-1.125, 2.417]`  p=`0.5209`
- Strong quantitative pass: `False`

### not_vulnerable
- Episodes: summary=12 none=12
- S_drift: `0.500`  CI95=`[0.083, 0.917]`  p=`0.0490`
- S_last: `0.708`  CI95=`[0.333, 1.125]`  p=`0.0044`
- Strong quantitative pass: `True`

## Vulnerable Quant Pass (both scenarios): `False`