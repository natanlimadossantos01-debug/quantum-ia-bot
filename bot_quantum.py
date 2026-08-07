#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════╗
║   ⚛️  Q U A N T U M   I A   M 1           ║
║   🧠 Catalogador Inteligente | Máxima Assertividade ║
║   🎯 65% Taxa Mínima | 🔥 65% Confiança    ║
║   🔄 Troca Rápida | 🛡️ Filtro Pavio        ║
║   👨‍🏫 Trader Professor | ⚔️ Samurai          ║
║   📊 26 Estratégias | 4 Pares OTC          ║
║   ⚡ SEM Bloqueio | ☁️ Cloud Ready          ║
╚══════════════════════════════════════════════╝
"""
import asyncio, time, requests, numpy as np, signal, sys, json, os, random
from datetime import datetime, timedelta, timezone
from collections import deque, defaultdict
from pathlib import Path

signal.signal(signal.SIGCHLD, signal.SIG_IGN)

FUSO_BR = timezone(timedelta(hours=-3))

FILOSOFIA_SAMURAI = [
    "⚔️ A vitória começa na execução perfeita, não no resultado.",
    "🎯 O objetivo é o trade certo, não o dinheiro.",
    "🧘 Aceite a perda como parte do caminho do guerreiro.",
    "🐉 O mercado é um oponente vivo. Respeite-o.",
    "🕯️ Cada vela é uma batalha. Cada dia, uma guerra.",
    "⏳ Paciência é arma. Espere a confirmação.",
    "🌊 A tendência é sua amiga. Não a desafie.",
    "🛡️ O stop é o escudo do samurai. Use-o com honra.",
    "📚 O verdadeiro guerreiro estuda seus erros.",
    "🧠 Mente vazia, espírito pronto. Sem emoção.",
    "🔥 Paixão pelo processo, não pelo resultado.",
    "⛩️ Disciplina é o alicerce do trader samurai.",
    "⚡ O momento da execução é tudo. Hesitação é derrota.",
    "🏔️ A montanha do lucro se conquista com paciência.",
    "🌅 Cada amanhecer traz uma nova oportunidade de batalha."
]

def get_filosofia():
    return random.choice(FILOSOFIA_SAMURAI)

class C:
    G='\033[92m';Y='\033[93m';R='\033[91m';C='\033[96m';W='\033[97m';B='\033[1m';E='\033[0m';GOLD='\033[38;5;220m'

def clear(): os.system('clear 2>/dev/null || cls 2>/dev/null')

def banner():
    clear()
    print(f"{C.GOLD}{C.B}╔══════════════════════════════════════════════╗")
    print(f"║   ⚛️  Q U A N T U M   I A   M 1           ║")
    print(f"║   🧠 Máxima Assertividade | 🔥 65%+        ║")
    print(f"║   🎯 65% Taxa Mínima | 🛡️ Filtro Pavio    ║")
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

ATIVOS_OTC={
    "EURUSD":"EURUSD-OTC",
    "GBPUSD":"GBPUSD-OTC",
    "EURGBP":"EURGBP-OTC",
    "EURJPY":"EURJPY-OTC"
}

class Placar:
    def __init__(self):self.w=0;self.l=0;self.g1=0;self.s=deque(maxlen=20);self.ops=[]
    def win(self,g=0):
        if g==0:self.w+=1;self.s.append('🟢');return"✅ WIN"
        else:self.g1+=1;self.s.append('🟡');return"✅ WIN GALE 1"
    def loss(self):self.l+=1;self.s.append('🔴');return"❌ LOSS"
    def registrar(self,ativo,direcao,conf,resultado,is_gale=False):
        agora=datetime.now(FUSO_BR);hora=agora.strftime('%H:%M')
        sufixo="¹" if is_gale else "";emoji="✅️" if "WIN" in resultado else "🔴"
        self.ops.append(f"M1 {ativo}-OTC {direcao} {hora} {emoji}{sufixo}")
    def zerar(self):self.w=0;self.l=0;self.g1=0;self.s.clear();self.ops.clear()

class Telegram:
    def __init__(self,t,c):self.u=f"https://api.telegram.org/bot{t}";self.c=c
    def send(self,txt):
        try:requests.post(f"{self.u}/sendMessage",json={"chat_id":self.c,"text":txt,"parse_mode":"Markdown"},timeout=5)
        except:pass

# ═══════════════════════════════════════════
# 🧠 CATALOGADOR INTELIGENTE (OTIMIZADO)
# ═══════════════════════════════════════════
class CatalogadorInteligente:
    def __init__(self):
        self.performance = {}
        self.combinacao_atual = None
        self.sinais_na_combinacao = 0
        self.max_sinais_por_combinacao = 1
        self.taxa_minima = 65
        self.min_operacoes = 5
        self.total_operacoes = 0
        self.ultimo_relatorio = 0
        
    def registrar(self, estrategia, par, venceu):
        chave = f"{estrategia}|{par}"
        if chave not in self.performance:
            self.performance[chave] = {'wins': 0, 'losses': 0, 'total': 0, 'estrategia': estrategia, 'par': par}
        self.performance[chave]['total'] += 1
        if venceu: self.performance[chave]['wins'] += 1
        else: self.performance[chave]['losses'] += 1
        self.total_operacoes += 1
    
    def get_taxa(self, estrategia, par):
        chave = f"{estrategia}|{par}"
        if chave in self.performance:
            p = self.performance[chave]
            return round((p['wins']/p['total'])*100, 1) if p['total'] > 0 else 0
        return 0
    
    def get_melhores(self, min_ops=5):
        melhores = []
        for chave, p in self.performance.items():
            if p['total'] >= min_ops:
                taxa = (p['wins']/p['total'])*100
                if taxa >= self.taxa_minima:
                    melhores.append({
                        'estrategia': p['estrategia'],
                        'par': p['par'],
                        'taxa': round(taxa, 1),
                        'total': p['total'],
                        'wins': p['wins'],
                        'losses': p['losses']
                    })
        melhores.sort(key=lambda x: x['taxa'], reverse=True)
        return melhores
    
    def escolher_melhor(self):
        melhores = self.get_melhores(self.min_operacoes)
        return melhores[0] if melhores else None
    
    def precisa_trocar(self):
        if not self.combinacao_atual: return True
        if self.sinais_na_combinacao >= self.max_sinais_por_combinacao: return True
        taxa_atual = self.get_taxa(self.combinacao_atual['estrategia'], self.combinacao_atual['par'])
        if taxa_atual < self.taxa_minima: return True
        melhor = self.escolher_melhor()
        if melhor and melhor['taxa'] > taxa_atual + 5: return True
        return False
    
    def atualizar_combinacao(self):
        if self.precisa_trocar():
            melhor = self.escolher_melhor()
            if melhor:
                self.combinacao_atual = {'estrategia': melhor['estrategia'], 'par': melhor['par'], 'taxa': melhor['taxa']}
                self.sinais_na_combinacao = 0
                return True, melhor
        return False, self.combinacao_atual
    
    def get_relatorio(self):
        melhores = self.get_melhores(2)
        if not melhores: return None
        msg = "📊 *CATALOGADOR INTELIGENTE*\n"
        msg += f"📈 Total: {self.total_operacoes} operações\n"
        if self.combinacao_atual:
            msg += f"🎯 *Atual:* {self.combinacao_atual['estrategia']} em {self.combinacao_atual['par']} ({self.combinacao_atual['taxa']}%)\n"
        msg += f"\n🏆 *Top Combinações:*\n"
        for i, m in enumerate(melhores[:6], 1):
            emoji = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else "📊"
            msg += f"{emoji} {m['estrategia']} | {m['par']}\n   {m['taxa']}% | {m['wins']}W/{m['losses']}L ({m['total']} ops)\n"
        return msg

# ═══════════════════════════════════════════
# 26 ESTRATÉGIAS
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

class FundoTopo:
    def analisar(self,v):
        try:
            if len(v)<15:return None,0
            precos=[x['close'] for x in v]
            max_10=max(precos[-10:]);min_10=min(precos[-10:]);atual=precos[-1]
            if min_10>0 and(atual-min_10)/min_10<0.0003:return'CALL',82
            if atual>0 and(max_10-atual)/atual<0.0003:return'PUT',82
            return None,0
        except:return None,0

class Sequencia:
    def analisar(self,v):
        try:
            if len(v)<6:return None,0
            precos=[x['close'] for x in v]
            altas=sum(1 for i in range(-3,0) if precos[i]>precos[i-1])
            if altas==3:return'PUT',78
            if altas==0:return'CALL',78
            return None,0
        except:return None,0

class Rejeicao:
    def analisar(self,v):
        try:
            if len(v)<3:return None,0
            vela=v[-1];corpo=abs(vela['close']-vela['open'])
            if corpo==0:return None,0
            pavio_sup=vela['high']-max(vela['close'],vela['open'])
            pavio_inf=min(vela['close'],vela['open'])-vela['low']
            if pavio_inf>corpo*3:return'CALL',85
            if pavio_sup>corpo*3:return'PUT',85
            return None,0
        except:return None,0

class MHI1_Adaptada:
    def analisar(self,v):
        try:
            if len(v)<8:return None,0
            velas_ant=v[-6:-3];ups=sum(1 for x in velas_ant if x['close']>x['open']);downs=3-ups
            if 0<ups<downs:return'CALL',72
            if 0<downs<ups:return'PUT',72
            return None,0
        except:return None,0

class Vituxo_Adaptada:
    def analisar(self,v):
        try:
            if len(v)<8:return None,0
            velas_ant=v[-8:-5];ups=sum(1 for x in velas_ant if x['close']>x['open']);downs=3-ups
            if ups>downs:return'CALL',70
            if downs>ups:return'PUT',70
            return None,0
        except:return None,0

class MilhaoMinoria_Adaptada:
    def analisar(self,v):
        try:
            if len(v)<10:return None,0
            velas_ant=v[-10:-5];ups=sum(1 for x in velas_ant if x['close']>x['open']);downs=5-ups
            if 0<ups<downs:return'CALL',74
            if 0<downs<ups:return'PUT',74
            return None,0
        except:return None,0

class DAKA_Adaptada:
    def analisar(self,v):
        try:
            if len(v)<9:return None,0
            vela_ref=v[-6]
            if vela_ref['close']>vela_ref['open']:return'CALL',68
            if vela_ref['close']<vela_ref['open']:return'PUT',68
            return None,0
        except:return None,0

class MHI2_Quadrante:
    def analisar(self,v):
        try:
            if len(v)<10:return None,0
            velas_ant=v[-6:-3];ups=sum(1 for x in velas_ant if x['close']>x['open']);downs=3-ups
            if 0<ups<downs:return'CALL',70
            if 0<downs<ups:return'PUT',70
            return None,0
        except:return None,0

class MHI3_Quadrante:
    def analisar(self,v):
        try:
            if len(v)<10:return None,0
            velas_ant=v[-6:-3];ups=sum(1 for x in velas_ant if x['close']>x['open']);downs=3-ups
            if 0<ups<downs:return'CALL',68
            if 0<downs<ups:return'PUT',68
            return None,0
        except:return None,0

class C3_Quadrante:
    def analisar(self,v):
        try:
            if len(v)<7:return None,0
            vela_ref=v[-6]
            if vela_ref['close']>vela_ref['open']:return'CALL',65
            if vela_ref['close']<vela_ref['open']:return'PUT',65
            return None,0
        except:return None,0

class MSF_Quadrante:
    def analisar(self,v):
        try:
            if len(v)<7:return None,0
            vela_ref=v[-6]
            if vela_ref['close']>vela_ref['open']:return'PUT',65
            if vela_ref['close']<vela_ref['open']:return'CALL',65
            return None,0
        except:return None,0

class MilhaoMaioria_Quadrante:
    def analisar(self,v):
        try:
            if len(v)<10:return None,0
            velas_ant=v[-10:-5];ups=sum(1 for x in velas_ant if x['close']>x['open']);downs=5-ups
            if ups>downs:return'CALL',72
            if downs>ups:return'PUT',72
            return None,0
        except:return None,0

class TresVizinhos_Quadrante:
    def analisar(self,v):
        try:
            if len(v)<5:return None,0
            vela_ref=v[-2]
            if vela_ref['close']>vela_ref['open']:return'CALL',66
            if vela_ref['close']<vela_ref['open']:return'PUT',66
            return None,0
        except:return None,0

class Estrategia23_Quadrante:
    def analisar(self,v):
        try:
            if len(v)<5:return None,0
            vela_ref=v[-3]
            if vela_ref['close']>vela_ref['open']:return'CALL',64
            if vela_ref['close']<vela_ref['open']:return'PUT',64
            return None,0
        except:return None,0

class R7_Quadrante:
    def analisar(self,v):
        try:
            if len(v)<14:return None,0
            vela_ref=v[-14]
            if vela_ref['close']>vela_ref['open']:return'CALL',62
            if vela_ref['close']<vela_ref['open']:return'PUT',62
            return None,0
        except:return None,0

class Estrategia520:
    def analisar(self,v):
        try:
            if len(v)<25:return None,0
            precos=[x['close'] for x in v]
            mm5=np.mean(precos[-5:])
            media20=np.mean(precos[-20:]);std20=np.std(precos[-20:])
            bs=media20+2*std20;bi=media20-2*std20;atual=precos[-1]
            if atual>mm5 and atual<=bi*1.002:return'CALL',78
            if atual<mm5 and atual>=bs*0.998:return'PUT',78
            return None,0
        except:return None,0

class Chinesa30:
    def analisar(self,v):
        try:
            if len(v)<30:return None,0
            precos=[x['close'] for x in v];highs=[x['high'] for x in v];lows=[x['low'] for x in v]
            ma20=np.mean(precos[-20:])
            suporte=min(lows[-10:]);resistencia=max(highs[-10:])
            atual=precos[-1]
            if atual>ma20 and highs[-1]>resistencia:return'CALL',80
            if atual<ma20 and lows[-1]<suporte:return'PUT',80
            return None,0
        except:return None,0

class SegueTendencia:
    def analisar(self,v):
        try:
            if len(v)<8:return None,0
            precos=[x['close'] for x in v]
            altas=sum(1 for i in range(-4,0) if precos[i]>precos[i-1])
            if altas>=3:return'CALL',67
            if altas<=1:return'PUT',67
            return None,0
        except:return None,0

class Rompimento:
    def analisar(self,v):
        try:
            if len(v)<5:return None,0
            precos=[x['close'] for x in v];highs=[x['high'] for x in v];lows=[x['low'] for x in v]
            max_3=max(highs[-4:-1]);min_3=min(lows[-4:-1])
            if precos[-1]>max_3:return'CALL',75
            if precos[-1]<min_3:return'PUT',75
            return None,0
        except:return None,0

class ForcaTendencia:
    def analisar(self,v):
        try:
            if len(v)<12:return None,0
            precos=[x['close'] for x in v]
            ema5=np.mean(precos[-5:]);ema10=np.mean(precos[-10:])
            if ema5>ema10*1.0003:return'CALL',70
            if ema5<ema10*0.9997:return'PUT',70
            return None,0
        except:return None,0

class ReversaoRapida:
    def analisar(self,v):
        try:
            if len(v)<4:return None,0
            v1=v[-1];v2=v[-2]
            if v2['close']>v2['open'] and v1['close']<v1['open']:return'PUT',68
            if v2['close']<v2['open'] and v1['close']>v1['open']:return'CALL',68
            return None,0
        except:return None,0

# ═══════════════════════════════════════════
# ⚛️ QUANTUM IA - CATALOGADOR DINÂMICO
# ═══════════════════════════════════════════
class QuantumIA:
    def __init__(self):
        self.estrategias=[
            ('💀 Mortalha',Mortalha()),('🐜 Formiga',Formiga()),('🏰 Fortaleza',Fortaleza()),
            ('⚡ Raio Negro',RaioNegro()),('🌊 Tsunami',Tsunami()),('🔥 Fundo/Topo',FundoTopo()),
            ('🔄 Sequência',Sequencia()),('🕯️ Rejeição',Rejeicao()),
            ('📊 MHI 1',MHI1_Adaptada()),('📊 VITUXO',Vituxo_Adaptada()),
            ('📊 Milhão Min',MilhaoMinoria_Adaptada()),('📊 DAKA',DAKA_Adaptada()),
            ('📊 MHI 2',MHI2_Quadrante()),('📊 MHI 3',MHI3_Quadrante()),
            ('📊 C3',C3_Quadrante()),('📊 MSF',MSF_Quadrante()),
            ('📊 Milhão Maj',MilhaoMaioria_Quadrante()),('📊 3 Vizinhos',TresVizinhos_Quadrante()),
            ('📊 23',Estrategia23_Quadrante()),('📊 R7',R7_Quadrante()),
            ('🔬 5-2-0',Estrategia520()),('🔬 Chinesa 3.0',Chinesa30()),
            ('📈 Segue Tend',SegueTendencia()),('💥 Rompimento',Rompimento()),
            ('💪 Força Tend',ForcaTendencia()),('🔄 Reversão',ReversaoRapida())
        ]
        self.catalogador=CatalogadorInteligente()
        self.sinais_bloqueados_pavio=0

    def analisar_estrategia(self, nome_estrategia, velas):
        for nome, est in self.estrategias:
            if nome == nome_estrategia:
                try: return est.analisar(velas)
                except: return None, 0
        return None, 0

    def obter_sinal_dinamico(self, velas_dict, bloqueados):
        trocou, combinacao = self.catalogador.atualizar_combinacao()
        if trocou and combinacao:
            print(f"  🧠 Nova combinação: {combinacao['estrategia']} em {combinacao['par']} ({combinacao['taxa']}%)")
        if not combinacao:
            return self._buscar_qualquer_sinal(velas_dict, bloqueados)
        par = combinacao['par']; estrategia_nome = combinacao['estrategia']
        if par in velas_dict and par not in bloqueados and len(velas_dict[par]) >= 30:
            d, c = self.analisar_estrategia(estrategia_nome, velas_dict[par])
            # 🔥 Só aceita confiança >= 65%
            if d and c >= 65 and self._pavio_ok(velas_dict[par], d):
                return {'ativo': par, 'direcao': d, 'confianca': c, 'estrategia': estrategia_nome, 'estrategias': 1, 'detalhes': {estrategia_nome: f"{d} {c:.0f}%"}}
            elif d and c < 65:
                pass  # Confiança baixa, ignora
            elif d:
                self.sinais_bloqueados_pavio += 1
        return self._buscar_qualquer_sinal(velas_dict, bloqueados)
    
    def _pavio_ok(self, velas, direcao):
        if len(velas) < 1: return True
        va = velas[-1]; corpo = abs(va['close'] - va['open'])
        if corpo == 0: return True
        if direcao == 'CALL':
            pavio_sup = va['high'] - max(va['close'], va['open'])
            return pavio_sup <= corpo * 0.6
        else:
            pavio_inf = min(va['close'], va['open']) - va['low']
            return pavio_inf <= corpo * 0.6
    
    def _buscar_qualquer_sinal(self, velas_dict, bloqueados):
        melhor = None; melhor_score = 0
        for nome_par, velas in velas_dict.items():
            if nome_par in bloqueados: continue
            if len(velas) < 30: continue
            for nome_est, est in self.estrategias:
                try:
                    d, c = est.analisar(velas)
                    # 🔥 NOVO: Só aceita confiança >= 65%
                    if d and c >= 65 and self._pavio_ok(velas, d):
                        score = c
                        taxa = self.catalogador.get_taxa(nome_est, nome_par)
                        if taxa > 60: score += taxa * 0.5  # Mais peso
                        if score > melhor_score:
                            melhor_score = score
                            melhor = {'ativo': nome_par, 'direcao': d, 'confianca': c, 'estrategia': nome_est, 'estrategias': 1, 'detalhes': {nome_est: f"{d} {c:.0f}%"}}
                except: pass
        return melhor

# ═══════════════════════════════════════════
# 👨‍🏫 TRADER PROFESSOR
# ═══════════════════════════════════════════
class TraderProfessor:
    def __init__(self):
        self.historico=deque(maxlen=50)
        self.stats_pares={nome:{'wins':0,'losses':0,'total':0,'taxa':0} for nome in ATIVOS_OTC}
        self.tendencias={nome:"NEUTRA" for nome in ATIVOS_OTC}
        self.losses=deque(maxlen=50)
    
    def atualizar_stats(self,ativo,resultado):
        if ativo in self.stats_pares:
            self.stats_pares[ativo]['total']+=1
            if resultado=='win':self.stats_pares[ativo]['wins']+=1
            else:self.stats_pares[ativo]['losses']+=1
            t=self.stats_pares[ativo]['total'];w=self.stats_pares[ativo]['wins']
            self.stats_pares[ativo]['taxa']=round((w/t)*100,1) if t>0 else 0
    
    def atualizar_dados(self,velas_dict):
        for nome,velas in velas_dict.items():
            if len(velas)>=21:
                closes=[v['close'] for v in list(velas)[-21:]]
                ema9=np.mean(closes[-9:]);ema21=np.mean(closes[-21:])
                if ema9>ema21*1.0002:self.tendencias[nome]="ALTA 📈"
                elif ema9<ema21*0.9998:self.tendencias[nome]="BAIXA 📉"
                else:self.tendencias[nome]="NEUTRA ➡️"
    
    def ler_grafico(self,velas,direcao):
        if len(velas)<5:return"Poucas velas",[],True
        obs=[];v=velas[-1];v1=velas[-2]
        corpo=abs(v['close']-v['open']);range_total=v['high']-v['low']
        pavio_sup=v['high']-max(v['close'],v['open']);pavio_inf=min(v['close'],v['open'])-v['low']
        pavio_ok=True
        if direcao=='CALL':
            if pavio_inf>corpo*2 and pavio_sup<corpo*0.3:obs.append("🔨 Martelo")
            elif corpo>abs(v1['close']-v1['open'])*1.5 and v['close']>v1['open']:obs.append("📈 Engolfo alta")
            if pavio_sup>corpo*0.6:obs.append("⚠️ Pavio superior");pavio_ok=False
        else:
            if pavio_sup>corpo*2 and pavio_inf<corpo*0.3:obs.append("💫 Estrela cadente")
            elif corpo>abs(v1['close']-v1['open'])*1.5 and v['close']<v1['open']:obs.append("📉 Engolfo baixa")
            if pavio_inf>corpo*0.6:obs.append("⚠️ Pavio inferior");pavio_ok=False
        if corpo>range_total*0.6:obs.append("💪 Vela forte")
        precos=[x['close'] for x in velas]
        altas=sum(1 for i in range(-5,0) if i>=-len(precos)+1 and precos[i]>precos[i-1])
        if altas>=4:obs.append("📈 Tendência alta")
        elif altas<=1:obs.append("📉 Tendência baixa")
        else:obs.append("↔️ Sem direção")
        if not obs:obs.append("✅ Setup neutro")
        return" | ".join(obs),obs,pavio_ok
    
    def explicar_entrada(self,sinal,velas):
        ativo=sinal['ativo'];direcao=sinal['direcao'];conf=sinal.get('confianca',0)
        est=sinal.get('estrategia','N/A')
        leitura,obs,pavio_ok=self.ler_grafico(velas,direcao)
        tendencia=self.tendencias.get(ativo,'NEUTRA')
        filosofia=get_filosofia()
        return f"""👨‍🏫 *ANÁLISE DO TRADER*

