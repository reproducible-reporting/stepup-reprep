# Tile PDFs

StepUp RepRep includes a tool to tile panels (individual PDF figures) into a composite PDF figure.

The tiling code is based on the *script protocol* in StepUp Core,
which is explained in the
[StepUp Core "Getting Started" tutorials](https://reproducible-reporting.github.io/stepup-core/getting_started/introduction/).

This tutorial provides a simple example that you can use as a starting point.
For a more advanced example, see the
[`tile_pdf` test case](https://github.com/reproducible-reporting/stepup-reprep/tree/main/tests/cases/tile_pdf)
in the StepUp RepRep unit test suite.

## Example

Example source files: [advanced_topics/tile_pdfs/](https://github.com/reproducible-reporting/stepup-reprep/tree/main/docs/advanced_topics/tile_pdfs)

Create a `tile.py` script with the following code:

```python
{% include 'advanced_topics/tile_pdfs/tile.py' %}
```

Next, create a script `plan.py` as follows:

```python
{% include 'advanced_topics/tile_pdfs/plan.py' %}
```

For this example to work, you also need to create four SVG figures of the same size:
`triangle.svg`, `square.svg`, `pentagon.svg` and `hexagon.svg`.

To run the example, make the scripts executable and run StepUp:

```bash
chmod +x plan.py tile.py
stepup -n -w1
```

You should see the following terminal output:

```text
{% include 'advanced_topics/tile_pdfs/stdout.txt' %}
```

This is the PNG conversion of the resulting PDF figure:

![figure](tile_pdfs/figure.png)
