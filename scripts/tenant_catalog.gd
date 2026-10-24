class_name TenantCatalog
extends RefCounted
## Fictional A-wing tenants. Floor numbers here use the game's zero-based levels.
const NORTH := {
 1:[["KITCHEN LAB / キッチン用品","kitchen"],["LUMI / コスメとケア","beauty"],[],["NOVA / レディース","fashion"],["FRAME / 眼鏡","optical"],["ORBIT / バッグと旅行","travel"],["ROOM / 寝具と暮らし","home"],["AURA / アクセサリー","jewelry"],[]],
 2:[["COLOR / 画材と文具","stationery"],["KIDS CLOSET / こども服","kids"],[],["BLOCK / おもちゃ","toys"],["HOBBY BASE / 模型","hobby"],["SOUND / 楽器","music"],["PLAY / ゲームコーナー","arcade"],["ACTIVE / スポーツ","sport"],[]]
}
const SOUTH := {
 1:[[],["STUDIO / メンズ","fashion"],[],["STEP / 靴","shoes"],["SELECT / 服飾雑貨","jewelry"],[],[],["MELLOW / カフェ","cafe"],["FOCUS / 生活家電","digital"]],
 2:[[],["STORY / 児童書","books"],[],["TRAIL / アウトドア","outdoor"],["JOURNEY / トラベル","travel"],[],[],["SWEET / デザートカフェ","cafe"],["CAMPUS / 文具と小物","stationery"]]
}
const THEMES := {
 "kitchen":"8b927e","beauty":"c29c96","fashion":"8c857b","optical":"6d8b8c","travel":"6a777f","home":"aa9b83","jewelry":"aa9577","cafe":"86745f","digital":"697c8b",
 "stationery":"729889","kids":"9eaf93","toys":"c4a16d","hobby":"7c8e9c","music":"686575","arcade":"526d86","sport":"7c8f70","books":"a7967d","outdoor":"8c9675","shoes":"9a8c7b"
}
static func tenant(level:int,index:int,side:int)->Dictionary:
	if not NORTH.has(level) or index<0 or index>=Mall.SHOP_CENTERS.size():return {}
	var row:Array=NORTH[level][index] if side<0 else SOUTH[level][index]
	if row.is_empty():return {}
	var kind:String=row[1]
	return {"level":level,"index":index,"x":Mall.SHOP_CENTERS[index],"side":side,"name":row[0],"kind":kind,"color":Color(THEMES[kind])}
static func all_for_floor(level:int)->Array[Dictionary]:
	var result:Array[Dictionary]=[]
	if not NORTH.has(level):return result
	for side in [-1,1]:
		for index in Mall.SHOP_CENTERS.size():
			var spec:=tenant(level,index,side)
			if not spec.is_empty():result.append(spec)
	return result
static func summary(level:int)->String:
	return "ファッション・ビューティー・暮らし" if level==1 else "キッズ・文具・楽器・ホビー"
static func category(kind:String)->int:
	if kind in ["books","stationery"]:return 0
	if kind in ["fashion","kids"]:return 1
	if kind in ["shoes","travel"]:return 2
	if kind=="digital" or kind=="arcade":return 4
	if kind=="cafe":return 5
	if kind=="home":return 6
	if kind in ["sport","outdoor"]:return 8
	return 3
static func entry_width(kind:String)->float:
	return 4.8 if kind in ["beauty","optical","jewelry"] else 7.2 if kind in ["kids","toys","arcade","sport"] else 6.0
static func transform(spec:Dictionary)->Transform3D:
	return Transform3D(Basis(Vector3.UP,PI if spec.side>0 else 0.0),Vector3(spec.x,Mall.floor_height(spec.level),0))