📊 *Mercado:* {tendencia}
👁️ *Gráfico:* {leitura}
🧠 *Estratégia:* {est}
🎯 *Decisão:* {direcao} com {conf:.0f}% de confiança
⚔️ _{filosofia}_"""
    
    def explicar_loss(self,sinal,velas):
        ativo=sinal['ativo'];direcao=sinal['direcao'];conf=sinal.get('confianca',0)
        leitura,obs,pavio_ok=self.ler_grafico(velas,direcao)
        causas=[];v=velas[-1];corpo=abs(v['close']-v['open'])
        if corpo>0:
            if direcao=='CALL' and(v['high']-max(v['close'],v['open']))/corpo>0.6:causas.append("🕯️ Pavio superior grande")
            elif direcao=='PUT' and(min(v['close'],v['open'])-v['low'])/corpo>0.6:causas.append("🕯️ Pavio inferior grande")
        tendencia=self.tendencias.get(ativo,'NEUTRA')
        if direcao=='CALL' and 'BAIXA' in tendencia:causas.append("📉 Contra tendência")
        elif direcao=='PUT' and 'ALTA' in tendencia:causas.append("📈 Contra tendência")
        if conf<65:causas.append("📊 Confiança baixa (<65%)")
        if not causas:causas.append("🎲 Movimento aleatório")
        self.losses.append({'ativo':ativo,'direcao':direcao,'confianca':conf,'causas':causas,'hora':datetime.now(FUSO_BR).hour})
        licao="Seguir o plano"
        if 'pavio' in str(causas).lower():licao="Verificar pavios antes de entrar"
        elif 'tendência' in str(causas).lower():licao="Não operar contra tendência"
        elif 'confiança' in str(causas).lower():licao="Esperar confiança mais alta (65%+)"
        filosofia=get_filosofia()
        return f"""🧠 *ANÁLISE DO LOSS*

