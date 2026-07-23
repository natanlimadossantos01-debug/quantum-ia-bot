#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════╗
║   ⚛️  Q U A N T U M   I A   M 1           ║
║   👨‍🏫 Trader Profissional | 🅰️🅱️🅲️🅳️ Filtro     ║
║   🚫 Bloqueia 🅳️ ARRISCADO                  ║
║   🏆 3/5 Confirmam + Nota OK = Entra        ║
║   🔄 Gale 1 | ☁️ Cloud | 🕐 Brasil          ║
╚══════════════════════════════════════════════╝
"""
import asyncio, time, requests, numpy as np, signal, sys, json, os
from datetime import datetime, timedelta, timezone
from collections import deque
from pathlib import Path

signal.signal(signal.SIGCHLD, signal.SIG_IGN)

FUSO_BR = timezone(timedelta(hours=-3))

class C:
    G='\033[92m';Y='\033[93m';R='\033[91m';C='\033[96m';W='\033[97m';B='\033[1m';E='\033[0m';GOLD='\033[38;5;220m'

def clear(): os.system('clear 2>/dev/null || cls 2>/dev/null')

def banner():
    clear()
    print(f"{C.GOLD}{C.B}╔══════════════════════════════════════════════╗")
    print(f"║   ⚛️  Q U A N T U M   I A   M 1           ║")
    print(f"║   👨‍🏫 Trader Profissional | 🚫 Filtro 🅳️    ║")
    print(f"║   🏆 3/5 + Nota OK = Entra                ║")
    print(f"╚══════════════════════════════════════════════╝{C.E}")

CONFIG_FILE="config_quantum.json"

def carregar_config():
    cloud_token = os.environ.get('TELEGRAM_TOKEN')
    cloud_chat = os.environ.get('TELEGRAM_CHAT_ID')
    cloud_email = os.environ.get('IQ_EMAIL')
    cloud_senha = os.environ.get('IQ_SENHA')
    
    if cloud_token and cloud_chat and cloud_email and cloud_senha:
        banner()
        print(f"\n{C.G}✅ Modo CLOUD detectado!{C.E}\n")
        return {"token": cloud_token, "chat": cloud_chat, "email": cloud_email, "senha": cloud_senha}
    
    if Path(CONFIG_FILE).exists():
        with open(CONFIG_FILE) as f: cfg=json.load(f)
        if 'token' not in cfg: Path(CONFIG_FILE).unlink();return carregar_config()
        banner();print(f"\n{C.G}✅ Config carregada!{C.E}\n");return cfg
    
    banner()
    try:
        cfg={
            "token":input(f"{C.G}Token: {C.E}").strip(),
            "chat":input(f"{C.G}Chat ID: {C.E}").strip(),
            "email":input(f"\n{C.G}Email IQ: {C.E}").strip(),
            "senha":input(f"{C.G}Senha IQ: {C.E}").strip()
        }
    except (EOFError, KeyboardInterrupt):
        print(f"\n{C.R}❌ Configure as variáveis de ambiente!{C.E}")
        sys.exit(1)
    
    with open(CONFIG_FILE,'w') as f: json.dump(cfg,f,indent=2)
    banner();print(f"\n{C.G}✅ Salvo!{C.E}\n");return cfg

cfg=carregar_config()
TOKEN=cfg['token'];CHAT=cfg['chat'];EMAIL=cfg['email'];SENHA=cfg['senha']

from iqoptionapi.stable_api import IQ_Option

ATIVOS_OTC={"EURUSD":"EURUSD-OTC","GBPUSD":"GBPUSD-OTC","EURGBP":"EURGBP-OTC"}

class Placar:
    def __init__(self):self.w=0;self.l=0;self.g1=0;self.s=deque(maxlen=20)
    def win(self,g=0):
        self.w+=1
        if g==0:self.s.append('🟢');return"✅ WIN"
        else:self.g1+=1;self.s.append('🟡');return"✅ WIN GALE 1"
    def loss(self):self.l+=1;self.s.append('🔴');return"❌ LOSS"
    def zerar(self):self.w=0;self.l=0;self.g1=0;self.s.clear()

class Telegram:
    def __init__(self,t,c):self.u=f"https://api.telegram.org/bot{t}";self.c=c
    def send(self,txt):
        try:requests.post(f"{self.u}/sendMessage",json={"chat_id":self.c,"text":txt,"parse_mode":"Markdown"},timeout=5)
        except:pass

# ═══════════════════════════════════════════
# 5 ESTRATÉGIAS
# ═══════════════════════════════════════════
class Mortalha:
    def sma(self,d,p):
        try:
            if len(d)>=p:return sum(d[-p:])/p
            return sum(d)/len(d) if d else 0
        except:return 0
    def wma(self,d,p):
        try:
            if len(d)<p:return sum(d)/len(d) if d else 0
            w=np.arange(1,p+1);return np.sum(np.array(d[-p:])*w)/np.sum(w)
        except:return 0
    def analisar(self,v):
        try:
            if len(v)<30:return None,0
            c=np.array([x['close'] for x in v]);b1=np.zeros(len(c))
            for i in range(len(c)):
                if i>=33:b1[i]=self.sma(c[:i+1],1)-self.sma(c[:i+1],34)
            b2=np.zeros(len(b1))
            for i in range(len(b1)):
                if i>=3:b2[i]=self.wma(b1[:i+1],4)
            if b1[-1]>b2[-1] and b1[-2]<=b2[-2]:return'CALL',min(45+abs(b1[-1]-b2[-1])*10000,90)
            if b1[-1]<b2[-1] and b1[-2]>=b2[-2]:return'PUT',min(45+abs(b1[-1]-b2[-1])*10000,90)
            return None,0
        except:return None,0

class Formiga:
    def ema(self,p,pe):
        try:
            if len(p)<pe:return sum(p)/len(p) if p else 0
            return np.mean(p[-pe:])
        except:return 0
    def analisar(self,v):
        try:
            if len(v)<15:return None,0
            precos=np.array([x['close'] for x in v])
            ema5=self.ema(precos,5);ema10=self.ema(precos,10)
            dif=((ema5-ema10)/ema10)*100 if ema10>0 else 0
            sc=0;sp=0
            if dif>0.02:sc+=3
            elif dif>0.005:sc+=1
            elif dif<-0.02:sp+=3
            elif dif<-0.005:sp+=1
            if sc>=2 and sc>sp:return'CALL',min(50+sc*4,85)
            if sp>=2 and sp>sc:return'PUT',min(50+sp*4,85)
            return None,0
        except:return None,0

class Fortaleza:
    def rsi(self,p,pe=7):
        try:
            if len(p)<pe+1:return 50
            d=np.diff(list(p[-pe-1:]));g=np.where(d>0,d,0);l=np.where(d<0,-d,0)
            mg=np.mean(g) if len(g)>0 else 0;mp=np.mean(l) if len(l)>0 else 0
            if mp==0:return 100
            return 100-(100/(1+mg/mp))
        except:return 50
    def analisar(self,v):
        try:
            if len(v)<18:return None,0
            precos=np.array([x['close'] for x in v])
            rsi_val=self.rsi(precos)
            m=np.mean(precos[-10:]) if len(precos)>=10 else np.mean(precos)
            s=np.std(precos[-10:]) if len(precos)>=10 else 0
            bs=m+2*s;bi=m-2*s
            sc=0;sp=0
            if rsi_val<30:sc+=3
            elif rsi_val<40:sc+=2
            if rsi_val>70:sp+=3
            elif rsi_val>60:sp+=2
            if precos[-1]<=bi*1.0004:sc+=3
            if precos[-1]>=bs*0.9996:sp+=3
            if sc>=4 and sc>sp:return'CALL',min(60+sc*3,90)
            if sp>=4 and sp>sc:return'PUT',min(60+sp*3,90)
            return None,0
        except:return None,0

class RaioNegro:
    def analisar(self,v):
        try:
            if len(v)<12:return None,0
            precos=np.array([x['close'] for x in v])
            ema5=np.mean(precos[-5:]) if len(precos)>=5 else precos[-1]
            ema13=np.mean(precos[-13:]) if len(precos)>=13 else ema5
            macd=ema5-ema13;sinal=macd*0.5
            mom=precos[-1]-precos[-3] if len(precos)>=3 else 0
            sc=0;sp=0
            if macd>sinal and macd>0:sc+=3
            elif macd>sinal:sc+=1
            elif macd<sinal and macd<0:sp+=3
            elif macd<sinal:sp+=1
            if mom>0.00003:sc+=3
            elif mom>0:sc+=1
            elif mom<-0.00003:sp+=3
            elif mom<0:sp+=1
            if sc>=2 and sc>sp:return'CALL',min(48+sc*4,85)
            if sp>=2 and sp>sc:return'PUT',min(48+sp*4,85)
            return None,0
        except:return None,0

class Tsunami:
    def analisar(self,v):
        try:
            if len(v)<12:return None,0
            precos=np.array([x['close'] for x in v])
            altas=sum(1 for i in range(-min(5,len(v)-1),0) if precos[i]>precos[i-1])
            sc=0;sp=0
            if altas>=3:sc+=3
            elif altas<=2:sp+=3
            if sc>=2 and sc>sp:return'CALL',min(50+sc*3,85)
            if sp>=2 and sp>sc:return'PUT',min(50+sp*3,85)
            return None,0
        except:return None,0

# ═══════════════════════════════════════════
# ⚛️ QUANTUM IA - 3/5 CONFIRMAM
# ═══════════════════════════════════════════
class QuantumIA:
    def __init__(self):
        self.mortalha=Mortalha();self.formiga=Formiga();self.fortaleza=Fortaleza()
        self.raio_negro=RaioNegro();self.tsunami=Tsunami()
        self.min_estrategias=3
    def analisar_completo(self,v):
        try:
            if len(v)<30:return None,0,0,{}
            resultados=[];votos={'CALL':0,'PUT':0};confiancas={'CALL':[],'PUT':[]};detalhes={}
            estrategias=[('💀 Mortalha',self.mortalha),('🐜 Formiga',self.formiga),
                        ('🏰 Fortaleza',self.fortaleza),('⚡ Raio Negro',self.raio_negro),
                        ('🌊 Tsunami',self.tsunami)]
            for nome,est in estrategias:
                try:
                    d,c=est.analisar(v)
                    if d:resultados.append((nome,d,c));votos[d]+=1;confiancas[d].append(c);detalhes[nome]=f"{d} {c:.0f}%"
                    else:detalhes[nome]="⏸️"
                except:detalhes[nome]="❌"
            total=len(resultados)
            if total<self.min_estrategias:return None,0,total,detalhes
            if votos['CALL']>=self.min_estrategias and votos['CALL']>votos['PUT']:
                conf=np.mean(confiancas['CALL']);return'CALL',min(conf+(total-3)*4,95),total,detalhes
            if votos['PUT']>=self.min_estrategias and votos['PUT']>votos['CALL']:
                conf=np.mean(confiancas['PUT']);return'PUT',min(conf+(total-3)*4,95),total,detalhes
            return None,0,total,detalhes
        except:return None,0,0,{}
    def melhor_par(self,velas_dict,bloqueados,stats_pares):
        melhor=None;melhor_score=0
        for nome,velas in velas_dict.items():
            if nome in bloqueados:continue
            if len(velas)>=30:
                d,cf,num,det=self.analisar_completo(velas)
                if d:
                    score=cf+(num*5)
                    if nome in stats_pares and stats_pares[nome]['total']>=5:score+=stats_pares[nome]['taxa']*0.1
                    if score>melhor_score:melhor_score=score;melhor={'ativo':nome,'direcao':d,'confianca':cf,'estrategias':num,'detalhes':det}
        return melhor

# ═══════════════════════════════════════════
# 👨‍🏫 TRADER PROFISSIONAL
# ═══════════════════════════════════════════
class TraderProfessor:
    def __init__(self):
        self.historico=deque(maxlen=50)
        self.stats_pares={nome:{'wins':0,'losses':0,'total':0,'taxa':0} for nome in ATIVOS_OTC}
        self.tendencias={nome:"NEUTRA" for nome in ATIVOS_OTC}
        self.velas_dict={}
        self.losses=deque(maxlen=50)
        self.performance_horario={h:{'wins':0,'total':0} for h in range(24)}
        self.performance_dia={d:{'wins':0,'total':0} for d in ['Seg','Ter','Qua','Qui','Sex','Sab','Dom']}
    
    def atualizar_stats(self,ativo,resultado):
        if ativo in self.stats_pares:
            self.stats_pares[ativo]['total']+=1
            if resultado=='win':self.stats_pares[ativo]['wins']+=1
            else:self.stats_pares[ativo]['losses']+=1
            t=self.stats_pares[ativo]['total'];w=self.stats_pares[ativo]['wins']
            self.stats_pares[ativo]['taxa']=round((w/t)*100,1) if t>0 else 0
        h=datetime.now(FUSO_BR).hour
        self.performance_horario[h]['total']+=1
        if resultado=='win':self.performance_horario[h]['wins']+=1
        dias=['Seg','Ter','Qua','Qui','Sex','Sab','Dom']
        d=dias[datetime.now(FUSO_BR).weekday()]
        self.performance_dia[d]['total']+=1
        if resultado=='win':self.performance_dia[d]['wins']+=1
    
    def atualizar_dados(self,velas_dict):
        self.velas_dict=velas_dict
        for nome,velas in velas_dict.items():
            if len(velas)>=21:
                closes=[v['close'] for v in list(velas)[-21:]]
                ema9=np.mean(closes[-9:]);ema21=np.mean(closes[-21:])
                if ema9>ema21*1.0002:self.tendencias[nome]="ALTA 📈"
                elif ema9<ema21*0.9998:self.tendencias[nome]="BAIXA 📉"
                else:self.tendencias[nome]="NEUTRA ➡️"
    
    # ═══════════════════════════════════════
    # ANÁLISES DO MERCADO
    # ═══════════════════════════════════════
    
    def termometro(self,velas):
        if len(velas)<10:return "🌡️ Sem dados",50
        precos=[v['close'] for v in velas]
        vol=np.std(precos[-10:])/np.mean(precos[-10:]) if np.mean(precos[-10:])>0 else 0
        score_vol=min(vol*10000,40)
        altas=sum(1 for i in range(-5,0) if i>=-len(precos)+1 and precos[i]>precos[i-1])
        score_tend=abs(altas-2.5)*12
        volumes=[v.get('volume',0) for v in velas[-3:]]
        score_vol_media=min(np.mean(volumes)/100,30)
        score=score_vol+score_tend+score_vol_media
        if score>=70:return f"🔥 QUENTE ({score:.0f}/100)",score
        elif score>=40:return f"🌤️ MORNO ({score:.0f}/100)",score
        else:return f"❄️ FRIO ({score:.0f}/100)",score
    
    def detectar_range(self,velas):
        if len(velas)<20:return None
        precos=[v['close'] for v in velas]
        maximo=max(precos[-15:]);minimo=min(precos[-15:])
        range_pct=((maximo-minimo)/np.mean(precos[-15:]))*100 if np.mean(precos[-15:])>0 else 0
        if range_pct<0.04:return f"📦 RANGE ESTREITO - Operar nas bordas"
        elif range_pct<0.08:return f"📦 Range moderado"
        return None
    
    def contar_sequencia(self,velas):
        if len(velas)<10:return None
        direcoes=[]
        for i in range(-8,0):
            if i>=-len(velas)+1 and velas[i]['close']>velas[i-1]['close']:direcoes.append('ALTA')
            else:direcoes.append('BAIXA')
        if not direcoes:return None
        seq=1
        for i in range(len(direcoes)-2,-1,-1):
            if direcoes[i]==direcoes[-1]:seq+=1
            else:break
        if seq>=5:return f"⚠️ {seq} velas de {direcoes[-1]}! PROVÁVEL REVERSÃO!"
        elif seq>=3:return f"📈 {seq} velas de {direcoes[-1]}"
        return None
    
    def analisar_volume(self,velas):
        if len(velas)<5:return None
        volumes=[v.get('volume',0) for v in velas[-5:]]
        media=np.mean(volumes[:-1]);atual=volumes[-1]
        if media==0:return None
        razao=atual/media
        if razao>2.0:return "🔥 Volume EXPLOSIVO"
        elif razao>1.5:return "📊 Volume ACIMA da média"
        elif razao>1.0:return "📊 Volume normal"
        elif razao>0.5:return "⚠️ Volume BAIXO"
        else:return "🚫 Volume MUITO baixo"
    
    def analisar_correlacao(self):
        if not self.velas_dict:return None
        pares=list(self.velas_dict.keys())
        if len(pares)<2:return None
        correlacoes=[]
        for i in range(len(pares)):
            for j in range(i+1,len(pares)):
                v1=[x['close'] for x in list(self.velas_dict[pares[i]])[-10:]]
                v2=[x['close'] for x in list(self.velas_dict[pares[j]])[-10:]]
                if len(v1)>=10 and len(v2)>=10:
                    corr=np.corrcoef(v1,v2)[0][1]
                    if abs(corr)>0.7:
                        correlacoes.append(f"{pares[i]}↔️{pares[j]}:{'🟢JUNTOS' if corr>0 else '🔴OPOSTOS'}")
        if correlacoes:return "🔗 "+" | ".join(correlacoes)
        return None
    
    def analisar_horario(self):
        h=datetime.now(FUSO_BR).hour
        if h in[0,1,2,3,4,5]:return "🌙 Madrugada"
        elif h in[8,9,10,11]:return "☀️ Manhã"
        elif h in[14,15,16,17]:return "🔥 Tarde"
        elif h in[20,21,22]:return "🌆 Noite"
        else:return "🕐 Horário normal"
    
    def classificar_sinal(self,confianca,estrategias,pavio_ok,tendencia):
        nota=0
        if confianca>=75:nota+=3
        elif confianca>=65:nota+=2
        elif confianca>=55:nota+=1
        if estrategias>=4:nota+=3
        elif estrategias>=3:nota+=1
        if pavio_ok:nota+=2
        if 'NEUTRA' not in tendencia:nota+=2
        if nota>=8:return "🅰️ EXCELENTE"
        elif nota>=6:return "🅱️ BOM"
        elif nota>=4:return "🅲️ REGULAR"
        else:return "🅳️ ARRISCADO"
    
    # ═══════════════════════════════════════
    # NOVO: VERIFICA SE O SINAL DEVE SER ENVIADO
    # ═══════════════════════════════════════
    def sinal_enviado(self, sinal, velas):
        """Retorna (True, nota) se o sinal passar no filtro 🅳️"""
        direcao = sinal.get('direcao')
        confianca = sinal.get('confianca', 0)
        estrategias = sinal.get('estrategias', 0)
        tendencia = self.tendencias.get(sinal.get('ativo', ''), 'NEUTRA')
        
        # Analisa pavio
        pavio_ok = True
        try:
            if len(velas) >= 1:
                v = velas[-1]
                corpo = abs(v['close'] - v['open'])
                if corpo > 0:
                    if direcao == 'CALL':
                        ratio = (v['high'] - max(v['close'], v['open'])) / corpo
                        if ratio > 0.6: pavio_ok = False
                    else:
                        ratio = (min(v['close'], v['open']) - v['low']) / corpo
                        if ratio > 0.6: pavio_ok = False
        except:
            pass
        
        nota = self.classificar_sinal(confianca, estrategias, pavio_ok, tendencia)
        
        # 🚫 Bloqueia apenas 🅳️ ARRISCADO
        if nota == "🅳️ ARRISCADO":
            return False, nota
        return True, nota
    
    # ═══════════════════════════════════════
    # EXPLICAÇÕES
    # ═══════════════════════════════════════
    
    def ler_grafico(self,velas,direcao):
        if len(velas)<5:return"Poucas velas",[],True
        obs=[];v=velas[-1];v1=velas[-2]
        corpo=abs(v['close']-v['open']);range_total=v['high']-v['low']
        pavio_sup=v['high']-max(v['close'],v['open']);pavio_inf=min(v['close'],v['open'])-v['low']
        pavio_ok=True
        
        if direcao=='CALL':
            if pavio_inf>corpo*2 and pavio_sup<corpo*0.3:obs.append("🔨 Martelo - forte compra")
            elif corpo>abs(v1['close']-v1['open'])*1.5 and v['close']>v1['open']:obs.append("📈 Engolfo de alta")
            if pavio_sup>corpo*0.6:obs.append("⚠️ Pavio superior grande");pavio_ok=False
        else:
            if pavio_sup>corpo*2 and pavio_inf<corpo*0.3:obs.append("💫 Estrela cadente - forte venda")
            elif corpo>abs(v1['close']-v1['open'])*1.5 and v['close']<v1['open']:obs.append("📉 Engolfo de baixa")
            if pavio_inf>corpo*0.6:obs.append("⚠️ Pavio inferior grande");pavio_ok=False
        
        if corpo>range_total*0.6:obs.append("💪 Vela forte")
        precos=[x['close'] for x in velas]
        altas=sum(1 for i in range(-5,0) if i>=-len(precos)+1 and precos[i]>precos[i-1])
        if altas>=4:obs.append("📈 Tendência visual de alta")
        elif altas<=1:obs.append("📉 Tendência visual de baixa")
        else:obs.append("↔️ Sem direção clara")
        
        if not obs:obs.append("✅ Setup neutro")
        return" | ".join(obs),obs,pavio_ok
    
    def explicar_entrada(self,sinal,velas):
        ativo=sinal['ativo'];direcao=sinal['direcao'];est=sinal.get('estrategias',0);conf=sinal.get('confianca',0)
        detalhes=sinal.get('detalhes',{})
        leitura,obs,pavio_ok=self.ler_grafico(velas,direcao)
        tendencia=self.tendencias.get(ativo,'NEUTRA')
        nota=self.classificar_sinal(conf,est,pavio_ok,tendencia)
        termometro,score_term=self.termometro(velas)
        range_msg=self.detectar_range(velas)
        sequencia=self.contar_sequencia(velas)
        volume=self.analisar_volume(velas)
        correlacao=self.analisar_correlacao()
        horario=self.analisar_horario()
        
        concordaram=[k for k,v in detalhes.items() if '⚠️' not in str(v) and '⏸️' not in str(v) and '❌' not in str(v)]
        
        extras=[]
        if range_msg:extras.append(range_msg)
        if sequencia:extras.append(sequencia)
        if volume:extras.append(volume)
        if correlacao:extras.append(correlacao)
        extras_str="\n".join([f"• {e}" for e in extras]) if extras else "• Nenhum alerta adicional"
        
        return f"""👨‍🏫 *ANÁLISE DO TRADER PROFISSIONAL*

