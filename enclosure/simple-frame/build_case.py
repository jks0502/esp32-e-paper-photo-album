"""Build the e-paper case with slide-in glass rails. All distances are mm."""
from pathlib import Path
import hashlib
import json
import FreeCAD as App
import Part
import Mesh
import MeshPart

OUT = Path(__file__).resolve().parent
W, H, DEPTH = 111.0, 99.0, 20.0
FRONT, WALL, COVER = 2.0, 2.4, 2.4
SCREEN_X, SCREEN_Y = 10.0, 12.0
SCREEN_W, SCREEN_H, SCREEN_T = 91.0, 77.0, 1.2
PLAY = 0.6  # clearance on EACH edge, not an assumed hardware dimension
RAIL_GAP, RAIL_ROOF = 2.0, 1.6
GLASS_Z = FRONT + (RAIL_GAP - SCREEN_T) / 2
SEAM = 0.3
PX, PY = SCREEN_X - PLAY, SCREEN_Y - PLAY
PW, PH = SCREEN_W + 2 * PLAY, SCREEN_H + 2 * PLAY
# Landscape, FPC downward: AA left/right/top margin 3.10; bottom 10.30.
AX, AY = SCREEN_X + 3.1, SCREEN_Y + 10.3
AW, AH = 84.8, 63.6
WINDOW_MARGIN = 1.0
HOLES = [(5, 5), (W-5, 5), (5, H-5), (W-5, H-5)]

def box(w, h, d, x=0, y=0, z=0):
    return Part.makeBox(w, h, d, App.Vector(x, y, z))

def round_box(w, h, d, r=3.0, z=0):
    shape = box(w-2*r, h, d, r, 0, z).fuse(box(w, h-2*r, d, 0, r, z))
    for x, y in [(r,r), (w-r,r), (r,h-r), (w-r,h-r)]:
        shape = shape.fuse(Part.makeCylinder(r, d, App.Vector(x,y,z)))
    return shape.removeSplitter()

doc = App.newDocument("CoupleFrameCase")
shell = round_box(W, H, DEPTH).cut(box(W-2*WALL, H-2*WALL, DEPTH, WALL, WALL, FRONT))
window = box(AW+2*WINDOW_MARGIN, AH+2*WINDOW_MARGIN, FRONT+2,
             AX-WINDOW_MARGIN, AY-WINDOW_MARGIN, -1)
shell = shell.cut(window)
# Two side rails: their rear lips overlap only the blank glass borders.
# The full-length insertion path is open through the bottom housing wall.
rail_end = PY + PH
for x, lip_x in [(PX-2, PX), (PX+PW, PX+PW-2.2)]:
    rail = box(2,rail_end-WALL,RAIL_GAP+RAIL_ROOF,x,WALL,FRONT)
    lip = box(2.2,rail_end-WALL,RAIL_ROOF,lip_x,WALL,FRONT+RAIL_GAP)
    shell = shell.fuse(rail).fuse(lip)
shell = shell.fuse(box(PW+4,2,RAIL_GAP+RAIL_ROOF,PX-2,rail_end,FRONT))
for x, y in HOLES:
    post = Part.makeCylinder(4.0, DEPTH-FRONT, App.Vector(x,y,FRONT))
    pilot = Part.makeCylinder(1.25, 9, App.Vector(x,y,DEPTH-8))
    shell = shell.fuse(post.cut(pilot))
# Broad rear-open service notch: enough width for the WHOLE 29.46 mm short
# PCB edge, allowing USB/BOOT/EN alignment without an invented port offset.
service = box(14, 40, 18, 99, 29, 6)
shell = shell.cut(service)
shell = shell.cut(box(PW,WALL+0.1,DEPTH,PX,-0.1,FRONT)).removeSplitter()
lid = round_box(W, H, COVER).cut(box(14,40,COVER+2,99,29,-1))
# Bottom rear-cover band is now part of the removable entry gate.
lid = lid.cut(box(W+2,10+SEAM,COVER+2,-1,0,-1))
# Rebate under the gate's tongue retains the bottom edge of the rear cover.
lid = lid.cut(box(W+2,5,2,-1,10,1.0))
for x, y in HOLES[2:]:
    lid = lid.cut(Part.makeCylinder(1.7,COVER+2,App.Vector(x,y,-1)))
lid = lid.removeSplitter()

gate = round_box(W,H,COVER,z=DEPTH).common(box(W+2,10,COVER+2,-1,0,DEPTH-1))
gate = gate.fuse(box(PW-2*SEAM,WALL,DEPTH-FRONT-0.2,
                     PX+SEAM,0,FRONT+0.2))
# Two short stops touch only the bottom glass corners, leaving the FPC free.
for x in (PX+SEAM, PX+PW-SEAM-8):
    gate = gate.fuse(box(8,PY-WALL,RAIL_GAP-0.4,x,WALL,FRONT+0.2))
gate = gate.fuse(box(W,5,1.2,0,9.5,DEPTH+COVER-1.2))
for x,y in HOLES[:2]:
    gate = gate.cut(Part.makeCylinder(1.7,COVER+2,App.Vector(x,y,DEPTH-1)))
