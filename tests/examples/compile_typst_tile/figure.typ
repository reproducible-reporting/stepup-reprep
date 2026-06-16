#set page(width: auto, height: auto, margin: 1mm)
/* Notes:
  - The bitmap figures have little metadata, so their sizes are set manually.
*/
#set text(font: "DejaVu Sans Mono", size: 8pt)
#grid(
  columns: 3,
  column-gutter: 2mm,
  row-gutter: 1mm,
  align: center + horizon,
  grid(
    columns: 1,
    box(height: 4mm)[(a) triangle.gif],
    image("triangle.gif", width: 50mm)
  ),
  grid(
    columns: 1,
    box(height: 4mm)[(b) square.webp],
    image("square.webp", width: 50mm)
  ),
  grid.cell(
    rowspan: 2,
    grid(
      columns: 1,
      box(height: 4mm)[(e) vertical.svg],
      image("vertical.svg")
    )
  ),
  grid(
    columns: 1,
    box(height: 4mm)[(c) pentagon.jpg],
    image("pentagon.jpg", width: 50mm)
  ),
  grid(
    columns: 1,
    box(height: 4mm)[(d) hexagon.png],
    image("hexagon.png", width: 50mm)
  ),
  grid.cell(
    colspan: 3,
    grid(
      columns: 1,
      box(height: 4mm)[(f) horizontal.pdf],
      image("horizontal.pdf")
    )
  )
)