📊 *Mercado:* {tendencia}
🌡️ *Termômetro:* {termometro}
🕐 *Horário:* {horario}
👁️ *Gráfico:* {leitura}
📋 *Nota do Sinal:* {nota}

✅ *Estratégias ({est}/5):* {', '.join(concordaram) if concordaram else 'Nenhuma'}
🎯 *Decisão:* {direcao} com {conf:.0f}% de confiança

🔍 *Análises Adicionais:*
{extras_str}"""
    
    def explicar_loss(self,sinal,velas):
        ativo=sinal['ativo'];direcao=sinal['direcao'];conf=sinal.get('confianca',0)
        leitura,obs,pavio_ok=self.ler_grafico(velas,direcao)
        causas=[]
        v=velas[-1];corpo=abs(v['close']-v['open'])
        if corpo>0:
            if direcao=='CALL' and(v['high']-max(v['close'],v['open']))/corpo>0.6:causas.append("🕯️ Pavio superior grande")
            elif direcao=='PUT' and(min(v['close'],v['open'])-v['low'])/corpo>0.6:causas.append("🕯️ Pavio inferior grande")
        tendencia=self.tendencias.get(ativo,'NEUTRA')
        if direcao=='CALL' and 'BAIXA' in tendencia:causas.append("📉 Contra tendência de baixa")
        elif direcao=='PUT' and 'ALTA' in tendencia:causas.append("📈 Contra tendência de alta")
        if conf<58:causas.append("📊 Confiança baixa")
        if 'NEUTRA' in tendencia:causas.append("↔️ Mercado lateral")
        sequencia=self.contar_sequencia(velas)
        if sequencia and 'REVERSÃO' in sequencia:causas.append("🔄 Possível reversão por sequência")
        if not causas:causas.append("🎲 Movimento aleatório do mercado")
        
        self.losses.append({'ativo':ativo,'direcao':direcao,'confianca':conf,'causas':causas,'hora':datetime.now(FUSO_BR).hour})
        
        licao="Seguir o plano e gerenciar risco"
        if 'pavio' in str(causas).lower():licao="Sempre verificar pavios antes de entrar"
        elif 'tendência' in str(causas).lower():licao="Nunca operar contra a tendência principal"
        elif 'confiança' in str(causas).lower():licao="Esperar sinais com confiança mais alta"
        elif 'lateral' in str(causas).lower():licao="Evitar operar em mercado lateral"
        elif 'reversão' in str(causas).lower():licao="Respeitar sequências longas de velas"
        
        return f"""🧠 *ANÁLISE DO LOSS*