gate = gate.removeSplitter()
# Lay the long wall face on the bed, with both tongues rising vertically.
gate_print = gate.copy()
gate_print.rotate(App.Vector(0,0,0),App.Vector(1,0,0),90)
gate_print.translate(App.Vector(0,DEPTH+COVER,0))

parts = []
for name, label, shape, placed_shape in [
    ("front", "Front frame / slide-in screen rails", shell, shell),
    ("back", "Removable back / adhesive board mounting", lid, None),
    ("gate", "Bottom entry gate / glass stops", gate_print, gate),
]:
    assert shape.isValid() and len(shape.Solids) == 1 and shape.Volume > 0, name
    obj = doc.addObject("Part::Feature", name.title())
    obj.Label = label
    obj.Shape = (placed_shape if placed_shape is not None else shape).copy()
    if name == "back":
        obj.Placement.Base.z = DEPTH
    parts.append(obj)
    # Export each component in its printing orientation, base at Z=0.
    export_obj = doc.addObject("Part::Feature", "Export"+name.title())
    export_obj.Shape = shape
    Part.export([export_obj], str(OUT / (name + ".stp")))
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.08,
                                  AngularDeflection=0.2, Relative=False)
    mesh.write(str(OUT / (name + ".stl")))
    mesh.write(str(OUT / (name + ".obj")))
    doc.removeObject(export_obj.Name)

# Hardware references are bounding envelopes, NOT component CAD models.
ref_group = doc.addObject("App::DocumentObjectGroup", "References")
references = [
    ("ScreenGlass", box(SCREEN_W,SCREEN_H,SCREEN_T,SCREEN_X,SCREEN_Y,GLASS_Z)),
    ("ActiveArea", box(AW,AH,0.05,AX,AY,GLASS_Z-0.05)),
    # 12 mm is available installation height, not a measured board thickness.
    ("DriverAllowedEnvelope", box(48.25,29.46,12,55,34,7)),
    ("AdapterAllowedEnvelope", box(40,32,10,10,16,9)),
]
preview = {"front":[], "back":[], "gate":[], "hardware":[]}
for name, shape in references:
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    obj.addProperty("App::PropertyString", "Note")
    obj.Note = "Reference only; hidden when opened; not a printable part."
    ref_group.addObject(obj)
    try:
        obj.ViewObject.Visibility = False
    except Exception:
        pass
    if name in ("ScreenGlass", "ActiveArea"):
        vertices, faces = shape.tessellate(0.08)
        preview["hardware"].append({"name":name, "vertices":[[v.x,v.y,v.z] for v in vertices], "faces":faces})

for obj in parts:
    vertices, faces = obj.Shape.tessellate(0.08)
    preview[obj.Name.lower()] = {"vertices":[[v.x,v.y,v.z] for v in vertices], "faces":faces}
    try:
        obj.ViewObject.ShapeColor = (0.82,0.84,0.86)
        obj.ViewObject.Visibility = True
    except Exception:
        pass
doc.recompute()
# Keep the deliverable native model limited to the two printable components.
# FreeCADCmd does not persist GUI visibility, so reference blocks must be removed.
for name, _ in references:
    doc.removeObject(name)
doc.removeObject(ref_group.Name)
doc.recompute()
doc.saveAs(str(OUT / "couple-frame-case.FCStd"))
# Cross section and an insertion position use the same exact CAD geometry.
section_box = box(9,0.2,6,6.5,40,0)
preview["rail_section"] = []
for name,shape in [("rail",shell.common(section_box)),
                   ("glass",references[0][1].common(section_box))]:
    vertices,faces = shape.tessellate(0.08)
    preview["rail_section"].append({"name":name,
        "vertices":[[v.x,v.y,v.z] for v in vertices],"faces":faces})
(OUT / "preview_geometry.json").write_text(json.dumps(preview), encoding="utf-8")

# Fit checks cover ONLY known geometry and declared installation envelopes.
assert shell.common(references[0][1]).Volume < 1e-7, "Glass collision"
# Exact swept volume verifies every position during the straight slide.
sweep = box(SCREEN_W,SCREEN_H+90,SCREEN_T,SCREEN_X,SCREEN_Y-90,GLASS_Z)
assert shell.common(sweep).Volume < 1e-7, "Blocked insertion path"
assert gate.common(references[0][1]).Volume < 1e-7, "Gate squeezes glass"
assert shell.common(gate).Volume < 1e-7, "Gate overlaps frame"
lifted = references[0][1].copy()
lifted.translate(App.Vector(0,0,0.9))
assert shell.common(lifted).Volume > 0.1, "Rails fail to retain glass"
dropped = references[0][1].copy()
dropped.translate(App.Vector(0,-0.7,0))
assert gate.common(dropped).Volume > 0.1, "Gate fails to stop downward sliding"
too_high = references[0][1].copy()
too_high.translate(App.Vector(0,0.7,0))
assert shell.common(too_high).Volume > 0.1, "Top stop fails"
for dx in (-0.7,0.7):
    shifted = references[0][1].copy()
    shifted.translate(App.Vector(dx,0,0))
    assert shell.common(shifted).Volume > 0.1, "Side stop fails"
