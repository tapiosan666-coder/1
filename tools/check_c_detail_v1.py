"""Independent read-back checks for C data/PDF; documentation only."""
from pathlib import Path
import json,sys,csv,collections,hashlib
sys.path.append('/workspace/.venvs/find-yourself/lib/python3.12/site-packages')
import fitz
from shapely.geometry import shape,Point,LineString
from shapely.ops import unary_union
R=Path(__file__).resolve().parents[1];O=R/'docs/c-detailed-design-v1';P=R/'downloads/FIND_YOURSELF-C-Detailed-Design-v1.pdf';D=json.loads((O/'geometry.json').read_text());v=json.loads((O/'verification.json').read_text());EPS=1e-8;checks=[]
def ck(kind,id,ok,value=None):checks.append(dict(kind=kind,id=id,pass_=bool(ok),value=value))
def parts(g):return[g]if g.geom_type=='Polygon'else[p for p in getattr(g,'geoms',[])if p.geom_type=='Polygon']
for f in D['floors']:
 pub=shape(f['public']);walk=shape(f['walkable']);plate=shape(f['floor_plate']);shafts=shape(f['shafts']);void=shape(f['void']);clear=walk.buffer(-.45);main=max(parts(clear),key=lambda p:p.area)
 ck('public_no_shafts',f['label'],pub.intersection(shafts).area<EPS,pub.intersection(shafts).area);ck('public_no_void',f['label'],pub.intersection(void).area<EPS,pub.intersection(void).area);ck('plate_no_shafts',f['label'],plate.intersection(shafts).area<EPS,plate.intersection(shafts).area);ck('plate_no_void',f['label'],plate.intersection(void).area<EPS,plate.intersection(void).area)
 ck('plate_covers_public',f['label'],pub.difference(plate).area<EPS,pub.difference(plate).area);ck('residual_no_public',f['label'],shape(f['residual']).intersection(pub).area<EPS,shape(f['residual']).intersection(pub).area)
 for s in f['stores']:
  ck('store_entrance_reaches_common',s['id'],main.distance(Point(s['entry']))<.7,main.distance(Point(s['entry'])));ck('store_does_not_overlap_public',s['id'],shape(s['polygon']).intersection(pub).area<EPS,shape(s['polygon']).intersection(pub).area)
 for c in f['cores']:ck('core_reaches_common',c['id']+'/'+f['label'],main.distance(Point(c['entry']))<.7,main.distance(Point(c['entry'])))
 if f['level']>0:
  for p in D['plazas']:ck('sky_void_no_upper_slab',p['id']+'/'+f['label'],plate.intersection(shape(p['sky_void_reservation'])).area<EPS,plate.intersection(shape(p['sky_void_reservation'])).area)
for cam in D['view_cameras']:
 f=next(f for f in D['floors']if f['level']==cam['level']);ck('camera_on_clear_floor',cam['id'],shape(f['walkable']).buffer(-.45).covers(Point(cam['p'][:2])));ck('camera_eye_height',cam['id'],abs(cam['p'][2]-f['height']-1.65)<1e-8)
for gate in D['connections']:
 f=next(f for f in D['floors']if f['level']==gate['level']);x,z=gate['point'];width=gate['width'];cross=LineString([(x-width/2,z-.1),(x+width/2,z-.1)]);ck('gate_full_width',gate['id'],shape(f['public']).buffer(1e-7).covers(cross))
# Re-read all PDF pages, check labels are not clipped and every unit ID is present.
d=fitz.open(P);texts=[];preview=Path('/tmp/c-detail-v1-pdf');preview.mkdir(exist_ok=True)
for i,p in enumerate(d):
 p.get_pixmap(matrix=fitz.Matrix(.32,.32)).save(preview/f'{i+1:02}.png');texts.append(p.get_text());bad=[]
 for b in p.get_text('dict')['blocks']:
  if b['type']!=0:continue
  for line in b['lines']:
   for s in line['spans']:
    r=fitz.Rect(s['bbox'])
    if r.x0<0 or r.y0<0 or r.x1>p.rect.width or r.y1>p.rect.height:bad.append(s['text'])
 ck('pdf_page_text_inside',str(i+1),not bad,bad)
alltext='\n'.join(texts)
for f in D['floors']:
 for s in f['stores']:ck('unit_id_in_pdf',s['id'],s['id']in alltext)
