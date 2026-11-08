extends Node3D
var game
var data:Dictionary
var stats:Dictionary={"boards":0,"rows":0,"omitted_boards":[],"blocked_rows":[],"source_mismatches":[],"floor_checks":0,"sweeps":0,"human_playtest":false}
var capsule:CapsuleShape3D
var checks:Array=[]
var live_graphs:Dictionary={}
var grids:Dictionary={}
var grid_index:Dictionary={}
var mounts:Dictionary={}
var mount_audit:Array=[]
var ink:StandardMaterial3D
var metal:StandardMaterial3D
var white:StandardMaterial3D
var icon_texture:Texture2D
func setup(g)->void:
 game=g;name="V21_Route_Derived_Wayfinding";data=g.read_json("res://source/v22/wayfinding.json");capsule=CapsuleShape3D.new();capsule.radius=.31;capsule.height=1.80
 ink=StandardMaterial3D.new();ink.albedo_color=Color(.025,.055,.058);ink.roughness=.56;metal=StandardMaterial3D.new();metal.albedo_color=Color(.21,.24,.25);metal.metallic=.6;metal.roughness=.42;white=StandardMaterial3D.new();white.albedo_color=Color(.83,.88,.85);icon_texture=load("res://assets/v21/art/wayfinding-icons.png")
 call_deferred("validate_and_build")
func get_grid(key:String)->Dictionary:
 if not grids.has(key):grids[key]=game.read_json(grid_index[key])
 return grids[key]
func resolve_mount(board:Dictionary)->void:
 # Support rods must terminate at actual built ceiling collision, never a nominal storey height.
 var p=game.v3(board.p);var n=Vector3(board.n[0],0,board.n[1]);var u=Vector3(n.z,0,-n.x);var top:float=INF
 for side:float in[-1.,1.]:
  var q=PhysicsRayQueryParameters3D.create(p+u*side*panel_width(board)*.35+Vector3.UP*3.9,p+u*side*panel_width(board)*.35+Vector3.UP*8.8,1);var hit=get_world_3d().direct_space_state.intersect_ray(q)
  if hit.is_empty():top=INF;break
  top=minf(top,float(hit.position.y))
 if is_finite(top)and top>p.y+3.9:
  board.mount="ceiling";board.ceiling_y=top-.035;board.mount_validation="Actual two-point ceiling ray support"
 else:
  board.mount="floor";board.mount_validation="No verified overhead support; supplemental outdoor/roof pylon retained"
func floor_y(p:Vector3)->float:
 stats.floor_checks+=1;var q=PhysicsRayQueryParameters3D.create(p+Vector3.UP*.22,p-Vector3.UP*.20,1);q.exclude=[game.player.get_rid()];var hit=get_world_3d().direct_space_state.intersect_ray(q)
 if hit.is_empty()or hit.normal.y<=.65 or absf(hit.position.y-p.y)>=.16:return NAN
 return hit.position.y
func floor_hit(p:Vector3)->bool:return not is_nan(floor_y(p))
func sweep(a:Vector3,b:Vector3)->bool:
 stats.sweeps+=1;var ay:float=floor_y(a);var by:float=floor_y(b)
 if is_nan(ay)or is_nan(by):return false
 a.y=ay;b.y=by
 var q=PhysicsShapeQueryParameters3D.new();q.shape=capsule;q.transform=Transform3D(Basis.IDENTITY,a+Vector3.UP*.95);q.motion=b-a;q.margin=.008;q.collision_mask=1;q.exclude=[game.player.get_rid()]
 var hit=get_world_3d().direct_space_state.cast_motion(q);return hit.is_empty()or hit[0]>=.997
