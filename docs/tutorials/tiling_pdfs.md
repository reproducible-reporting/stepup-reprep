# Tiling PDFs

StepUp RepRep contains a tool to tile panels (individual PDF figures) into one composite PDF figure.

The tiling code builds on the script protocol in StepUp Core,
which is explained in the [Getting Started tutorials](TODO) of StepUp Core.

This tutorial provides a simple example, which you can use as a starting point.
For a more advanced example, check out the [`tild_pdf` test case](TODO) in the unit test suite of StepUp RepRep.


## Example

Create a `tile.py` script with the following code:

```python
{% include 'tutorials/tile_pdf/tile.py' %}
```

Next, create a script `plan.py` as follows:

```python
{% include 'tutorials/tile_pdf/plan.py' %}
```

For this example to work, you also need to create four SVG figures of the same size: `triangle.svg`, `square.svg`, `pentagon.svg` and  `hexagon.svg`.

To run the example, make the scripts executable and run StepUp:

```bash
chmod +x plan.py tile.py
stepup -n -w1
```

You should see the following terminal output:

```
{% include 'tutorials/tile_pdf/stdout.txt' %}
```

This is the PNG conversion of the resulting PDF figure:

![figure](tile_pdf/figure.png)
