"""
Example with the pyvista 3d plotting library
============================================

Mkdocs-Gallery supports examples made with the
[pyvista library](https://docs.pyvista.org/version/stable/). 

In order to use pyvista, the [`conf_script` of the project](../../index.md#b-advanced) should include the
following lines to adequatly configure pyvista:

```python
import pyvista

pyvista.BUILDING_GALLERY = True
pyvista.OFF_SCREEN = True

conf = {
    ...,
    "image_scrapers": ("pyvista", ...),
}
```
"""
import pyvista as pv

# %%
# You can display an animation as a gif

sphere = pv.Sphere()
pl = pv.Plotter()
pl.enable_hidden_line_removal()
pl.add_mesh(sphere, show_edges=True, color="tan")
# for this example
pl.open_gif("animation.gif", fps=10)
# alternatively, to disable movie generation:
# pl.show(auto_close=False, interactive=False)
delta_x = 0.05
center = sphere.center
for angle in range(0, 360, 10):

    rot = sphere.rotate_x(angle, point=(0, 0, 0), inplace=False)

    pl.clear_actors()
    pl.add_mesh(rot, show_edges=True, color="tan")
    pl.write_frame()


pl.show()

# %%
# or simply show a static plot

sphere = pv.Sphere()
pl = pv.Plotter()
pl.add_mesh(sphere, show_edges=True, color="tan")
pl.show()