func validate_and_build()->void:
 await get_tree().physics_frame;await get_tree().physics_frame
 for path:String in data.source_hashes:
  if FileAccess.get_sha256("res://"+path)!=str(data.source_hashes[path]):stats.source_mismatches.append(path)
 if not stats.source_mismatches.is_empty():push_warning("V21 wayfinding source changed: regenerate routes; stale arrows suppressed");finish();return
 var variant:String="combined"if game.c_open_proposal and game.es_site_proposal else"C"if game.c_open_proposal else"ES"if game.es_site_proposal else"normal"
 grid_index=game.read_json("res://source/v30/navigation/index.json");stats.live_replans=0;stats.offline_route_conflicts=0
 # Install all physically supported sign bodies first, so no later post can invalidate an earlier route.
 for board:Dictionary in data[variant]:
  if board.has("disabled_reason"):stats.omitted_boards.append({"id":board.id,"reason":board.disabled_reason});continue
  var supported:bool=true;var p=game.v3(board.p)
  for x:float in[-.4,0.,.4]:
   if not floor_hit(p+Vector3(x,0,0)):supported=false
  if supported and post_clear_of_npcs(board):
   resolve_mount(board)
   if board.get("require_ceiling",false)and board.mount!="ceiling":
    stats.omitted_boards.append({"id":board.id,"reason":"No physically confirmed ceiling for transfer guide; no floor obstruction substituted"});continue
   mounts[board.id]=build_board(board,[]);mount_audit.append({"id":board.id,"wing":board.wing,"floor":board.floor,"mount":board.mount,"ceiling_y":board.get("ceiling_y"),"validation":board.get("mount_validation","")})
 await get_tree().physics_frame;await get_tree().physics_frame
 for board:Dictionary in data[variant]:
  if board.has("disabled_reason"):continue
  var position=game.v3(board.p);var supported:bool=true
  for x:float in[-.4,0.,.4]:
   if not floor_hit(position+Vector3(x,0,0)):supported=false
  if not supported:stats.omitted_boards.append({"id":board.id,"reason":"No real same-floor support"});continue
  if not mounts.has(board.id):stats.omitted_boards.append({"id":board.id,"reason":"Post conflicts with preserved NPC route or lacks support"});continue
  var rows:Array=[]
  for row:Dictionary in board.rows:
   row=row.duplicate(true);var result:Dictionary=check_path(row.path);var pass_route:bool=result["pass"];var issue:String=result.reason;var replanned:bool=false
   if not pass_route:
    stats.offline_route_conflicts+=1
    if not live_graphs.has(board.grid_key):
     var graph=load("res://nav_live_v21.gd").new();graph.setup(get_grid(board.grid_key),self);live_graphs[board.grid_key]=graph
    var candidate:Array=live_graphs[board.grid_key].repair(row)
    if not candidate.is_empty():
     result=check_path(candidate)
     if result["pass"]:row.path=candidate;pass_route=true;issue="";replanned=true;stats.live_replans+=1
   var fallback_from:String=""
   if not pass_route and row.has("alternate_targets"):
    for alternative:Dictionary in row.alternate_targets:
     var other:Dictionary=row.duplicate(true);other.target_id=alternative.id;other.target_point=alternative.point;other.label=alternative.label;other.target_source=alternative.source;var candidate:Array=live_graphs[board.grid_key].repair(other)
     if candidate.is_empty():continue
     var result_other:Dictionary=check_path(candidate)
     if not result_other["pass"]:continue
     fallback_from=str(row.target_id);row=other;row.path=candidate;pass_route=true;issue="";replanned=true;stats.live_replans+=1;break
   if pass_route:
    var distance:float=0.;var delta=Vector2.ZERO
    for i in range(row.path.size()-1):
     var a=game.v3(row.path[i]);var b=game.v3(row.path[i+1]);distance+=a.distance_to(b)
     if delta.length()<.15:delta=Vector2(b.x-a.x,b.z-a.z)
    row.distance_m=snappedf(distance,.1)
    for side:int in[1,-1]:
     var n=Vector2(board.n[0],board.n[1])*side;var right=Vector2(n.y,-n.x);var angle:float=atan2(delta.dot(right),delta.dot(-n));row["front_arrow"if side==1 else"back_arrow"]="●"if delta.length()<.15 else["↑","↗","→","↘","↓","↙","←","↖"][posmod(roundi(angle/(PI/4.)),8)]
   checks.append({"sign":board.id,"target":row.target_id,"kind":row.kind,"pass":pass_route,"reason":issue,"variant":variant,"replanned_against_live_collision":replanned,"actual_path":row.path,"fallback_from_unverified_target":fallback_from,"front_arrow":row.front_arrow,"back_arrow":row.back_arrow,"distance_m":row.distance_m})
   if pass_route:rows.append(row)
   else:stats.blocked_rows.append(checks[-1])
  if rows.is_empty():stats.omitted_boards.append({"id":board.id,"reason":"No physically validated destination route"});disable_mount(board.id);continue
  if mounts.has(board.id):fill_labels(mounts[board.id],board,rows)
  stats.boards+=1;stats.rows+=rows.size()
 finish()
