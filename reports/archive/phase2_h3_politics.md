# Fixed-Binary Separation Evaluation

- Bootstrap reps: `5000`
- Permutation reps: `5000`

## Politics
### vulnerable
- Episodes: summary=12 none=12
- S_drift: `0.458`  CI95=`[-1.250, 2.084]`  p=`0.6415`
- S_last: `1.000`  CI95=`[-0.542, 2.500]`  p=`0.2507`
- Strong quantitative pass: `False`

### not_vulnerable
- Episodes: summary=12 none=12
- S_drift: `1.125`  CI95=`[0.458, 1.875]`  p=`0.0062`
- S_last: `0.792`  CI95=`[0.292, 1.333]`  p=`0.0110`
- Strong quantitative pass: `True`

## Vulnerable Quant Pass (both scenarios): `False`