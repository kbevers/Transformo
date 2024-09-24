# Residuals

step 0: Source coordinates
step 1: Helmert transformation
step 2: Helmert estimation
step 3: Target coordinates


## Datasources

```python
...
ds = DataSource(...)

new_coords = op.forward(ds.coordinate_matrix)

new_ds = ds.update_coordinates(new_coords)



```