🔴 {ativo}-OTC {direcao} | {conf:.0f}%
👁️ *Gráfico:* {leitura}

🚫 *Causas Detectadas:*
{chr(10).join(f'• {c}' for c in causas)}

📚 *Lição do Professor:* {licao}"""
    
    def registrar(self,resultado):self.historico.append(1 if resultado=='win' else 0)

# ═══════════════════════════════════════════
# IQ API
# ═══════════════════════════════════════════
class IQAPI:
    def __init__(self,e,s,a):self.e=e;self.s=s;self.a=a;self.api=None;self.velas={nome:deque(maxlen=100) for nome in a};self.ok=False;self.erros=0
    def conectar(self):
        for t in range(5):
            try:
                if self.api:
                    try:self.api.close()
                    except:pass
                    time.sleep(2)
                self.api=IQ_Option(self.e,self.s);ok,_=self.api.connect()
                if ok:self.ok=True;self.erros=0;return True
                time.sleep(5*(t+1))
            except:time.sleep(5*(t+1))
        self.ok=False;return False
    def obter(self,ativo_id,qtd=80):
        for retry in range(3):
            if not self.ok and not self.conectar():return 0
            try:
                c=self.api.get_candles(ativo_id,60,qtd,time.time())
                if c and len(c)>0:
                    nome=[k for k,v in self.a.items() if v==ativo_id][0];self.velas[nome].clear()
                    for x in c[-qtd:]:
                        if isinstance(x,dict):
                            try:self.velas[nome].append({'time':datetime.fromtimestamp(x.get('from',0),FUSO_BR),'open':float(x['open']),'high':float(x['max']),'low':float(x['min']),'close':float(x['close']),'volume':int(x.get('volume',0))})
                            except:pass
                    return len(c)
            except:
                self.ok=False
                if retry<2:time.sleep(3);continue
        return 0
    def atualizar(self):
        if not self.ok:self.conectar()
        for n,i in self.a.items():
            try:self.obter(i)
            except:pass

# ═══════════════════════════════════════════
# BOT
# ═══════════════════════════════════════════
class Bot:
    def __init__(self):
        self.tg=Telegram(TOKEN,CHAT);self.m=QuantumIA();self.p=Placar();self.iq=IQAPI(EMAIL,SENHA,ATIVOS_OTC)
        self.professor=TraderProfessor()
        self.op=False;self.g=0;self.ult=0;self.sinais=0
        self.ultimo_sinal_ativo={};self.intervalo_minimo=180
        self.sinais_recusados=0  # 🚫 Contador de sinais bloqueados
        self.ultimo_dia=datetime.now(FUSO_BR).day;self.placar_enviado=False

    def pode_enviar(self,ativo):
        agora=time.time()
        if ativo in self.ultimo_sinal_ativo:
            if agora-self.ultimo_sinal_ativo[ativo]<self.intervalo_minimo:return False
        return True
    def registrar_envio(self,ativo):self.ultimo_sinal_ativo[ativo]=time.time()
    def _barra(self,pct):p=int(pct/10);return '█'*p+'░'*(10-p)

    def fechar_dia(self):
        agora=datetime.now(FUSO_BR);data=agora.strftime('%d/%m/%Y')
        dias={'Monday':'Segunda','Tuesday':'Terça','Wednesday':'Quarta','Thursday':'Quinta','Friday':'Sexta','Saturday':'Sábado','Sunday':'Domingo'}
        dia=dias.get(agora.strftime('%A'),'')
        w=self.p.w;g1=self.p.g1;l=self.p.l;total=max(w+l,1);tx=round((w/total)*100,1)
        lucro=round(w*1.6+g1*0.4-l*5,2)
        
        melhor_h=None;melhor_tx=0
        for h,data_h in self.professor.performance_horario.items():
            if data_h['total']>=3:
                tx_h=data_h['wins']/data_h['total']*100
                if tx_h>melhor_tx:melhor_tx=tx_h;melhor_h=h
        melhor_p=max(self.professor.stats_pares,key=lambda p:self.professor.stats_pares[p]['taxa'])
        
        msg=f"""📊 *PLACAR DIÁRIO FINALIZADO*

