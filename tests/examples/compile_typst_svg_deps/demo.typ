#import "@preview/based:0.1.0": encode64

#set page(
  width: auto,
  height: auto,
  margin: 0.5cm,
)

// Loads an SVG image and replaces any contained links to images with the base64 encoded data of the images
// Workaround for https://github.com/typst/typst/issues/5335
#let load-svg = (path, ..args) => {
  let original = read(path)
  // Extract base path to load linked images
  let basepath = path.trim(regex(`[^/]`.text), at: end)
  // Find all image tags with xlink:href attribute
  let matches = original.matches(regex(`<image[^>]*xlink:href="([^"]*)"`.text))
  let output = original
  // Keep track of loaded images to avoid loading the same image multiple times
  let loaded = (:)

  for match in matches {
    let linked-path = match.captures.first()
    // Skip already embedded images
    if linked-path.starts-with("data:image/") {
      continue
    }
    let ext = linked-path.split(".").last()
    // Skip unsupported formats and only load new images
    if (ext.ends-with(regex("[jJ][pP][eE]?[gG]")) or ext.ends-with(regex("[pP][nN][gG]")) or ext.ends-with(regex("[gG][iI][fF]"))) and not loaded.at(linked-path, default: false) {
      let data = read(basepath + linked-path, encoding: none)
      let data-encoded = encode64(data)
      output = output.replace(linked-path, "data:image/" + ext + ";base64," + data-encoded)
      loaded.insert(linked-path, true)
    }
  }

  image(bytes(output), ..args)
}

#grid(
  columns: 2,
  gutter: 0.5cm,
  align: center,
  grid.cell(colspan: 2)[*Typst built-in image function:*],
  [linked.svg],[embedded.svg],
  image("linked.svg"),image("embedded.svg"),
  grid.cell(colspan: 2)[*w1th0utnam3 load-svg workaround:*],
  [linked.svg],[embedded.svg],
  load-svg("linked.svg"),load-svg("embedded.svg"),
)
