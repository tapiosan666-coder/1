extends Node3D
var player:Node3D
var leaves:Array=[]
var progress:float=0.
var hold:float=0.
var trigger_radius:float=3.5
var opening:float=1.7
var force_open:bool=false
var cycles:int=0
var previous_open:bool=false
var actors:Array=[]
var sense_npcs:bool=true
func _physics_process(delta:float)->void:
 if player==null:return
 var p:Vector3=to_local(player.global_position)
 var detected:bool=absf(p.x)<3.2 and absf(p.z)<trigger_radius and absf(p.y)<2.5
 if sense_npcs and not detected:
  for actor in actors:
   if not is_instance_valid(actor)or not actor.is_visible_in_tree():continue
   var q:Vector3=to_local(actor.global_position)
   if absf(q.x)<3.2 and absf(q.z)<trigger_radius and absf(q.y)<2.5:detected=true;break
 if detected or force_open:hold=1.8
 else:hold=maxf(0.,hold-delta)
 var target:float=1. if hold>0. else 0.
 progress=move_toward(progress,target,delta*1.8)
 # Sensor hold covers the entire doorway; a capsule in the opening prevents closure.
 for index in leaves.size():
  var side:float=-1. if index==0 else 1.
  leaves[index].position.x=side*(.83+opening*progress)
 if progress>.98 and not previous_open:cycles+=1;previous_open=true
 if progress<.02:previous_open=false
func state()->Dictionary:return {"progress":progress,"hold":hold,"cycles":cycles,"collision_leaves":leaves.size(),"sensor_radius_m":trigger_radius}
