This document will only compile well if the field `data.yaml` contains a field `fixed`.

#let data = yaml("data.yaml")

Test: #data.fixed