🔴 {ativo}-OTC {direcao} | {conf:.0f}%
🚫 *Causas:* {', '.join(causas)}
📚 *Lição:* {licao}
⚔️ _{filosofia}_"""
    
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
        self.ultimo_dia=datetime.now(FUSO_BR).day;self.placar_enviado=False

    def _barra(self,pct):p=int(pct/10);return '█'*p+'░'*(10-p)

    def fechar_dia(self):
        agora=datetime.now(FUSO_BR);data=agora.strftime('%d/%m/%Y')
        dias={'Monday':'Segunda','Tuesday':'Terça','Wednesday':'Quarta','Thursday':'Quinta','Friday':'Sexta','Saturday':'Sábado','Sunday':'Domingo'}
        dia=dias.get(agora.strftime('%A'),'')
        w=self.p.w;g1=self.p.g1;l=self.p.l
        total_profit=w+g1;total_trades=total_profit+l
        tx=round((total_profit/total_trades)*100,1) if total_trades>0 else 0
        lucro=round(w*1.6+g1*0.4-l*5,2)
        lista_ops=""
        if self.p.ops:
            for op in self.p.ops[-50:]:lista_ops+=op+"\n"
        relatorio=self.m.catalogador.get_relatorio()
        msg=f"""📊 *PLACAR DIÁRIO FINALIZADO*

