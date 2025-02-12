This is a silly main document. It requires data from several other files.

= News flash!!

#image("tada.svg")

#let productivity = csv("aux/productivity.csv")

We're doing great! Here's a summary of our most recent achievements:

#table(
  columns: 2,
  [*Coworker*], [*Last known activity*],
  ..productivity.flatten(),
)