func post_clear_of_npcs(d:Dictionary)->bool:
 if d.mount=="ceiling":return true
 var p=Vector2(d.p[0],d.p[2]);var n=Vector2(d.n[0],d.n[1]);var u=Vector2(n.y,-n.x);var poly=PackedVector2Array([p-u*1.10-n*.275,p+u*1.10-n*.275,p+u*1.10+n*.275,p-u*1.10+n*.275]);var padded:Array=Geometry2D.offset_polygon(poly,.44)
 for actor in game.shoppers_v18.actors:
  var r:Dictionary=actor.record
  if str(r.wing)!=str(d.wing)or str(r.floor)!=str(d.floor):continue
  var lines:Array=[]
  if r.get("path",[]).size()>1:lines.append(r.path)
  if r.has("home_point")and r.has("stand_point"):lines.append([r.home_point,r.stand_point])
  if r.has("home_point")and r.has("browse_point"):lines.append([r.home_point,r.browse_point])
  for border:PackedVector2Array in padded:
   for key:String in["p","stand_point","home_point","browse_point"]:
    if r.has(key)and Geometry2D.is_point_in_polygon(Vector2(r[key][0],r[key][2]),border):return false
   for points:Array in lines:
    var route=PackedVector2Array(points.map(func(q):return Vector2(q[0],q[2])))
    if not Geometry2D.intersect_polyline_with_polygon(route,border).is_empty():return false
 return true
func check_path(path:Array)->Dictionary:
 for i in range(path.size()-1):
  var a=game.v3(path[i]);var b=game.v3(path[i+1]);var length:float=a.distance_to(b)
  if not sweep(a,b):return{"pass":false,"reason":"Physical capsule blocked"}
  for j in range(maxi(1,ceili(length/.65))+1):
   if not floor_hit(a.lerp(b,float(j)/maxi(1,ceili(length/.65)))):return{"pass":false,"reason":"Physical same-floor support missing"}
 return{"pass":true,"reason":""}
func disable_mount(id:String)->void:
 if not mounts.has(id):return
 var node:Node3D=mounts[id];node.visible=false
 for c in node.get_children():
  if c is StaticBody3D:c.collision_layer=0
func finish()->void:
 stats.mounts=mount_audit;stats.checks=checks;set_meta("ready",true);game.write_json("v21-wayfinding-physics.json",stats);print("V21_WAYFINDING ",stats.boards," boards / ",stats.rows," rows; blocked ",stats.blocked_rows.size()," omitted ",stats.omitted_boards.size())
func solid(parent:Node3D,p:Vector3,size:Vector3,mat:Material,collision:bool=true)->void:
 var mesh=MeshInstance3D.new();var cube=BoxMesh.new();cube.size=size;mesh.mesh=cube;mesh.position=p;mesh.material_override=mat;mesh.visibility_range_end=100.;parent.add_child(mesh)
 if collision:
  var body=StaticBody3D.new();var shape=CollisionShape3D.new();var box=BoxShape3D.new();box.size=size;shape.shape=box;body.position=p;body.add_child(shape);parent.add_child(body)
func text(parent:Node3D,message:String,p:Vector3,width:float,px:float=.003)->void:
 var label=Label3D.new();label.text=message;label.font=game.font;label.font_size=40;label.pixel_size=px;label.position=p;label.outline_size=0;label.double_sided=false;label.horizontal_alignment=HORIZONTAL_ALIGNMENT_LEFT;label.visibility_range_end=75.;parent.add_child(label);var w:float=game.font.get_string_size(message,HORIZONTAL_ALIGNMENT_LEFT,-1,40).x*px
 if w>width:label.pixel_size*=width/w
func icon(parent:Node3D,kind:String,p:Vector3)->void:
 var i:int=["WC","EV","ES","ST","INFO","FOOD","DINING","CINEMA","ARCADE","PARK","A","B","C","EXIT"].find(kind)
 if i<0:return
 var st=SurfaceTool.new();st.begin(Mesh.PRIMITIVE_TRIANGLES);var points=[Vector3(-.10,.12,0),Vector3(-.10,-.12,0),Vector3(.10,-.12,0),Vector3(.10,.12,0)];var uv=[Vector2(i*192./float(icon_texture.get_width()),0),Vector2(i*192./float(icon_texture.get_width()),1),Vector2((i*192.+192.)/float(icon_texture.get_width()),1),Vector2((i*192.+192.)/float(icon_texture.get_width()),0)]
 for k:int in[0,1,2,0,2,3]:st.set_normal(Vector3.BACK);st.set_uv(uv[k]);st.add_vertex(points[k])
 var mesh=MeshInstance3D.new();mesh.mesh=st.commit();var mat=StandardMaterial3D.new();mat.albedo_texture=icon_texture;mat.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA;mat.cull_mode=BaseMaterial3D.CULL_DISABLED;mat.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;mesh.material_override=mat;mesh.position=p;mesh.visibility_range_end=75.;parent.add_child(mesh)
