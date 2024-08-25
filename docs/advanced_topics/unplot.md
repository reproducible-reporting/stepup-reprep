# Unplot

!!! note "Version history"

    This feature was added to StepUp RepRep 1.4.

Unplot converts plots back into data points.
(It is a sanitized version of [Depix](https://github.com/tovrstra/depix).)


## How to prepare an input SVG file.

1. If the plot is embedded in a PDF, use `pdfimages`
   to extract the figures from the PDF as `.pbm` files.
   Most PDF viewers can easily extract bitmaps from a PDF:
   right-click on the image and select "Save Image As ...".

2. Open the image containing the plot in Gimp,
   crop it if necessary, and save it as a `.png` or `.jpg` file.

3. Open the `.png` or `.jpg` file in Inkscape.
   Use the "link" option to avoid large `.svg` files in one of the following steps.

4. Draw the x-axis and y-axis as two separate straight line segments,
   i.e., lines with only one start node and one end node.
   The accuracy of the extracted data will improve
   if these line segments are made as long as possible.
   It also helps to zoom in to place the nodes as accurately as possible.
   You must make sure that the start and the end nodes are at well-defined points on the axes.
   Unplot can handle cases where the x and y axes are not orthogonal or are rotated,
   e.g. due to a bad scan.

5. Draw one or more polylines consisting of straight line segments
   over the curve(s) of interest.
   Make sure that your drawing falls nicely over the curve in the scanned image,
   as this will also determine the accuracy of the final data.
   It may be helpful to use a brightly colored and semi-transparent line style.
   Inkscape also supports node markers that make it easier to position the nodes,
   as shown in the example below.
   Zooming in on the data points also helps to optimize their position.

6. Open the XML Editor in Inkscape. (Press `Ctrl-Shift-X`.)
   Select the x-axis in the figure
   and change the `id` of the path in the XML Editor to `xaxis:x0:x1:kind`,
   where `x0` and `x1` are replaced with the numerical x-values of
   the start and end points of the line segment for the x-axis.
   The last part, `kind`, must be replaced with `lin` or `log`
   for linear or logarithmic scales, respectively.
   Do the same for the y-axis using the id `yaxis:y0:y1:kind`,
   following the same conventions.
   The paths over the curves should be given the id `data:label`,
   where you replace `label` with an appropriate label.
   This label will be used to identify the data in the output.

7. Use the "File" -> "Save as" menu item to save the file in `.svg` format.


## Example

Example source files: [advanced_topics/unplot/](https://github.com/reproducible-reporting/stepup-reprep/tree/main/docs/advanced_topics/unplot)

The following plot has been [taken from Wikipedia](https://en.m.wikipedia.org/wiki/File:Measured_Bearing_Speed_Effect_data_and_curve.jpg)
and the necessary paths have been drawn over it as input for Unplot.
Open this file in Inkscape to inspect the paths in the XML Editor.
The start and intermediate nodes are marked with circles.
The end node is a diamond.
Hollow node markers are easy to align with data points in the original image.

![plot](unplot/plot.svg)

To convert these paths into data, you can use the `unplot` function of StepUp RepRep as follows:

```python
{% include 'advanced_topics/unplot/plan.py' %}
```
To run the example, make the scripts executable and run StepUp:

```bash
chmod +x plan.py tile.py
stepup -n -w1
```

You should see the following terminal output:

```
{% include 'advanced_topics/unplot/stdout.txt' %}
```

The output is a JSON file containing the extracted data points:

```json
{% include 'advanced_topics/unplot/plot.json' %}
```

Each curve is an item in the dictionary
and the corresponding value is a list with two lists (x- and y-coordinates).

## Troubleshooting

**Q.**
The data points are flipped horizontally or vertically. How can I fix this?

**A.**
You need to make sure that the order of the two points in the line segments for the x
(or y) axes is compatible with the order of `x0` and `x1` in the path id
`xaxis:x0:x1:kind`.
Add a special end marker in Inkscape to identify the end point of the line segment.
The menu item "Path" -> "Reverse path" allows you to swap start and end.
