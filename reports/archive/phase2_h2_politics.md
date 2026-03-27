# Fixed-Binary Separation Evaluation

- Bootstrap reps: `5000`
- Permutation reps: `5000`

## Politics
### vulnerable
- Episodes: summary=12 none=12
- S_drift: `-0.333`  CI95=`[-1.833, 1.125]`  p=`0.7137`
- S_last: `0.333`  CI95=`[-1.000, 1.583]`  p=`0.6561`
- Strong quantitative pass: `False`

### not_vulnerable
- Episodes: summary=12 none=12
- S_drift: `0.042`  CI95=`[-0.458, 0.542]`  p=`1.0000`
- S_last: `0.208`  CI95=`[-0.333, 0.750]`  p=`0.5745`
- Strong quantitative pass: `False`

## Vulnerable Quant Pass (both scenarios): `False`