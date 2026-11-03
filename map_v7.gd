extends Control
var data:Array=[]
var player:CharacterBody3D
var font:Font
var wing:String="B"
var floor_label:String="1F"
var selected:Dictionary={}
var scale_m:float=1.
var offset:Vector2
var map_rect=Rect2(275,140,1600,790)
var wing_select:OptionButton
var floor_select:OptionButton
func setup(d:Array,p:CharacterBody3D,f:Font)->void:
 data=d;player=p;font=f;set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 var panel=ColorRect.new();panel.show_behind_parent=true;panel.color=Color(.025,.045,.055,.97);panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);add_child(panel)
 var title=Label.new();title.position=Vector2(38,25);title.text=("構造別案・未承認  /  "if d.any(func(q):return q.has("variant"))else"")+"検証用 館内マップ  /  Mで閉じる";title.add_theme_font_size_override("font_size",30);add_child(title)
 wing_select=OptionButton.new();wing_select.position=Vector2(35,135);wing_select.size=Vector2(210,50)
 for w in ["A","B","C","P-A-E","P-B-S","P-C-N","P-B-W","P-A-S"]:wing_select.add_item(w+"館"if w.length()==1 else w)
 wing_select.select(1);wing_select.item_selected.connect(func(index):wing=wing_select.get_item_text(index).trim_suffix("館");refresh_floors());add_child(wing_select)
 floor_select=OptionButton.new();floor_select.position=Vector2(35,205);floor_select.size=Vector2(210,50);floor_select.item_selected.connect(func(index):floor_label=floor_select.get_item_text(index);choose());add_child(floor_select)
 var legend=Label.new();legend.position=Vector2(35,300);legend.text="水色：共用通路\n青：店舗\n緑：広場・庭園・EV\n黄：階段・ES\n紫：トイレ\n灰：駐車区画\n×印：未実装・未承認\n\n赤矢印：現在地・向き\n\n検証用の設備表示です。\n建築安全・避難性能は\n実証していません。";legend.add_theme_font_size_override("font_size",18);add_child(legend)
 var footer=Label.new();footer.position=Vector2(35,990);footer.text="移動停止中 / 階の切替は表示のみ・ワープしません。設備は実装状態を示し、検査合否とは別です。";footer.add_theme_font_size_override("font_size",20);add_child(footer)
 refresh_floors()
func refresh_floors()->void:
 floor_select.clear();var index:int=0;var found:bool=false
 for f:Dictionary in data:
  if f.wing!=wing:continue
  floor_select.add_item(f.label)
  if f.label==floor_label:floor_select.select(index);found=true
  index+=1
 if not found:floor_label=floor_select.get_item_text(0);floor_select.select(0)
 choose()
func choose()->void:
 for f:Dictionary in data:
  if f.wing==wing and f.label==floor_label:selected=f;break
 var bb:Array=selected.bounds;var w:float=bb[2]-bb[0];var h:float=bb[3]-bb[1];scale_m=min(map_rect.size.x/(w+12),map_rect.size.y/(h+12));offset=map_rect.get_center()-Vector2((bb[0]+bb[2])/2,(bb[1]+bb[3])/2)*scale_m
 queue_redraw()
func point(q:Array)->Vector2:return Vector2(q[0],q[1])*scale_m+offset
func polyfill(geometry:Array,color:Color)->void:
 for po:Array in geometry:
  var first:bool=true
  for ring:Array in po:
   var points=PackedVector2Array()
   for p:Array in ring:points.append(point(p))
   if points.size()>3:
    points.remove_at(points.size()-1)
    if Geometry2D.triangulate_polygon(points).size()>0:draw_colored_polygon(points,color if first else Color(.025,.045,.055))
    var outline=points.duplicate();outline.append(points[0]);draw_polyline(outline,Color(.65,.73,.75,.5),1.)
   first=false
