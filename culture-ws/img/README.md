# Photos

Every image on this site is from the building or an event. No stock photography.

Until real files land here, each image slot renders as a flat color panel with a
halftone screen and a label saying what belongs there. The site looks finished
either way — nothing is broken, the panels are just honest about being empty.

## What to shoot and drop in

| File | Where it shows | What it should be |
|---|---|---|
| `building.jpg` | Home hero | Liberty Plaza from 3rd Street, tall crop |
| `studio-occupied.jpg` | Studios hero | A studio actually being used, not tidied |
| `studio-door.jpg` | Studios grid | A studio door on the ninth floor |
| `hallway.jpg` | Studios grid | The ninth floor hallway |
| `work-in-progress.jpg` | Studios grid | Something half-made on a table |
| `reception.jpg` | Studios grid | Gallery / reception space |
| `drawing-night.jpg` | Classes | A Monday figure drawing session, tall crop |
| `camp.jpg` | Classes | Camp week, kids working |
| `comedy-night.jpg` | Comedy hero | The room mid-show, dark is fine |
| `current-show.jpg` | Gallery | Installation view, wide crop |
| `entrance.jpg` | Visit hero | The 3rd Street entrance, tall crop |

## How to swap one in

Find the slot in the HTML — it looks like this:

```html
<div class="photo photo--tall halftone tilt-r2">
  <!-- <img src="img/building.jpg" alt="Liberty Plaza from 3rd Street"> -->
  <span class="photo__note">Photo — Liberty Plaza, 3rd St.</span>
</div>
```

Uncomment the `<img>`, delete the `<span class="photo__note">` line. Keep the
`halftone` class on dark photos — that is the 5px dot screen from the deck.
Leave the `tilt-*` class alone; the tilts are deliberately uneven.

Export at roughly 1600px on the long edge, JPEG, quality 80.