🗓️ *{data} ({dia})*
⏰ {agora.strftime('%H:%M')}

┌──────────────────────────┐
│ ⚛️ QUANTUM IA M1        │
│ 🟢 Wins Diretos: {w}      │
│ 🟡 Gale 1: {g1}            │
│ 🔴 Losses: {l}            │
│ 📨 Total Sinais: {total_trades} │
│ 🎯 Assertividade: {tx}%   │
│ [{self._barra(tx)}]      │
│ 💰 Lucro: +R${lucro}      │
│ 🛡️ Pavios bloqueados: {self.m.sinais_bloqueados_pavio} │
└──────────────────────────┘

📋 *Operações do Dia:*
{lista_ops if lista_ops else 'Nenhuma operação'}

⚔️ _{get_filosofia()}_

🔄 *Placar zerado!*"""
        self.tg.send(msg)
        if relatorio:self.tg.send(relatorio)
        print(f"\n{C.GOLD}╔══════════════════════════════╗{C.E}")
        print(f"{C.GOLD}║ 📊 PLACAR DIÁRIO FINALIZADO ║{C.E}")
        print(f"{C.GOLD}║ 🟢{w}W 🟡{g1}G1 🔴{l}L 🎯{tx}% 💰+R${lucro} ║{C.E}")
        print(f"{C.GOLD}╚══════════════════════════════╝{C.E}\n")
        self.p.zerar();self.sinais=0;self.m.sinais_bloqueados_pavio=0
        print(f"  {C.G}🔄 Placar ZERADO! Novo dia!{C.E}\n")

    def fmt_sinal(self,s):
        agora=datetime.now(FUSO_BR)
        he=(agora.replace(second=0,microsecond=0)+timedelta(minutes=1)).strftime('%H:%M')
        e="🟢" if s['direcao']=='CALL' else "🔴"
        est=s.get('estrategia','N/A')
        return f"""⚛️ SINAL QUANTUM IA ⚛️