func panel_width(d:Dictionary)->float:
 return .28+1.78*mini(5,d.rows.size()) if d.mount=="ceiling" else 2.2
func build_board(d:Dictionary,rows:Array)->Node3D:
 var mount=Node3D.new();mount.name=str(d.id).validate_node_name();mount.set_meta("v30_wayfinding",d.id)
 var n=Vector3(d.n[0],0,d.n[1]);mount.transform=Transform3D(Basis(Vector3.UP.cross(n),Vector3.UP,n),game.v3(d.p));add_child(mount)
 var overhead:bool=d.mount=="ceiling";var width:float=panel_width(d);var y:float=3.25 if overhead else 1.8
 var accent=StandardMaterial3D.new();accent.albedo_color=Color(.12,.37,.51)if d.wing=="A"else Color(.12,.31,.22)if d.wing=="B"else Color(.55,.28,.13);accent.roughness=.55
 var panels:int=ceili(float(d.rows.size())/5.) if overhead else ceili(float(d.rows.size())/2.)
 for panel:int in panels:
  var py:float=y-float(panel)*.70
  solid(mount,Vector3(0,py,0),Vector3(width,.60,.12),white,not overhead)
  solid(mount,Vector3(0,py+.285,0),Vector3(width,.025,.14),accent,false)
 if overhead:
  var top:float=float(d.ceiling_y)-float(d.p[1]);var length:float=maxf(.03,top-y-.30)
  for x:float in[-width*.35,width*.35]:solid(mount,Vector3(x,y+.30+length/2.,0),Vector3(.025,length,.025),metal,false)
 else:
  solid(mount,Vector3(0,.055,0),Vector3(1.36,.11,.55),metal)
  for x:float in[-.77,.77]:solid(mount,Vector3(x,.50,0),Vector3(.055,.90,.055),metal)
 if not rows.is_empty():fill_labels(mount,d,rows)
 return mount
func fill_labels(mount:Node3D,d:Dictionary,rows:Array)->void:
 var overhead:bool=d.mount=="ceiling";var width:float=panel_width(d);var y:float=3.25 if overhead else 1.8
 var per_panel:int=5 if overhead else 2
 var names:Dictionary={"WC":"トイレ","EV":"エレベーター","ES":"エスカレーター","ST":"階段","INFO":"ご案内","FOOD":"フードコート","DINING":"レストラン","CINEMA":"シネマ","ARCADE":"ゲーム","PARK":"駐車場","EXIT":"出口","A":"A館","B":"B館","C":"C館"}
 for side:float in[1.,-1.]:
  for panel:int in ceili(float(rows.size())/float(per_panel)):
   var face=Node3D.new();face.name="HorizontalFace_%s_%d"%[str(side),panel];face.position=Vector3(0,y-float(panel)*.70,.066*side);face.rotation.y=PI if side<0 else 0.;mount.add_child(face)
   var count:int=mini(per_panel,rows.size()-panel*per_panel);var cell:float=(width-.24)/float(count)
   for i:int in count:
    var row:Dictionary=rows[panel*per_panel+i];var left:float=-width*.5+.12+float(i)*cell
    var arrow:String=str(row.front_arrow if side>0 else row.back_arrow)
    text(face,arrow,Vector3(left,.0,.003),cell*.17,.006 if overhead else .004)
    var before:int=face.get_child_count();icon(face,str(row.kind),Vector3(left+cell*.24,0,.004))
    if face.get_child_count()>before:
     var glyph:MeshInstance3D=face.get_child(-1);var material:StandardMaterial3D=glyph.material_override.duplicate();material.albedo_color=Color(.08,.17,.20);glyph.material_override=material;glyph.scale=Vector3.ONE*(1.0 if overhead else .72)
    text(face,str(names.get(row.kind,row.label)),Vector3(left+cell*.35,0,.003),cell*.61,.0034 if overhead else .0025)
    if i>0:solid(face,Vector3(left-.05,0,0),Vector3(.008,.36,.006),metal,false)
   for label:Label3D in face.find_children("*","Label3D",true,false):label.modulate=Color(.08,.17,.20)
 mount.set_meta("v30_visible_destinations",rows.size());mount.set_meta("v30_distance_displayed",false)

func _exit_tree()->void:
 for graph in live_graphs.values():graph.clear();graph.way=null
 live_graphs.clear();mounts.clear();game=null