fpc_route = box(56,9,3.5,28,2.7,2.4)
assert shell.common(fpc_route).Volume < 1e-7
assert gate.common(fpc_route).Volume < 1e-7, "FPC corridor blocked"
assert shell.common(references[2][1]).Volume < 1e-7, "Driver envelope collision"
assert shell.common(references[3][1]).Volume < 1e-7, "Adapter envelope collision"
assembled_lid = lid.copy()
assembled_lid.translate(App.Vector(0,0,DEPTH))
assert shell.common(assembled_lid).Volume < 1e-7, "Case parts overlap"
assert gate.common(assembled_lid).Volume < 1e-7, "Gate overlaps rear cover"
# The gate also slides in from the bottom. Its fingers cannot be dropped
# vertically through the rail roofs, so verify the actual horizontal route.
gate_sweep = box(PW-2*SEAM,WALL+30,DEPTH-FRONT-0.2,PX+SEAM,-30,FRONT+0.2)
for x in (PX+SEAM,PX+PW-SEAM-8):
    gate_sweep = gate_sweep.fuse(box(8,PY-WALL+30,RAIL_GAP-0.4,x,WALL-30,FRONT+0.2))
gate_sweep = gate_sweep.fuse(box(W,40,COVER,0,-30,DEPTH))
gate_sweep = gate_sweep.fuse(box(W,35,1.2,0,9.5-30,DEPTH+COVER-1.2))
assert gate_sweep.common(shell).Volume < 1e-7, "Gate insertion blocked by frame"
assert gate_sweep.common(assembled_lid).Volume < 1e-7, "Gate insertion blocked by cover"
assert gate_sweep.common(references[0][1]).Volume < 1e-7, "Gate insertion hits glass"
assert assembled_lid.common(references[2][1]).Volume < 1e-7
# Every possible point on the PCB's short edge has a route to outside.
usb_route = box(W-103.25+1,29.46,12,103.25,34,7)
assert shell.common(usb_route).Volume < 1e-7
assert assembled_lid.common(usb_route).Volume < 1e-7

report = {
    "version":"v2-slide-in",
    "units":"mm", "case_dimensions":[W,H,DEPTH+COVER],
    "screen_dimensions":[SCREEN_W,SCREEN_H,SCREEN_T],
    "screen_pocket":[PW,PH], "window":[AW+2,AH+2],
    "rail_slot_height":RAIL_GAP,"rail_rear_lip_thickness":RAIL_ROOF,
    "screen_retention":"side rails, top stop, removable bottom stop; no glue on glass",
    "screws":{"diameter":3,"under_head_length":8,"count":4,
              "type":"pan head plastic self tapping","rear_cover":2,"entry_gate":2},
    "service_notch":{"width_along_board_edge":40,"front_z":6,"open_to_rear":True},
    "driver_documented_dimensions":[48.25,29.46],
    "driver_allowed_total_height":12,"adapter_allowed_envelope":[40,32,10],
    "physical_fit_verified":False,
    "unknowns":["Rev3 total component thickness", "adapter actual overall size", "actual cable overmold size"],
    "passed_checks":["one valid solid per printable part", "no glass collision",
        "no installed envelope collision", "no case parts overlap", "clear USB insertion route"],
    "exports":[],
}
report["passed_checks"] += ["continuous screen insertion swept volume clear",
    "rear lift constrained by rails", "side and top movement constrained",
    "bottom sliding constrained by gate", "FPC corridor clear", "gate and cover do not overlap"]
report["passed_checks"].append("continuous gate insertion swept volume clear with cover installed")
for name, shape in [("front",shell),("back",lid),("gate",gate_print)]:
    for ext in ("stl","stp","obj"):
        path = OUT / (name+"."+ext)
        if ext == "stp":
            restored = Part.read(str(path))
            assert restored.isValid() and len(restored.Solids) == 1
            volume = restored.Volume
        else:
            restored = Mesh.Mesh(str(path))
            assert restored.isSolid() and restored.CountFacets > 0
            volume = abs(restored.Volume)
        assert abs(volume-shape.Volume)/shape.Volume < 0.003
        bounds = restored.BoundBox
        actual = [bounds.XLength,bounds.YLength,bounds.ZLength]
        source_bounds = shape.BoundBox
        expected = [source_bounds.XLength,source_bounds.YLength,source_bounds.ZLength]
        assert all(abs(a-b)<0.01 for a,b in zip(actual,expected))
        report["exports"].append({"file":path.name,"dimensions":actual,
            "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"round_trip_valid":True})
(OUT / "verification.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
App.closeDocument(doc.Name)
restored = App.openDocument(str(OUT / "couple-frame-case.FCStd"))
assert restored.getObject("Front").Shape.isValid()
assert restored.getObject("Back").Shape.isValid()
assert restored.getObject("Gate").Shape.isValid()
App.closeDocument(restored.Name)
print("PASS: three solids, nine exports, continuous glass insertion, retention and FPC/USB clearance")
