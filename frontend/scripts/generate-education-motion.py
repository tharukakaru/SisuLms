"""Generate SISU's original vector classroom Lottie. No external media assets."""
import json
import re
from pathlib import Path
K=lambda v:{'a':0,'k':v}
def color(h):return [int(h[i:i+2],16)/255 for i in (0,2,4)]+[1]
def anim(values):
    return {'a':1,'k':[dict(t=t,s=v,**({'e':values[i+1][1],'o':{'x':.42,'y':0},'i':{'x':.58,'y':1}} if i<len(values)-1 else {})) for i,(t,v) in enumerate(values)]}
def shape(geo,fill=None,stroke=None,width=2):
    it=[geo]
    if fill:it.append({'ty':'fl','c':K(color(fill)),'o':K(100),'r':1})
    if stroke:it.append({'ty':'st','c':K(color(stroke)),'o':K(100),'w':K(width),'lc':2,'lj':2})
    return {'ty':'gr','it':it}
def rect(x,y,w,h,c,r=5,stroke=None):return shape({'ty':'rc','p':K([x,y]),'s':K([w,h]),'r':K(r)},c,stroke)
def ellipse(x,y,w,h,c,stroke=None):return shape({'ty':'el','p':K([x,y]),'s':K([w,h])},c,stroke)
def path(svg,c=None,stroke=None,width=2):
    parts=re.findall(r'M[^M]+',svg)
    if len(parts)>1:return {'ty':'gr','it':[path(part,c,stroke,width) for part in parts]}
    tokens=re.findall(r'[MLCQZ]|-?\d+(?:\.\d+)?',svg);v=[];ins=[];outs=[];closed=False;i=0
    while i<len(tokens):
        cmd=tokens[i];i+=1
        if cmd=='Z':closed=True;continue
        n={'M':2,'L':2,'C':6,'Q':4}[cmd];nums=list(map(float,tokens[i:i+n]));i+=n
        target=nums[-2:]
        if cmd in ('C','Q'):
            prev=v[-1]
            if cmd=='C':c1,c2=nums[:2],nums[2:4]
            else:c1=[prev[j]+2/3*(nums[j]-prev[j]) for j in (0,1)];c2=[target[j]+2/3*(nums[j]-target[j]) for j in (0,1)]
            outs[-1]=[c1[j]-prev[j] for j in (0,1)];incoming=[c2[j]-target[j] for j in (0,1)]
        else:incoming=[0,0]
        v.append(target);ins.append(incoming);outs.append([0,0])
    return shape({'ty':'sh','ks':K({'v':v,'i':ins,'o':outs,'c':closed})},c,stroke,width)
layers=[]
def layer(name,shapes,p=None,r=None,anchor=None,scale=None,opacity=None):
    layers.append({'ddd':0,'ind':len(layers)+1,'ty':4,'nm':name,'sr':1,'ks':{'o':opacity or K(100),'r':r or K(0),'p':p or K([0,0,0]),'a':K(anchor or [0,0,0]),'s':scale or K([100,100,100])},'shapes':list(reversed(shapes)),'ip':0,'op':240,'st':0,'bm':0})