🗓️ *{data} ({dia})*
⏰ {agora.strftime('%H:%M')}

┌──────────────────────────┐
│ ⚛️ QUANTUM IA M1        │
│ 🟢 Wins: {w}              │
│ 🟡 Gale 1: {g1}            │
│ 🔴 Losses: {l}            │
│ 📨 Sinais: {w+g1+l}       │
│ 🎯 Assertividade: {tx}%   │
│ [{self._barra(tx)}]      │
│ 💰 Lucro: +R${lucro}      │
│ 🚫 Recusados: {self.sinais_recusados} │
├──────────────────────────┤
│ ⭐ Melhor horário: {melhor_h}h ({melhor_tx:.0f}%) │
│ 🏆 Melhor par: {melhor_p} ({self.professor.stats_pares[melhor_p]['taxa']}%) │
└──────────────────────────┘

🔄 *Placar zerado!*"""
        self.tg.send(msg)
        print(f"\n{C.GOLD}╔══════════════════════════════╗{C.E}")
        print(f"{C.GOLD}║ 📊 PLACAR DIÁRIO FINALIZADO ║{C.E}")
        print(f"{C.GOLD}║ 🟢{w}W 🟡{g1}G1 🔴{l}L 🎯{tx}% 💰+R${lucro} ║{C.E}")
        print(f"{C.GOLD}╚══════════════════════════════╝{C.E}\n")
        self.p.zerar();self.sinais=0;self.sinais_recusados=0
        print(f"  {C.G}🔄 Placar ZERADO! Novo dia!{C.E}\n")

    def fmt_sinal(self,s):
        agora=datetime.now(FUSO_BR)
        he=(agora.replace(second=0,microsecond=0)+timedelta(minutes=1)).strftime('%H:%M')
        e="🟢" if s['direcao']=='CALL' else "🔴"
        est=s.get('estrategias',0)
        return f"""⚛️ SINAL QUANTUM IA ⚛️

