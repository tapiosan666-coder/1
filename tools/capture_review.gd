extends SceneTree
## Read-only v0.23 review: real game rendering plus an explicit demonstration setup.
var game:Node3D
var captures:Array=[]
const PREFIX:="res://docs/screenshots/review23-"
func _initialize()->void:call_deferred("capture")
func world_ring(points:PackedVector2Array)->Array:
 var out:Array=[]
 for i in points.size():
  var a:=points[i];var b:=points[(i+1)%points.size()];var steps:=maxi(1,ceili(a.distance_to(b)/5.0))
  for step in steps:
   var p:=a.lerp(b,float(step)/steps);var q:=MallCurve.world(Vector3(p.x,0,p.y));out.append([q.x,q.z])
 return out
func snapshot()->Dictionary:
 var names:Dictionary={}
 for s:Dictionary in StoreSigns.specifications():names[s.get("outlet",s.id)]=s.text
 var floors:Array=[];var units:Array=[];var roles:Dictionary={};var occupancy:Dictionary={}
 for role in game.crowd.roles:roles[role]=roles.get(role,0)+1
 for slot:Dictionary in game.crowd.slots:
  var key:=MallLayout.floor_at(slot.pos);occupancy[key]=occupancy.get(key,0)+1
 for u:Dictionary in RetailDensity.units():
  var corners:=PackedVector2Array()
  for p:Vector3 in [Vector3(-u.half,0,-u.front),Vector3(u.half,0,-u.front),Vector3(u.half,0,-u.back),Vector3(-u.half,0,-u.back)]:
   var q:Vector3=u.t*p;corners.append(Vector2(q.x,q.z))
  units.append({"id":u.id,"building":u.building,"level":u.level,"kind":u.kind,"name":names.get(u.id,u.kind),"polygon":world_ring(corners)})
 for f:Dictionary in MallLayout.catalog():
  var entry:={"id":f.id,"building":f.building,"level":f.level,"height":f.height,"implemented":f.implemented,"base":[],"structure":[],"shops":[],"plazas":[],"escalators":[],"hubs":[],"fixed_people":occupancy.get(f.id,0)}
  if f.implemented:
   for rect:Rect2 in f.regions:
    if rect==MallStructure.bounds(f.building,f.level):continue
    entry.base.append(world_ring(PackedVector2Array([rect.position,Vector2(rect.end.x,rect.position.y),rect.end,Vector2(rect.position.x,rect.end.y)])))
   for p:Dictionary in MallStructure.floor_packets(f.building,f.level):
    var shape:={"outer":world_ring(p.outer),"holes":[]}
    for hole:PackedVector2Array in p.holes:shape.holes.append(world_ring(hole))
    entry.structure.append(shape)
   for unit:Dictionary in units:
    if unit.building==f.building and unit.level==f.level:entry.shops.append(unit)
   if f.level in [0,1,2]:
    for plaza:Dictionary in MallStructureData.DATA[f.building].plazas:
     if f.building=="C" and f.level==1 and plaza.id=="terrace":continue
     var at:=MallCurve.world(Vector3(plaza.at[0],0,plaza.at[1]));entry.plazas.append({"name":plaza.name,"at":[at.x,at.z]})
    if f.building in ["A","B"]:
     for bank:Dictionary in MallStructureData.DATA[f.building].escalator_banks:
      for lane in [0,1]:
       var x:float=bank.at[0]+bank.side*[13.5,16.5][lane];var a:=MallCurve.world(Vector3(x,0,bank.at[1]-6));var b:=MallCurve.world(Vector3(x,0,bank.at[1]+6));entry.escalators.append({"up":lane==0,"a":[a.x,a.z],"b":[b.x,b.z],"bank":bank.name})
   for h:Dictionary in MallLayout.travel_points():
    if h.floor_id==f.id:entry.hubs.append({"name":h.legacy_key,"at":[h.position.x,h.position.z]})
   if f.building=="A" and f.level in [0,1,2]:entry.private=world_ring(PackedVector2Array([Vector2(-30,-36),Vector2(60,-36),Vector2(60,-24),Vector2(-30,-24)]))
  floors.append(entry)
 var stairs:Array=[]
 for building in ["A","C"]:
  for route:PackedVector3Array in (MallAnnex.core_routes() if building=="A" else CUpper.core_routes()):
   var points:Array=[]
   for p:Vector3 in route:
    var w:=MallCurve.world(p);points.append([w.x,w.y,w.z])
   stairs.append({"building":building,"name":"西側通常階段" if building=="A" else "ゲートコート通常階段","lower":Mall.level_at(route[0].y),"upper":Mall.level_at(route[-1].y),"world_points":points})
 return {"stair_routes":stairs,"version":ProjectSettings.get_setting("application/config/version"),"source_commit":"40ccc24b350373fbc40d14489ea1a46a5207737d","population":game.run.population,"fixed_people":game.crowd.slots.size(),"walking_people":game.crowd.roles.count("walking"),"roles":roles,"floors":floors,"outlets":units,"skills":IdentityRun.SKILLS,"debug_scan_keys":IdentityRun.DEBUG_SCAN_KEYS,"items":RunLoot.ITEMS,"target_distribution":IdentityRun.DISTRIBUTION,"rendering":"Godot 4.6.3, GL Compatibility, balanced; Mesa llvmpipe; not a performance benchmark","captures":captures}
