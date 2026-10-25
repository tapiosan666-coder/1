extends SceneTree
var checks:=0
var failures:=0
var polygons:=0
func _initialize()->void:call_deferred("verify")
func verify()->void:
 var hud:=FindHUD.new();root.add_child(hud)
 for level in [-1,0,1,2,3]:
  hud.mode="map";hud.map_level=level
  check_view(hud,Rect2(100,270,1240,325),level,"full map")
 for level in [0,1,2]:
  hud.mode="play"
  for x in [-650,-600,-500,-414,-370,-305,-218,-192]:
   for z in [-45,0,40,75]:
    hud.player_position=Vector3(x,Mall.floor_height(level),z)
    check_view(hud,Rect2(49,751,212,86),level,"moving minimap")
 hud.queue_free();await process_frame
 print("MAP UI POLYGONS ",polygons)
 print("MAP UI RESULT: %d checks, %d failures"%[checks,failures]);quit(1 if failures else 0)
func check_view(hud:FindHUD,frame:Rect2,level:int,label:String)->void:
 checks+=1;var passed:=true
 var limit:=PackedVector2Array([frame.position,Vector2(frame.end.x,frame.position.y),frame.end,Vector2(frame.position.x,frame.end.y)])
 for building in ["A","B","C"]:
  for record:Dictionary in hud._structure_shapes(building,level,Color.WHITE):
   var transformed:=PackedVector2Array()
   for p:Vector2 in record.points:transformed.append(hud._map_point(p,frame))
   for clipped:PackedVector2Array in Geometry2D.intersect_polygons(transformed,limit):
    var result:=FindHUD.map_triangles(clipped)
    if result.is_empty():continue
    polygons+=1
    if result.indices.is_empty():passed=false;push_error("Unfilled %s %s/%d at %s"%[label,building,level,hud.player_position]);continue
    var points:PackedVector2Array=result.points;var ids:PackedInt32Array=result.indices;var area:=0.0
    for i in range(0,ids.size(),3):area+=absf((points[ids[i+1]]-points[ids[i]]).cross(points[ids[i+2]]-points[ids[i]]))*.5
    var ring_area:=0.0
    for i in points.size():ring_area+=points[i].cross(points[(i+1)%points.size()])*.5
    if absf(area-absf(ring_area))>maxf(.1,area*.0001):passed=false;push_error("Map triangle area differs from its floor outline")
 if not passed:failures+=1
