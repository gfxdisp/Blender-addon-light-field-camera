# Light Field Rendering Blender Plugin

This is a blender plugin to help you synthesize render light field. In effect, you are allow to render a grid of camera positions. 

This addon is usable for Blender 2.8+

## Installation

To install the plugin, you should go to the [Github](https://github.com/gfxdisp/Blender-addon-light-field-camera) page and click **Download Zip** to download the page.

![./images/Untitled%201.png](./images/Untitled%201.png)

Then open blender and select Edit/Preference → Add-ons, click "Install.." and select the zip file to install. Finally, click the box **Render:Light Field Camera**.

![./images/Untitled%201.png](./images/Untitled%201.png)

![./images/Untitled%202.png](./images/Untitled%202.png)

## Usage

### Enable Light Field Rendering

If you wish to render with a light field camera, you should first select a camera object in Layout Mode (Make sure it is selected)

![./images/Untitled%203.png](./images/Untitled%203.png)

Then choose the **Object Data Properties** panel, you will see a **Light Field** section, to enable the light field rendering, click the checkbox.

![./images/Untitled%204.png](./images/Untitled%204.png)

### Rendering & Parameters

Now you are able to render the light field with "Render LightField" Button. Which in effect renders with the camera at a grid of positions. 

Here are four parameters

- **cols/rows**: the size of the camera grid, how many rows and columns are there in the camera grid. For example, if you want to render a light field of size 5x5, modify both to 5.
- **base x/base y**: the distance between two neighbouring camera position measured in meters (blender's unit)

The results will be generated 

### Tricks

When rendering, press `esc` to interrupt rendering.

When the light field is enabled of a certain camera, there is a rectangle outline associate with the camera shown in the 3D view. The size of the camera bound the range of the camera grid.


### Using in script

You can also use this as script.

For each camera, there is an additional lightfield attribute. You can specify its `num_rows` `num_cols` `base_x` `base_y`. To render the light field, simply call `bpy.ops.render.lightfield()`. 

```python
import bpy
import numpy as np

def render(camera):
    """
        cam is the camera object
        """
        lf = camera.lightfield
        lf.enabled = True
        lf.num_rows = ... # input number of rows
        lf.num_cols = ... # input number of columns
        lf.base_x = ... # base x
    lf.base_y = ... # base y
        bpy.ops.render.lightfield()
```