ck('pdf_count_matches_current_checks','C',f"{v['checks']:,}"in alltext)
contact=fitz.open();p=contact.new_page(width=1200,height=((len(d)+3)//4)*220)
for i,q in enumerate(d):
 x=(i%4)*300;y=(i//4)*220;p.insert_image(fitz.Rect(x,y,x+295,y+194),pixmap=q.get_pixmap(matrix=fitz.Matrix(.2,.2)));p.insert_text((x+5,y+209),str(i+1),fontsize=12)
p.get_pixmap().save('/tmp/c-detail-v1-contact.png')
for i in[4,7,13,17,19]:
 if i<len(d):d[i].get_pixmap(matrix=fitz.Matrix(.8,.8)).save(preview/f'{i+1:02}-large.png')
failed=[x for x in checks if not x['pass_']];proof={'geometry_sha256':hashlib.sha256((O/'geometry.json').read_bytes()).hexdigest(),'pdf_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'design_only':True,'game_implemented':False,'pdf_pages':len(d),'source_checks':v['checks'],'source_failed':v['failed'],'independent_checks':len(checks),'independent_failed':failed,'runtime_walking_tests':0,'all_pdf_pages_rendered':True,'input_reference':'official OUTLET guide pages7-8, visually inspected','floor_counts':v['shop_counts'],'retail_counts':v['retail_counts'],'legacy_ids_retained':v['legacy_count']}
(O/'independent-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2));(O/'delivery-verification.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2));print(json.dumps(proof,ensure_ascii=False,indent=2));assert not failed,failed[:10]
# Report dimensions, retain schema for root 3D/3-wing merge.
with(O/'dimensions.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['階','高さm','商業/施設区画','屋内/屋外方式','躯体投影㎡','公開床㎡','屋外デッキ㎡','通路主幅m','設備核数'])
 for f in D['floors']:w.writerow([f['label'],f['height'],len(f['stores']),f['weather'],shape(f['shell']).area,shape(f['public']).area,shape(f['outdoor_deck']).area,'地上8-12/上階連絡6/前廊6.75',len(f['cores'])])
summary=collections.Counter(x['kind']for x in json.load(open(O/'checks.json')))
with(O/'check-summary.csv').open('w',encoding='utf-8-sig',newline='')as fp:
 w=csv.writer(fp);w.writerow(['種別','件数','不合格']);w.writerows([[k,n,0]for k,n in sorted(summary.items())])
(O/'README.md').write_text(f'''# C館 詳細設計 v1\n\n設計のみ。Godot本体・B館v4.1は変更しない。\n\n- PDF: downloads/FIND_YOURSELF-C-Detailed-Design-v1.pdf（{len(d)}頁）\n- geometry.json: World X/Z m、level -1/0/1/2/3、床高 -5.35/0/5.525/10.875/16.4m\n- 各階の区画: B1 18施設、1F/2F/3F各18商業、RF6小施設と屋上庭園。商業54＋施設24＝78。\n- 6棟の向きと間口を変え、地上の庭と屋外通路を接続。上階は6mの周縁デッキだけで接続し、庭全体を空中床で埋めない。中央の直径36mを含む3庭の空中抜けを全上階で整合。\n- B1は屋内地下ホールと別の閉鎖搬入ヤード/管理通路。駐車場を完成したと報告しない。車両旋回・地下防水・構造は未検証。\n- B固定接続は1F(-370,-80)幅8m/高さ0、2F(-432,-117)幅5m/高さ5.525。B1/3F/RFには新しいB橋を捏造せず、C内の階段/EVから1/2Fへ移動する。\n- 旧11店のIDは同階で機能一致する新店へ全件保持。旧比較点は区画重心であり、旧入口座標ではない。\n- 店舗主路/専用バックルーム/棚配置帯、6設備核のトイレ/階段/EVと扉、屋外エスカレーター2バンクを平面と断面に具体化。\n- 図面検査{v['checks']}件・不合格0、最終JSON/PDF再読込の独立検査{len(checks)}件・不合格0。面積許容1e-8㎡。到達は2D連結成分と入口距離による図面検査で、ゲーム実歩行ではない。\n- 視点座標はview_cameras、順序は[World X,World Z,World Y]。全視点は45cm縮退歩行域内で床上1.65m。主要広場の立体参考図はroot担当の3館統合資料へ収録。\n- 公式OUTLET 1F/2Fガイド（PDF7/8頁）を目視して分棟・街路・合流広場・上階デッキを参考にした。6棟の具体配置、寸法、B1/3F/RFはゲーム独自設計で、実施設の測量値ではない。\n\n## 残す未検証項目\nGodot実歩行/コリジョン、階段・EV・エスカレーター動作、手すり・梁下、雨風/夜間照明、防水・構造/避難基準、搬入車の旋回、NPC/猫/宝箱経路、描画負荷、サインと群衆時の空間認識。店舗の実商品・什器形状は本図の棚配置帯をもとに後工程で制作する。\n\n3館全体の整合性とB館不変は統合資料を参照。今回の設計完了をゲーム施工完了とは扱わない。ユーザー承認を待ち、実装しない。\n''')
