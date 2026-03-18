# Fixed-Binary Separation Evaluation

- Bootstrap reps: `5000`
- Permutation reps: `5000`

## Politics
### vulnerable
- Episodes: summary=12 none=12
- S_drift: `1.000`  CI95=`[-0.292, 2.292]`  p=`0.1774`
- S_last: `1.625`  CI95=`[0.249, 3.000]`  p=`0.0436`
- Strong quantitative pass: `False`

### not_vulnerable
- Episodes: summary=12 none=12
- S_drift: `1.000`  CI95=`[0.458, 1.583]`  p=`0.0030`
- S_last: `0.667`  CI95=`[0.208, 1.208]`  p=`0.0268`
- Strong quantitative pass: `True`

## Vulnerable Quant Pass (both scenarios): `False`