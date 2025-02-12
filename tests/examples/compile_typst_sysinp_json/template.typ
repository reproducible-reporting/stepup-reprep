#let data = json(sys.inputs.json)

#for person in data [
- Hi! I'm #person.name and I'm #person.age years old.
]