⏰ Horário: {he}
💰 Ativo: {s['ativo']}-OTC
📈 Direção: {s['direcao']} {e}
⌛️ Expiração: M1
📊 Confiança: {s['confianca']:.0f}%
🧠 Estratégia: {est}

⚠️ Entrar somente no horário marcado.
🔄 1 recuperação (Gale 1)!"""

    def fmt_corr(self,r,s):
        total_profit=self.p.w+self.p.g1
        total_trades=total_profit+self.p.l
        tx=round((total_profit/total_trades)*100,1) if total_trades>0 else 0
        return f"""{r}
📊 {s['ativo']}-OTC | {s['direcao']} {'🟢' if s['direcao']=='CALL' else '🔴'}
📊 Placar: 🟢{self.p.w}W 🟡{self.p.g1}G1 🔴{self.p.l}L
🎯 Assertividade: {tx}%"""

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
        at=sinal['ativo'];d=sinal['direcao'];conf=sinal.get('confianca',0)
        estrategia_nome=sinal.get('estrategia','Desconhecida')
        try:
            self.iq.atualizar()
            await self.esperar(8);v=self.iq.velas[at]
            if len(v)<2:self.op=False;return
            pc=v[-1]['open'];hora=v[-1]['time'].strftime('%H:%M')
            print(f"\n  ⚛️ {at}-OTC {d} | {estrategia_nome} | OPEN:{pc:.5f} | Vela:{hora}")
            await self.esperar(5);v=self.iq.velas[at]
            if len(v)>0 and self.bateu(d,pc,v[-1]):
                r=self.p.win(0);print(f"  ✅ {r}");self.p.registrar(at,d,conf,"WIN")
                self.tg.send(self.fmt_corr(r,sinal))
                self.professor.registrar('win');self.professor.atualizar_stats(at,'win')
                self.m.catalogador.registrar(estrategia_nome,at,True)
                self.op=False;return
            print(f"  ❌ Principal")
            self.g=1;v=self.iq.velas[at];pg=v[-1]['open'] if len(v)>0 else pc
            print(f"  🔄 GALE 1 | OPEN:{pg:.5f}");await self.esperar(5);v=self.iq.velas[at]
            if len(v)>0 and self.bateu(d,pg,v[-1]):
                r=self.p.win(1);print(f"  ✅ {r}");self.p.registrar(at,d,conf,"WIN GALE 1",is_gale=True)
                self.tg.send(self.fmt_corr(r,sinal))
                self.professor.registrar('win');self.professor.atualizar_stats(at,'win')
                self.m.catalogador.registrar(estrategia_nome,at,True)
                self.op=False;return
            print(f"  ❌ GALE 1");r=self.p.loss();print(f"  🔴 {r}");self.p.registrar(at,d,conf,"LOSS")
            self.tg.send(self.fmt_corr(r,sinal))
            self.professor.registrar('loss');self.professor.atualizar_stats(at,'loss')
            self.m.catalogador.registrar(estrategia_nome,at,False)
            explicacao=self.professor.explicar_loss(sinal,self.iq.velas[at])
            self.tg.send(explicacao)
            print(f"  🧠 Loss explicado!")
            self.op=False
        except Exception as e:print(f"  ❌ {e}");self.op=False

    async def run(self):
        banner()
        print(f"\n  ⚛️ Iniciando Quantum IA - Máxima Assertividade...\n")
        print(f"  🕐 Horário Brasil: {datetime.now(FUSO_BR).strftime('%H:%M:%S')}\n")
        print(f"  🔥 65% Taxa Mínima | 🔥 65% Confiança | 🛡️ Filtro Pavio | ⚡ SEM Bloqueio\n")
        if not self.iq.conectar():print(f"  ❌ Falha conexão!");return
        self.iq.atualizar()
        self.ultimo_dia=datetime.now(FUSO_BR).day
        print(f"\n  ✅ QUANTUM IA | 🔥 Máxima Assertividade | 🎯 Melhor Combinação | 4 Pares\n")
        self.tg.send(f"🔥 *QUANTUM IA - MÁXIMA ASSERTIVIDADE*\n👨‍🏫 Trader Professor\n📊 26 Estratégias | 4 Pares\n🎯 Taxa Mínima: 65%\n🔥 Confiança Mínima: 65%\n🔄 Troca Rápida\n🛡️ Filtro de Pavio\n⚡ SEM Bloqueio\n⏰ {datetime.now(FUSO_BR).strftime('%H:%M:%S')}")

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
                        sinal=self.m.obter_sinal_dinamico(self.iq.velas,[])
                        if sinal and time.time()-self.ult>25:
                            self.op=True;self.sinais+=1
                            he=(agora.replace(second=0,microsecond=0)+timedelta(minutes=1)).strftime('%H:%M')
                            est=sinal.get('estrategia','N/A')
                            print(f"\n⚛️ #{self.sinais} {sinal['ativo']}-OTC {sinal['direcao']} | {sinal['confianca']:.0f}% | 🧠 {est} | ⏰ {he}")
                            self.tg.send(self.fmt_sinal(sinal))
                            explicacao=self.professor.explicar_entrada(sinal,self.iq.velas[sinal['ativo']])
                            self.tg.send(explicacao)
                            self.ult=time.time()
                            asyncio.create_task(self.corrigir(sinal))
                    except:pass
                if self.m.catalogador.total_operacoes>0 and self.m.catalogador.total_operacoes%10==0 and self.m.catalogador.total_operacoes!=self.m.catalogador.ultimo_relatorio:
                    relatorio=self.m.catalogador.get_relatorio()
                    if relatorio:
                        self.tg.send(relatorio)
                        self.m.catalogador.ultimo_relatorio=self.m.catalogador.total_operacoes
                if agora.second in[0,30]:
                    try:
                        w,l,g1=self.p.w,self.p.l,self.p.g1
                        total_profit=w+g1;total_trades=total_profit+l
                        tx=round((total_profit/total_trades)*100,1) if total_trades>0 else 0
                        lucro=round(w*1.6+g1*0.4-l*5,2)
                        comb=self.m.catalogador.combinacao_atual
                        info_comb=f" | 🧠 {comb['estrategia']} em {comb['par']}" if comb else ""
                        print(f"{C.GOLD}┌──────────────────────────────────────────────────────┐{C.E}")
                        print(f"{C.GOLD}│{C.E} ⏰ {agora.strftime('%H:%M:%S')} | 📨{self.sinais} | 🟢{w}W 🟡{g1}G1 🔴{l}L 🎯{tx}% | 💰+R${lucro} | 🛡️{self.m.sinais_bloqueados_pavio}{info_comb}")
                        print(f"{C.GOLD}│{C.E} 🔥 65%+ | ⚔️ {get_filosofia()}")
                        print(f"{C.GOLD}└──────────────────────────────────────────────────────┘{C.E}")
                    except:pass
                await asyncio.sleep(3)
            except KeyboardInterrupt:
                clear();w,l,g1=self.p.w,self.p.l,self.p.g1
                total_profit=w+g1;total_trades=total_profit+l
                tx=round((total_profit/total_trades)*100,1) if total_trades>0 else 0
                lucro=round(w*1.6+g1*0.4-l*5,2)
                print(f"\n👋 🟢{w}W 🟡{g1}G1 🔴{l}L | 🎯{tx}% | 💰+R${lucro}\n")
                self.tg.send(f"⚠️ *Desligado*\n🟢{w}W 🟡{g1}G1 🔴{l}L\n🎯{tx}%\n💰+R${lucro}")
                if self.iq.api:
                    try:self.iq.api.close()
                    except:pass
                break
            except Exception as e:
                print(f"  {C.R}❌ {str(e)[:40]}{C.E}");self.iq.ok=False;await asyncio.sleep(5)

if __name__=="__main__":
    asyncio.run(Bot().run())
