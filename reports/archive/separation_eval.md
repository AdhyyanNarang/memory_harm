# Fixed-Binary Separation Evaluation

- Bootstrap reps: `5000`
- Permutation reps: `5000`

## Avoidance
### vulnerable
- Episodes: summary=10 none=10
- S_drift: `-0.250`  CI95=`[-1.100, 0.617]`  p=`0.6081`
- S_last: `0.533`  CI95=`[-0.050, 1.133]`  p=`0.1142`
- Strong quantitative pass: `False`

### not_vulnerable
- Episodes: summary=10 none=10
- S_drift: `-1.083`  CI95=`[-1.883, -0.283]`  p=`0.0228`
- S_last: `-0.083`  CI95=`[-0.533, 0.400]`  p=`0.8042`
- Strong quantitative pass: `False`

## Vulnerable Quant Pass (both scenarios): `False`