def floatp(x=0,y=0,dy=-6):return anim([(0,[x,y,0]),(120,[x,y+dy,0]),(240,[x,y,0])])
purple='512383';dark='27283B';skin='E6AE8D';shade='C9876D';mint='84B6A2';pale='F1EAF8'
layer('Quiet classroom backdrop',[path('M 56 283 C 23 201 59 104 141 108 C 186 108 189 50 272 44 C 356 28 401 58 427 101 C 514 105 571 151 560 228 C 549 306 496 353 393 354 L 141 354 C 82 353 67 327 56 283 Z','F7F3FB'),ellipse(319,375,475,17,'EEE8F4')])
layer('Wall details',[rect(543,101,45,66,None,2,'E9E2EF'),path('M 524 115 L 538 101 L 548 111 L 559 93',None,'E9E2EF',2),ellipse(222,69,9,9,'E0D2EC'),ellipse(495,57,15,15,'E7DDF0')])
# Computer screen and pedestal.
layer('Monitor pedestal',[path('M 350 293 L 395 293 L 407 343 L 338 343 Z','D4CBDD'),rect(373,347,123,13,'EAE4F0',5),rect(373,351,136,8,'DAD1E4',4)])
layer('Monitor frame',[rect(377,195,312,232,'DCD3E7',15),rect(374,190,312,232,dark,15),rect(374,181,289,189,'FFFFFF',5),rect(374,286,289,17,'E7E0EE',3),ellipse(374,286,5,5,'B3A3C4')])
layer('Lesson browser',[rect(374,97,289,20,'F7F4FA',2),ellipse(240,97,4,4,'B99ACD'),ellipse(248,97,4,4,'DACAE6'),ellipse(256,97,4,4,'DACAE6'),rect(371,97,155,7,'EAE1F2',3),rect(374,181,271,146,'F2EDF7',2),rect(374,258,271,18,'353347',2),ellipse(250,258,5,5,'E7A2A6'),rect(284,258,43,3,'CDBCD9',1),path('M 483 255 L 489 258 L 483 261 Z','FFFFFF')])
# A board behind the teacher.
layer('Lesson board',[rect(371,172,227,111,'E3D8EE',6),rect(371,172,218,102,'FFFFFF',3),path('M 276 148 L 304 148 M 276 158 L 320 158 M 440 201 L 460 201',None,'C7B2DB',3),ellipse(450,148,20,20,None,'CBB6DF'),path('M 442 148 L 448 153 L 459 141',None,'9162B0',2)])
# Teacher torso.
layer('Teacher jacket',[path('M 354 172 Q 331 176 325 199 L 319 244 L 422 244 L 418 199 Q 416 178 389 171 Z',purple),path('M 361 171 L 375 183 L 389 171 L 396 244 L 350 244 Z','E9DCF3'),path('M 375 183 L 368 192 L 375 227 L 382 192 Z','8961A6'),path('M 353 176 L 343 190 L 354 201 M 394 177 L 406 190 L 394 202',None,'724B96',2)])
layer('Teacher neck',[path('M 363 151 L 363 174 Q 374 187 387 173 L 386 150 Z',skin),path('M 365 154 L 385 158 L 385 165 Q 372 168 365 161 Z',shade)])
layer('Teacher hair back',[path('M 347 133 Q 337 103 356 103 Q 358 89 373 102 Q 394 94 397 116 L 394 140 Z',dark)])
layer('Teacher face',[path('M 351 119 Q 367 113 386 119 L 388 141 Q 385 159 374 160 Q 358 159 353 146 Z',skin),ellipse(351,137,10,14,skin),ellipse(389,137,9,13,skin),path('M 349 120 Q 356 101 374 108 Q 390 106 391 126 L 385 125 L 383 116 Q 366 126 354 119 L 355 136 L 350 134 Z',dark),path('M 374 132 L 371 141 L 376 142',None,shade,1.5),path('M 366 147 Q 375 154 382 146',None,'8E4D4D',2),path('M 359 128 Q 362 126 366 128 M 379 127 Q 383 125 385 128',None,dark,1.5)])
layer('Teacher eyes',[ellipse(363,133,3,3.5,dark),ellipse(382,133,3,3.5,dark)],scale=anim([(0,[100,100,100]),(95,[100,100,100]),(98,[100,10,100]),(102,[100,100,100]),(240,[100,100,100])]),anchor=[374,133,0],p=K([374,133,0]))
# Teaching gesture: forearm pivots naturally at shoulder.
layer('Teacher explains',[path('M 407 184 Q 416 180 422 188 L 441 209 L 457 189 L 468 195 Q 453 230 438 228 L 408 204 Z',purple),path('M 457 191 L 458 178 Q 458 173 461 176 L 464 184 L 470 173 Q 473 171 474 175 L 468 189 Q 479 185 479 189 L 468 199 Z',skin),path('M 421 202 L 440 219 L 457 197',None,'714593',2)],p=K([409,190,0]),anchor=[409,190,0],r=anim([(0,[0]),(40,[-18]),(85,[-3]),(130,[-14]),(175,[2]),(210,[-10]),(240,[0])]))
layer('Teacher book and hand',[path('M 323 224 L 341 209 L 367 217 L 350 241 L 323 236 Z','D4BE72'),path('M 341 211 L 364 218 L 349 237 L 328 232 Z','FFF7DC'),path('M 327 203 Q 321 211 325 220 L 339 226 Q 344 226 344 222 L 334 215 L 338 206 Z',skin)])
# Clock with moving hand.
layer('Study clock',[ellipse(164,76,51,51,'E6DDED'),ellipse(161,73,51,51,purple),ellipse(161,73,41,41,'FFFFFF'),ellipse(161,73,3,3,purple),path('M 161 73 L 151 62',None,purple,2)])
layer('Clock minute hand',[path('M 0 0 L 12 -5',None,'9979B5',2)],p=K([161,73,0]),r=anim([(0,[0]),(120,[180]),(240,[360])]))
# Chair and legs behind the student.
layer('Student chair',[path('M 89 269 L 78 365 M 145 280 L 165 366',None,'527B6B',7),rect(110,258,76,88,mint,22),rect(123,296,93,14,'5C907B',6)])
layer('Student legs',[path('M 119 277 Q 154 270 174 288 Q 179 299 177 327 L 174 359 L 156 359 L 153 311 L 122 310 Z',dark),path('M 144 294 L 151 335 L 153 361 L 135 362 L 128 331 L 118 308 Z','3D3A50'),path('M 156 354 L 174 354 L 174 365 L 156 365 Z',skin),path('M 135 356 L 152 355 L 155 366 L 137 367 Z',skin)])
layer('Student trainers',[path('M 152 363 L 174 363 Q 181 370 193 370 L 195 379 L 152 379 Z',purple),rect(173,378,46,5,'D3C0E4',2),path('M 133 365 L 155 364 Q 163 370 175 373 L 176 382 L 132 382 Z','8D62AD'),rect(153,382,46,4,'EEE6F5',2),path('M 158 370 L 167 371 M 160 374 L 169 375',None,'FFFFFF',1.5)])
layer('Student hair behind',[path('M 95 163 Q 80 140 96 124 Q 113 111 137 126 Q 151 136 145 159 L 137 212 L 91 221 Q 77 190 95 163 Z',dark),path('M 94 148 Q 71 144 70 167 L 66 212 Q 60 225 54 225 Q 81 234 88 211 L 99 166 Z','393348')])
layer('Student shirt',[path('M 99 183 Q 112 176 129 184 L 144 210 L 151 281 Q 123 292 95 280 L 88 223 Q 84 199 99 183 Z','AE87C9'),path('M 102 197 L 113 219 L 116 278',None,'9871B4',2),path('M 94 266 Q 119 274 146 265',None,'C6A4DE',2)])
layer('Student neck',[path('M 112 165 L 110 184 Q 120 197 132 184 L 128 162 Z',skin),path('M 114 169 Q 121 178 130 172 L 129 164 Z',shade)])
layer('Student face',[path('M 104 137 Q 119 128 138 138 L 141 150 L 148 157 L 141 160 L 139 170 Q 131 181 116 172 Q 105 162 104 137 Z',skin),path('M 103 141 Q 100 124 120 126 Q 139 125 143 140 Q 124 146 118 134 L 112 149 L 106 157 Z',dark),ellipse(109,153,10,14,skin),path('M 136 166 Q 132 169 127 166',None,'985C57',1.5),path('M 130 145 L 139 144',None,dark,1.5),ellipse(134,152,2.5,3.5,dark),ellipse(132,152,16,16,None,'6E527A'),path('M 124 151 L 111 149',None,'6E527A',1.5),ellipse(112,160,4,4,'E8CB85')])
# Desk structure in foreground.
layer('Desk legs',[path('M 70 282 L 54 382 M 239 282 L 253 382',None,'5D8D7B',9),path('M 66 337 L 247 337',None,'9EC5B6',4)])
layer('Desktop',[rect(157,278,219,13,'87B6A3',4),rect(157,286,219,5,'487360',1)])
layer('Student arm on desk',[path('M 99 199 Q 108 194 115 206 L 123 242 L 162 253 L 157 265 Q 110 260 108 250 L 96 220 Z',skin),path('M 99 197 Q 109 193 115 204 L 121 222 L 100 229 L 93 212 Z','C6A3DF'),path('M 157 253 L 168 250 Q 179 252 178 257 L 169 259 L 180 260 Q 182 265 173 266 L 156 264 Z',skin)])
layer('Laptop on desk',[path('M 161 260 L 180 203 Q 181 199 186 199 L 241 199 Q 246 200 244 205 L 227 261 Z','393547'),path('M 170 253 L 185 205 L 237 205 L 222 253 Z','52435F'),ellipse(208,230,11,11,'B69ACA'),rect(195,264,84,5,'DDD2E7',2)])
# Notebook and subtle animated pencil beside laptop.
layer('Student notes',[path('M 224 263 L 244 252 L 267 259 L 247 272 Z','FFFDF8','DDD1E5',1),path('M 235 262 L 248 266 M 240 259 L 254 263',None,'C2AACF',1)])
layer('Study pencil',[path('M 236 260 L 258 243',None,'D7B16A',3),path('M 234 262 L 239 259',None,dark,1.5)],p=anim([(0,[0,0,0]),(30,[7,-4,0]),(60,[1,1,0]),(90,[6,-2,0]),(120,[0,0,0]),(150,[7,-4,0]),(180,[1,1,0]),(210,[6,-2,0]),(240,[0,0,0])]))
layer('Pencil cup',[path('M 62 247 L 64 269 L 80 269 L 83 247 Z','D9B77A'),path('M 66 251 L 64 232 M 73 251 L 74 228 M 78 251 L 82 235',None,'8A66A8',3),path('M 65 256 L 80 256 M 66 261 L 79 261',None,'F3D8A9',1)])
# Plant with an anchored, softly swaying crown.
layer('Plant stand',[path('M 521 333 L 509 380 M 548 333 L 559 380 M 517 358 L 554 358',None,dark,5),rect(535,330,54,7,dark,2),path('M 514 299 L 520 327 L 549 327 L 556 299 Z','A47EC2'),rect(535,300,46,7,purple,3)])
layer('Plant leaves',[path('M 535 302 L 535 244 M 535 287 L 516 267 M 535 277 L 555 250',None,'528F75',2),path('M 535 277 C 506 268 502 245 518 238 C 536 239 538 258 535 277 Z','88BBA5'),path('M 537 279 C 541 249 557 232 568 245 C 579 262 556 279 537 286 Z','70A58D'),path('M 535 259 C 514 244 522 221 535 222 C 551 227 549 248 535 259 Z','A9CFBA'),path('M 534 267 L 519 246 M 542 276 L 563 250 M 535 253 L 535 229',None,'538C72',1.5)],p=K([535,302,0]),anchor=[535,302,0],r=anim([(0,[-2]),(60,[5]),(120,[-2]),(180,[5]),(240,[-2])]))
# Floating connection card above desk.
layer('Connected to class',[rect(214,140,42,30,'FFFFFF',7,'E5D9ED'),path('M 209 144 L 213 148 L 221 137',None,purple,2.5),ellipse(201,138,3,3,'92BAA2')],p=floatp(0,0,-12))
layer('Small progress sparks',[path('M 76 102 L 76 112 M 71 107 L 81 107',None,'BA9FD2',2),ellipse(574,195,6,6,'D7B676'),path('M 461 51 L 461 59 M 457 55 L 465 55',None,'9EBFAC',2)],p=floatp(0,0,-9),opacity=anim([(0,[45]),(60,[100]),(120,[45]),(180,[100]),(240,[45])]))

# Visible lesson progress: lines appear as the teacher explains, then reset softly.
layer('Lesson notes appearing',[rect(293,177,35,3,'B99ACD',1),rect(303,188,55,3,'DDD0E8',1),rect(294,199,37,3,'DDD0E8',1)],opacity=anim([(0,[20]),(40,[20]),(85,[100]),(190,[100]),(240,[20])]))
layer('Lesson progress rail',[rect(375,258,115,3,'62536E',1)])
layer('Lesson progress moving',[rect(0,0,115,3,'BE9DDD',1)],anchor=[-57.5,0,0],p=K([317.5,258,0]),scale=anim([(0,[12,100,100]),(200,[100,100,100]),(220,[100,100,100]),(240,[12,100,100])]))

animation={'v':'5.12.2','fr':30,'ip':0,'op':240,'w':600,'h':420,'nm':'SISU — connected classroom (original illustration)','ddd':0,'assets':[],'layers':list(reversed(layers))}
Path(__file__).resolve().parents[1].joinpath('src/learning/education-motion.json').write_text(json.dumps(animation,separators=(',',':')),encoding='utf-8')