func _draw()->void:
 if selected.is_empty():return
 draw_rect(map_rect,Color(.045,.07,.08));polyfill(selected.floor,Color(.19,.25,.28));polyfill(selected.public,Color(.30,.48,.51))
 var colors={"庭園":Color(.23,.42,.28),"休憩所":Color(.34,.61,.49),"ロッカー":Color(.38,.56,.66),"店舗":Color(.16,.36,.52),"広場":Color(.29,.52,.37),"EV":Color(.21,.65,.48),"階段":Color(.8,.65,.26),"エスカレーター":Color(.73,.52,.24),"トイレ":Color(.58,.39,.63),"吹抜":Color(.04,.08,.1),"催事":Color(.87,.56,.25),"休憩・施設":Color(.35,.68,.50),"駐車場":Color(.38,.41,.42)}
 var label_boxes:Array=[];var seen:Dictionary={};var labels:Array=[]
 for q:Dictionary in selected.items:
  polyfill(q.geometry,colors.get(q.kind,Color(.6,.6,.6)))
  var p=point(q.point)
  if not q.implemented:draw_line(p-Vector2(5,5),p+Vector2(5,5),Color(.9,.6,.4),2);draw_line(p+Vector2(5,-5),p+Vector2(-5,5),Color(.9,.6,.4),2)
  if q.kind not in ["店舗","駐車場","吹抜"]:
   var key:String=str(q.id);var caption:String=str(q.get("name",q.kind))if str(q.id).begins_with("V16-")else str(q.kind)
   if q.kind=="トイレ":key=key.trim_suffix("-women").trim_suffix("-men")+"-WC";caption="WC"
   elif q.kind=="エスカレーター":key=key.trim_suffix("-UP").trim_suffix("-DOWN");caption="ES"
   if not seen.has(key):
    seen[key]=true;var width:float=font.get_string_size(caption,HORIZONTAL_ALIGNMENT_LEFT,-1,12).x+10
    var r=Rect2(p+Vector2(8,-15),Vector2(width,19))
    for attempt in range(14):
     var overlap:bool=false
     for previous:Rect2 in label_boxes:
      if r.grow(2).intersects(previous):overlap=true;break
     if not overlap:break
     r.position.y+=21
    label_boxes.append(r);labels.append({"rect":r,"point":p,"caption":caption})
 for label:Dictionary in labels:
  var r:Rect2=label.rect;draw_line(label.point,r.get_center(),Color(.70,.77,.75),1);draw_rect(r,Color(.03,.09,.11,.94));draw_string(font,r.position+Vector2(5,14),label.caption,HORIZONTAL_ALIGNMENT_LEFT,-1,12,Color.WHITE)
 var world=Vector2(player.position.x-429,player.position.z+46);var marker=world*scale_m+offset
 if map_rect.has_point(marker) and abs(player.position.y-float(selected.height))<3.0:
  var forward=Vector2(-player.global_basis.z.x,-player.global_basis.z.z).normalized();var side=Vector2(-forward.y,forward.x);draw_colored_polygon(PackedVector2Array([marker+forward*17,marker-forward*9+side*9,marker-forward*9-side*9]),Color(1,.30,.25))
 draw_string(font,Vector2(290,114),wing+" / "+floor_label+(" （階間移動中）" if abs(player.position.y-float(selected.height))>.7 else "")+"   寸法単位 m   店舗 "+str(selected.items.filter(func(q):return q.kind=="店舗").size()),HORIZONTAL_ALIGNMENT_LEFT,-1,25,Color.WHITE)
 var length_m:float=50.;var yy:float=map_rect.end.y+32;draw_line(Vector2(300,yy),Vector2(300+length_m*scale_m,yy),Color.WHITE,3);draw_string(font,Vector2(300,yy+24),"50 m",HORIZONTAL_ALIGNMENT_LEFT,-1,18,Color.WHITE)
func follow_current_floor()->void:
 var world=Vector2(player.position.x-429,player.position.z+46);var best:float=INF;var chosen:Dictionary={}
 for f:Dictionary in data:
  var bb=f.bounds;var r=Rect2(bb[0],bb[1],bb[2]-bb[0],bb[3]-bb[1]);var penalty:float=abs(player.position.y-float(f.height))+(0 if r.has_point(world) else 500)
  if penalty<best:best=penalty;chosen=f
 if chosen.is_empty():return
 wing=chosen.wing;floor_label=chosen.label
 for i in range(wing_select.item_count):
  if wing_select.get_item_text(i).trim_suffix("館")==wing:wing_select.select(i)
 refresh_floors()
func _process(_dt:float)->void:
 if visible:queue_redraw()
func _get_tooltip(at:Vector2)->String:
 var world=(at-offset)/scale_m
 for item:Dictionary in selected.get("items",[]):
  for polygon:Array in item.geometry:
   if polygon.is_empty():continue
   var ring=PackedVector2Array()
   for p:Array in polygon[0]:ring.append(Vector2(p[0],p[1]))
   if not Geometry2D.is_point_in_polygon(world,ring):continue
   var in_hole:bool=false
   for j in range(1,polygon.size()):
    var hole=PackedVector2Array()
    for p:Array in polygon[j]:hole.append(Vector2(p[0],p[1]))
    if Geometry2D.is_point_in_polygon(world,hole):in_hole=true
   if not in_hole:return str(item.id)+" / "+str(item.kind)+(" / 未実装・未承認" if not item.implemented else " / 検証モデル")+("\n"+str(item.validation_note)if item.has("validation_note")else"")
 return ""