func viewpoint(at:Vector3,toward:Vector3,show_hud:bool=false)->void:
 game.player.position=MallCurve.world(at)-Vector3.UP*1.68;game.player.velocity=Vector3.ZERO;game.player.camera.global_position=MallCurve.world(at);game.player.camera.look_at(MallCurve.world(toward));game.crowd._render()
 game.hud.visible=show_hud;game.player.handheld.visible=show_hud and not game.using_gun;game.player.gun.visible=show_hud and game.using_gun
 game.hud.player_position=game.player.position;game.hud.location_name=Mall.zone_name(game.player.position);game.hud.notice_time=0;game.hud.queue_redraw()
func save_image(id:String,caption:String,setup:String="固定視点・人物の位置/動作を停止。建築・照明・材質は通常ゲームのまま。") -> void:
 game.hud.queue_redraw()
 for frame in 5:await process_frame
 await RenderingServer.frame_post_draw
 var picture:=root.get_texture().get_image();assert(picture.save_png(PREFIX+id+".png")==OK)
 captures.append({"id":id,"caption":caption,"setup":setup,"width":picture.get_width(),"height":picture.get_height(),"image":"review23-"+id+".png"});print("REVIEW_CAPTURE ",id)
func capture()->void:
 root.size=Vector2i(1600,1000)
 game=load("res://scenes/main.tscn").instantiate();root.add_child(game);game.start_run(1000,912)
 game.set_physics_process(false);game.crowd.set_physics_process(false);game.player.set_physics_process(false);GraphicsOptions.apply(game,"balanced",false);game.crowd.clock=.4
 await physics_frame;await physics_frame
 var data:=snapshot()
 var shots:Array=[
  ["a-center","A館1階・中央吹き抜けと上下対の昇降口",Vector3(-34,1.7,-1),Vector3(-42,7,17)],
  ["a-north","A館1階・木もれびの広場",Vector3(-34,1.7,-25),Vector3(-45,6,-39)],
  ["a-entry","A館1階・衣料品店の入口と陳列",Vector3(-57,1.7,-3),Vector3(-57,2,-14)],
  ["a-2f","A館2階・コスメ売場",Vector3(-57,7.225,-5),Vector3(-57,7.9,-17)],
  ["a-3f","A館3階・楽器売場",Vector3(15,12.575,-5),Vector3(15,13.2,-17)],
  ["a-food","A館1階・フードコート",Vector3(69,1.7,-35),Vector3(69,2.3,-60)],
  ["a-restroom","A館1階・洗面と個室",Vector3(-82,1.7,38.5),Vector3(-85,1.3,48.5)],
  ["a-basement","A館地下1階・食品街",Vector3(-82,-3.65,-6),Vector3(-57,-3.5,-18)],
  ["a-roof","A館屋上・庭園と休憩席",Vector3(-87,18.1,-5),Vector3(-65,17.5,-16)],
  ["parking","西駐車場・静止車両と歩行路",Vector3(-160,1.7,-4),Vector3(-130,1.8,18)],
  ["ab-bridge","A館・B館2階連絡通路",Vector3(-143,7.225,-5.5),Vector3(-190,7.225,-5.5)],
  ["b-1f","B館1階・時の広場と主回廊",Vector3(-331,1.7,25),Vector3(-310,5.5,44)],
  ["b-2f","B館2階・昇降口から店舗前回廊へ",Vector3(-204.5,7.225,9.5),Vector3(-231,7.225,13)],
  ["b-3f","B館3階・時の広場側の回廊",Vector3(-311.5,12.575,52.5),Vector3(-334,12.575,62)],
  ["b-cinema","B館3階・映画館",Vector3(-458,12.575,0),Vector3(-479,12.0,0)],
  ["c-1f","C館1階・ゲートコートからガーデンコートへ",Vector3(-386,1.7,-102),Vector3(-428,6,-132)],
  ["c-2f","C館2階・ガーデンテラスと店舗",Vector3(-432,7.225,-117),Vector3(-432,7.525,-151)],
  ["bc-bridge","B館・C館2階ガーデンブリッジ",Vector3(-442,7.225,-34),Vector3(-442,7.525,-94)]
 ]
 for row:Array in shots:
  viewpoint(row[2],row[3]);await save_image(row[0],row[1])
 # Use an existing conversation actor, without replacing or relocating the model.
 var actor:int=game.crowd.roles.find("conversation");var head:Vector3=game.crowd.positions[actor]+Vector3.UP*1.65;var pose:float=game.crowd.headings[actor]
 for side in [0,1]:
  var camera_at:=head+Vector3(sin(pose+side*PI),.02,cos(pose+side*PI))*1.65
  viewpoint(MallCurve.plan(camera_at),MallCurve.plan(head));await save_image("person-"+str(side),"現在の人物モデル・同じ役割人物の近接記録")
 # Find a real, unobstructed target with the initial scanner.
 var found:=false
 for id in game.crowd.slots.size():
  if game.crowd.roles[id] not in ["conversation","walking","browsing"] or id==game.run.true_id:continue
  var target:Vector3=game.crowd.positions[id]
  if MallLayout.floor_at(target)!="A/1F":continue
  for angle in [0.0,PI*.5,PI,PI*1.5]:
   var feet:=target+Vector3(sin(angle),0,cos(angle))*2.6
   if not Mall.walkable(feet):continue
   viewpoint(MallCurve.plan(feet+Vector3.UP*1.68),MallCurve.plan(target+Vector3.UP*1.45),true)
   var hit:Dictionary=game.ray_target()
   if hit.is_empty() or hit.collider.get_meta("identity",-1)!=id:continue
   game.speech.update_nearby(game.crowd,game.player.camera,true);await save_image("speech","近づいたNPCの日本語吹き出し","既存NPCを実際の距離・遮蔽判定で注視。人物位置の差し替えなし。")
   game.speech.dismiss();game._tick_handheld(.9,true,hit);game.hud.target_id=id;game.hud.scan_progress=game.handheld_scan.seconds/game.run.handheld_seconds();game.player.reader_screen.text="スキャン中\n045%"
   await save_image("scanner","初期スキャナーで単体を解析している画面","実際の照準判定と初期スキャナー処理を0.9秒進めて撮影。通常の2秒設定。")
   game._tick_handheld(1.15,true,hit);game.hud.scan_progress=0;game._physics_process(0.0);game.crowd._physics_process(.35);game.crowd._render();await save_image("fall","偽物の解析完了・落下とAP獲得","同じ対象へ初期スキャナーの残り時間を進め、実際の判定・落下処理を記録。")
   found=true;break
  if found:break
 assert(found,"Need an actual unobstructed scan example")
 # UI/ability examples use a disclosed AP grant; no normal-start balance is implied.
 game.run.ap=20000;game.set_mode("skills");await save_image("skills","スキルツリー・AP購入画面","説明用に20,000 APを付与。スキルの表示/購入処理は通常ゲームと同じ。")
 game.set_mode("play");game.buy_skill("gun");game.buy_skill("cat");game.buy_skill("sonar");game.buy_skill("travel");game.set_mode("play");game.equip(true)
 game.hud.ammo=game.ammo;game.hud.using_gun=true;game.sonar();await save_image("gun-sonar","購入したスキャン銃と瞬間ソナー","説明用APで銃・猫・ソナー等を正規購入。ソナーの通常処理を実行。")
 game.equip(false)
 for frame in 90:game._tick_cat(1.0/60)
 var cat_at:Vector3=game.cat.global_position;viewpoint(MallCurve.plan(cat_at+Vector3(1.8,1.5,1.8)),MallCurve.plan(cat_at+Vector3.UP*.4));await save_image("cat","自動探索を担当する猫","説明用APで猫を正規購入し、通常の猫探索処理を90ステップ進めた状態。")
 var chest:Dictionary=game.loot.chests[-1];var chest_view:=false
 for point:Vector3 in game.mall.spawn_points:
  if absf(point.y-chest.pos.y)>.1 or point.distance_to(chest.pos)<1.7 or point.distance_to(chest.pos)>3.3:continue
  var eye:=point+Vector3.UP*1.4
  var ray:=PhysicsRayQueryParameters3D.create(eye,chest.pos+Vector3.UP*.3,1,[game.player.get_rid()])
  if not game.get_world_3d().direct_space_state.intersect_ray(ray).is_empty():continue
  viewpoint(MallCurve.plan(eye),MallCurve.plan(chest.pos+Vector3.UP*.3));chest_view=true;break
 assert(chest_view,"Need a reachable, unobstructed chest viewpoint")
 await save_image("chest","実際に抽選配置された伝説の宝箱","実行中のランの宝箱。場所や中身は撮影用に置き換えていない。")
 for i in game.loot.chests.size():game.loot.open(i)
 game.hud.visible=true;game.set_mode("inventory");await save_image("inventory","宝箱アイテムのバッグ画面","説明用にこのランの宝箱10個を開封。入手品の種類は実際の抽選結果。")
 viewpoint(Vector3(-204.5,7.225,9.5),Vector3(-231,7.225,13),true);game.set_mode("map");game.hud.set_map_floor(1);await save_image("map","ゲーム内案内図・2階と移動地点","説明用APで移動スキル購入済み。未訪問地点へのワープ条件は通常のまま。")
 game.set_mode("title");await save_image("title","タイトル・探索人数とデバッグ開始設定","通常のタイトルUI。デバッグのチェックはOFF。")
 data.captures=captures
 var file:=FileAccess.open("res://docs/review-v023-snapshot.json",FileAccess.WRITE);file.store_string(JSON.stringify(data,"  "));file.close()
 print("REVIEW_EXPORT_OK ",captures.size()," screenshots; ",data.floors.size()," floor records")
 game.queue_free();await process_frame;quit()