⏰ Horário: {he}
💰 Ativo: {s['ativo']}-OTC
📈 Direção: {s['direcao']} {e}
⌛️ Expiração: M1
📊 Confiança: {s['confianca']:.0f}%
🧠 Estratégias: {est}/5

⚠️ Entrar somente no horário marcado.
🔄 1 recuperação (Gale 1)!"""

    def fmt_corr(self,r,s):
        return f"""{r}
📊 {s['ativo']}-OTC | {s['direcao']} {'🟢' if s['direcao']=='CALL' else '🔴'}
📊 Placar: 🟢{self.p.w}W 🟡{self.p.g1}G1 🔴{self.p.l}L"""

    def bateu(self,d,p,v):return v['high']>p if d=='CALL' else v['low']<p

    async def esperar(self,seg=60):
        try:
            agora=datetime.now(FUSO_BR)
            alvo=agora.replace(second=0,microsecond=0)+timedelta(minutes=1)+timedelta(seconds=seg)
            e=max(0,(alvo-agora).total_seconds())
            if e>0:await asyncio.sleep(e)
            self.iq.atualizar()
        except:pass

    async def corrigir(self,sinal):
        at=sinal['ativo'];d=sinal['direcao']
        try:
            await self.esperar(8);v=self.iq.velas[at]
            if len(v)<2:self.op=False;return
            pc=v[-1]['open'];hora=v[-1]['time'].strftime('%H:%M')
            print(f"\n  ⚛️ {at}-OTC {d} | OPEN:{pc:.5f} | Vela:{hora}")
            await self.esperar(5);v=self.iq.velas[at]
            if len(v)>0 and self.bateu(d,pc,v[-1]):
                r=self.p.win(0);print(f"  ✅ {r}")
                self.tg.send(self.fmt_corr(r,sinal))
                self.professor.registrar('win');self.professor.atualizar_stats(at,'win')
                self.op=False;return
            print(f"  ❌ Principal")
            self.g=1;v=self.iq.velas[at];pg=v[-1]['open'] if len(v)>0 else pc
            print(f"  🔄 GALE 1 | OPEN:{pg:.5f}");await self.esperar(5);v=self.iq.velas[at]
            if len(v)>0 and self.bateu(d,pg,v[-1]):
                r=self.p.win(1);print(f"  ✅ {r}")
                self.tg.send(self.fmt_corr(r,sinal))
                self.professor.registrar('win');self.professor.atualizar_stats(at,'win')
                self.op=False;return
            print(f"  ❌ GALE 1");r=self.p.loss();print(f"  🔴 {r}")
            self.tg.send(self.fmt_corr(r,sinal))
            self.professor.registrar('loss');self.professor.atualizar_stats(at,'loss')
            explicacao=self.professor.explicar_loss(sinal,self.iq.velas[at])
            self.tg.send(explicacao)
            print(f"  🧠 Loss explicado!")
            self.op=False
        except Exception as e:print(f"  ❌ {e}");self.op=False

    async def catalogacao_inicial(self):
        print(f"\n  {C.GOLD}📊 CATALOGAÇÃO INICIAL (80 velas){C.E}")
        for nome in ATIVOS_OTC:
            velas=self.iq.velas[nome]
            if len(velas)<35:print(f"  {C.Y}⚠️ {nome}: Poucas velas{C.E}");continue
            wins=0;total=0
            for i in range(35,len(velas)-1):
                janela=list(velas)[i-35:i+1];d,cf,num,det=self.m.analisar_completo(janela)
                if d:
                    total+=1;vela_seguinte=list(velas)[i+1]
                    if self.bateu(d,vela_seguinte['open'],vela_seguinte):wins+=1
            if total>0:
                self.professor.stats_pares[nome]['wins']=wins
                self.professor.stats_pares[nome]['total']=total
                self.professor.stats_pares[nome]['taxa']=round((wins/total)*100,1)
                print(f"  {C.G}✅ {nome}: {wins}/{total} ({self.professor.stats_pares[nome]['taxa']}%){C.E}")

    async def run(self):
        banner()
        print(f"\n  ⚛️ Iniciando Quantum IA - Trader Profissional com Filtro 🅳️...\n")
        print(f"  🕐 Horário Brasil: {datetime.now(FUSO_BR).strftime('%H:%M:%S')}\n")
        if not self.iq.conectar():print(f"  ❌ Falha conexão!");return
        self.iq.atualizar();await self.catalogacao_inicial()
        self.ultimo_dia=datetime.now(FUSO_BR).day
        print(f"\n  ✅ QUANTUM IA | 👨‍🏫 Trader Profissional | 🚫 Filtro 🅳️ | 🏆 3/5 + Nota OK\n")
        self.tg.send(f"⚛️ *QUANTUM IA - TRADER PROFISSIONAL*\n🚫 Bloqueando sinais 🅳️ ARRISCADO\n🏆 3/5 Estratégias + Nota OK\n⏰ {datetime.now(FUSO_BR).strftime('%H:%M:%S')}")

        while True:
            try:
                agora=datetime.now(FUSO_BR)
                if agora.hour==23 and agora.minute==59 and not self.placar_enviado:
                    self.fechar_dia();self.placar_enviado=True
                if agora.day!=self.ultimo_dia:self.ultimo_dia=agora.day;self.placar_enviado=False
                if agora.second in[0,30]:
                    try:self.iq.atualizar();self.professor.atualizar_dados(self.iq.velas)
                    except:self.iq.ok=False
                if not self.op:
                    try:
                        bloqueados=[a for a in ATIVOS_OTC if not self.pode_enviar(a)]
                        sinal=self.m.melhor_par(self.iq.velas,bloqueados,self.professor.stats_pares)
                        if sinal and time.time()-self.ult>25:
                            # 🚫 NOVO: Verifica se o sinal deve ser enviado (filtro 🅳️)
                            enviar, nota = self.professor.sinal_enviado(sinal, self.iq.velas[sinal['ativo']])
                            if enviar:
                                self.op=True;self.sinais+=1;self.registrar_envio(sinal['ativo'])
                                he=(agora.replace(second=0,microsecond=0)+timedelta(minutes=1)).strftime('%H:%M')
                                print(f"\n⚛️ #{self.sinais} {sinal['ativo']}-OTC {sinal['direcao']} | {sinal['confianca']:.0f}% | {sinal.get('estrategias',0)}/5 | Nota: {nota} | ⏰ {he}")
                                self.tg.send(self.fmt_sinal(sinal))
                                explicacao=self.professor.explicar_entrada(sinal,self.iq.velas[sinal['ativo']])
                                self.tg.send(explicacao)
                                self.ult=time.time()
                                asyncio.create_task(self.corrigir(sinal))
                            else:
                                self.sinais_recusados+=1
                                print(f"  {C.Y}🚫 Sinal BLOQUEADO ({sinal['ativo']}-OTC {sinal['direcao']}): Nota {nota}{C.E}")
                    except:pass
                if agora.second in[0,30]:
                    try:
                        w,l,g1=self.p.w,self.p.l,self.p.g1;t=max(w+l,1);tx=round((w/t)*100,1)
                        lucro=round(w*1.6+g1*0.4-l*5,2)
                        print(f"{C.GOLD}┌──────────────────────────────────────────────────────┐{C.E}")
                        print(f"{C.GOLD}│{C.E} ⏰ {agora.strftime('%H:%M:%S')} | 📨{self.sinais} | 🟢{w}W 🟡{g1}G1 🔴{l}L 🎯{tx}% | 💰+R${lucro} | 🚫{self.sinais_recusados}")
                        print(f"{C.GOLD}└──────────────────────────────────────────────────────┘{C.E}")
                    except:pass
                await asyncio.sleep(3)
            except KeyboardInterrupt:
                clear();w,l,g1=self.p.w,self.p.l,self.p.g1;t=max(w+l,1);tx=round((w/t)*100,1)
                lucro=round(w*1.6+g1*0.4-l*5,2)
                print(f"\n👋 🟢{w}W 🟡{g1}G1 🔴{l}L | 🎯{tx}% | 💰+R${lucro} | 🚫{self.sinais_recusados}\n")
                self.tg.send(f"⚠️ *Desligado*\n🟢{w}W 🟡{g1}G1 🔴{l}L\n🎯{tx}%\n💰+R${lucro}\n🚫{self.sinais_recusados} recusados")
                if self.iq.api:
                    try:self.iq.api.close()
                    except:pass
                break
            except Exception as e:
                print(f"  {C.R}❌ {str(e)[:40]}{C.E}");self.iq.ok=False;await asyncio.sleep(5)

if __name__=="__main__":
    asyncio.run(Bot().run())
