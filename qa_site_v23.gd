extends SceneTree
var g
func _initialize()->void:call_deferred("run")
func run()->void:
 var scene:String="res://Integrated_candidate_v22.tscn"
 for a:String in OS.get_cmdline_user_args():
  if a=="--normal":scene="res://main.tscn"
 g=load(scene).instantiate();g.mode="v22-actual-collision-audit";root.add_child(g)
 while g.results.is_empty():await process_frame
 var way=g.get_node("V21_Route_Derived_Wayfinding")
 while not way.has_meta("ready"):await process_frame
 Engine.max_fps=0;g.shoppers_v18.set_frozen(true);g.player.set_physics_process(false);await physics_frame;await physics_frame
 var source:Dictionary=g.read_json("res://source/v25/retail-plan.json");var entrances:Array=[];var supported:Array=[];var directions:Dictionary=g.read_json("res://source/v22/store-directions.json");var physics=g.get_world_3d().direct_space_state
 for s:Dictionary in source.stores:
  var entry=Vector3(s.entry_world[0],s.height,s.entry_world[1]);var n:Vector3=g.v3(directions[s.id])
  n.y=0;n=n.normalized();var u=Vector3(n.z,0,-n.x);var pass_entry:bool=false;var used:float=0.;var detail:Array=[]
  for offset:float in[0.,-.25,.25,-.5,.5]:
   var a:Vector3=entry+u*offset-n*.85;var b:Vector3=entry+u*offset+n*1.20
   if way.sweep(a,b):pass_entry=true;used=offset;break
  if not pass_entry:
   var query=PhysicsShapeQueryParameters3D.new();query.shape=way.capsule;query.transform.origin=entry+Vector3.UP*.95;query.collision_mask=1
   for hit:Dictionary in physics.intersect_shape(query,6):detail.append(str(hit.collider.name))
  entrances.append({"store_id":s.id,"wing":s.wing,"floor":s.floor,"entry_world":[entry.x,entry.y,entry.z],"capsule_access":pass_entry,"lateral_offset_m":used,"contacts":detail,"canonical_coordinate_clear":pass_entry and used==0.,"human_tested":false})
 for r:Dictionary in source.fixtures:
  var p=g.v3(r.p)-Vector3.UP*.02;supported.append({"id":r.id,"store_id":r.store_id,"floor_support":way.floor_hit(p)})
 var seam:Array=[]
 for x:float in[391.5,392.,392.5,393.,393.2,393.5,394.,394.5,395.]:
  var p=Vector3(x,1.05,-51.4);var q=PhysicsRayQueryParameters3D.create(p,p+Vector3(0,0,-24),1);var hit=physics.intersect_ray(q)
  seam.append({"start":[p.x,p.y,p.z],"hit":[hit.position.x,hit.position.y,hit.position.z]if not hit.is_empty()else[],"collider":str(hit.collider.name)if not hit.is_empty()else"NONE"})
 var npc_count:int=0
 for a in g.shoppers_v18.actors:
  if a.visible:npc_count+=1
 var report={"scene":scene,"software_gpu_only":true,"human_playtest":false,"method":"Actual loaded Godot collision: continuous r=.31m h=1.8m capsule cast across entrances, +/-0.5m diagnostics and floor rays. This is not CharacterBody walking or human control.","entrances":entrances,"failed_entrances":entrances.filter(func(r):return not r.capsule_access),"canonical_entry_offsets":entrances.filter(func(r):return r.capsule_access and r.lateral_offset_m!=0.),"fixture_floor_support":supported,"unsupported_fixtures":supported.filter(func(r):return not r.floor_support),"reported_A_joint_rays":seam,"NPC_visible":npc_count,"retail":g.get_node("V22_Separate_Fixtures_And_SKUs").stats,"structural_engineering_verified":false}
 g.write_json("v23-site-collision.json",report);print("V22_SITE_QA ",entrances.size()-report.failed_entrances.size(),"/",entrances.size()," entrances; unsupported ",report.unsupported_fixtures.size(),"/",supported.size());g.queue_free();await process_frame;await process_frame;quit()
