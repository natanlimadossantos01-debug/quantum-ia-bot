#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════╗
║   ⚛️  Q U A N T U M   I A   M 1           ║
║   🔬 Estratégia 5-2-0 | Catalogador Pares  ║
║   🎯 Melhor Par do Momento                  ║
║   🔄 Troca Automática | 🛡️ Filtro Pavio    ║
║   👨‍🏫 Trader Professor | ⚔️ Samurai          ║
║   📊 4 Pares OTC | ☁️ Cloud Ready          ║
╚══════════════════════════════════════════════╝
"""
import asyncio, time, requests, numpy as np, signal, sys, json, os, random
from datetime import datetime, timedelta, timezone
from collections import deque
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
    print(f"║   🔬 Estratégia 5-2-0 | Catalogador Pares  ║")
    print(f"║   🎯 Melhor Par do Momento                  ║")
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
# 📊 CATALOGADOR DE PARES (SIMPLIFICADO)
# ═══════════════════════════════════════════
class CatalogadorPares:
    def __init__(self):
        self.performance = {}  # {par: {wins, losses, total}}
        self.par_atual = None
        self.sinais_no_par = 0
        self.max_sinais_por_par = 3  # Reavalia a cada 3 sinais
        self.taxa_minima = 55
        self.min_operacoes = 3
        self.total_operacoes = 0
        self.ultimo_relatorio = 0
        
    def registrar(self, par, venceu):
        if par not in self.performance:
            self.performance[par] = {'wins': 0, 'losses': 0, 'total': 0}
        self.performance[par]['total'] += 1
        if venceu: self.performance[par]['wins'] += 1
        else: self.performance[par]['losses'] += 1
        self.total_operacoes += 1
        if self.par_atual == par:
            self.sinais_no_par += 1
    
    def get_taxa(self, par):
        if par in self.performance:
            p = self.performance[par]
            return round((p['wins']/p['total'])*100, 1) if p['total'] > 0 else 0
        return 0
    
    def escolher_melhor_par(self):
        """Escolhe o par com maior taxa de acerto"""
        melhores = []
        for par, p in self.performance.items():
            if p['total'] >= self.min_operacoes:
                taxa = (p['wins']/p['total'])*100
                if taxa >= self.taxa_minima:
                    melhores.append({'par': par, 'taxa': taxa, 'total': p['total'], 'wins': p['wins'], 'losses': p['losses']})
        melhores.sort(key=lambda x: x['taxa'], reverse=True)
        return melhores[0] if melhores else None
    
    def precisa_trocar(self):
        if not self.par_atual:
            return True
        if self.sinais_no_par >= self.max_sinais_por_par:
            return True
        taxa_atual = self.get_taxa(self.par_atual)
        if taxa_atual < self.taxa_minima:
            return True
        melhor = self.escolher_melhor_par()
        if melhor and melhor['taxa'] > taxa_atual + 10:
            return True
        return False
    
    def atualizar_par(self):
        if self.precisa_trocar():
            melhor = self.escolher_melhor_par()
            if melhor:
                self.par_atual = melhor['par']
                self.sinais_no_par = 0
                return True, melhor
        return False, None
    
    def get_relatorio(self):
        if not self.performance: return None
        msg = "📊 *CATALOGADOR DE PARES - 5-2-0*\n"
        msg += f"📈 Total: {self.total_operacoes} operações\n"
        if self.par_atual:
            taxa = self.get_taxa(self.par_atual)
            msg += f"🎯 *Par Atual:* {self.par_atual} ({taxa}%)\n"
        msg += f"\n🏆 *Performance por Par:*\n"
        ranking = []
        for par, p in self.performance.items():
            taxa = (p['wins']/p['total'])*100 if p['total'] > 0 else 0
            ranking.append({'par': par, 'taxa': taxa, 'total': p['total'], 'wins': p['wins'], 'losses': p['losses']})
        ranking.sort(key=lambda x: x['taxa'], reverse=True)
        for i, r in enumerate(ranking, 1):
            emoji = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else "📊"
            msg += f"{emoji} {r['par']}: {r['taxa']}% | {r['wins']}W/{r['losses']}L ({r['total']} ops)\n"
        return msg

# ═══════════════════════════════════════════
# 🔬 ESTRATÉGIA 5-2-0 (ÚNICA)
# ═══════════════════════════════════════════
class Estrategia520:
    def analisar(self, v):
        try:
            if len(v) < 25: return None, 0
            precos = [x['close'] for x in v]
            mm5 = np.mean(precos[-5:])
            media20 = np.mean(precos[-20:])
            std20 = np.std(precos[-20:])
            bs = media20 + 2*std20
            bi = media20 - 2*std20
            atual = precos[-1]
            if atual > mm5 and atual <= bi * 1.002: return 'CALL', 78
            if atual < mm5 and atual >= bs * 0.998: return 'PUT', 78
            return None, 0
        except: return None, 0

# ═══════════════════════════════════════════
# ⚛️ QUANTUM IA - 5-2-0 + CATALOGADOR
# ═══════════════════════════════════════════
class QuantumIA:
    def __init__(self):
        self.estrategia = Estrategia520()
        self.catalogador = CatalogadorPares()
        self.sinais_bloqueados_pavio = 0

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

    def obter_sinal(self, velas_dict, bloqueados):
        """Obtém sinal priorizando o melhor par"""
        trocou, info = self.catalogador.atualizar_par()
        if trocou and info:
            print(f"  🎯 Novo par foco: {info['par']} ({info['taxa']}%)")
        
        # Primeiro: tenta no par atual (se tiver)
        if self.catalogador.par_atual:
            par = self.catalogador.par_atual
            if par in velas_dict and par not in bloqueados and len(velas_dict[par]) >= 25:
                d, c = self.estrategia.analisar(velas_dict[par])
                if d and self._pavio_ok(velas_dict[par], d):
                    return {'ativo': par, 'direcao': d, 'confianca': c, 'estrategia': '🔬 5-2-0'}
                elif d: self.sinais_bloqueados_pavio += 1
        
        # Segundo: busca em qualquer par disponível
        melhor = None; melhor_score = 0
        for par, velas in velas_dict.items():
            if par in bloqueados: continue
            if len(velas) < 25: continue
            d, c = self.estrategia.analisar(velas)
            if d and self._pavio_ok(velas, d):
                score = c
                taxa = self.catalogador.get_taxa(par)
                if taxa > 60: score += taxa * 0.5
                if score > melhor_score:
                    melhor_score = score
                    melhor = {'ativo': par, 'direcao': d, 'confianca': c, 'estrategia': '🔬 5-2-0'}
        
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
        leitura,obs,pavio_ok=self.ler_grafico(velas,direcao)
        tendencia=self.tendencias.get(ativo,'NEUTRA')
        filosofia=get_filosofia()
        return f"""👨‍🏫 *ANÁLISE DO TRADER*

📊 *Mercado:* {tendencia}
👁️ *Gráfico:* {leitura}
🔬 *Estratégia:* 5-2-0 (Bandas Bollinger + Média Móvel)
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
        if conf<58:causas.append("📊 Confiança baixa")
        if not causas:causas.append("🎲 Movimento aleatório")
        self.losses.append({'ativo':ativo,'direcao':direcao,'confianca':conf,'causas':causas,'hora':datetime.now(FUSO_BR).hour})
        licao="Seguir o plano"
        if 'pavio' in str(causas).lower():licao="Verificar pavios antes de entrar"
        elif 'tendência' in str(causas).lower():licao="Não operar contra tendência"
        elif 'confiança' in str(causas).lower():licao="Esperar confiança mais alta"
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
        self.ultimo_sinal_ativo={}
        self.bloqueio_par_segundos=420
        self.ultimo_dia=datetime.now(FUSO_BR).day;self.placar_enviado=False

    def pode_enviar(self,ativo):
        agora=time.time()
        if ativo in self.ultimo_sinal_ativo:
            if agora-self.ultimo_sinal_ativo[ativo]<self.bloqueio_par_segundos:return False
        return True
    def registrar_envio(self,ativo):self.ultimo_sinal_ativo[ativo]=time.time()
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
        self.ultimo_sinal_ativo.clear()
        print(f"  {C.G}🔄 Placar ZERADO! Novo dia!{C.E}\n")

    def fmt_sinal(self,s):
        agora=datetime.now(FUSO_BR)
        he=(agora.replace(second=0,microsecond=0)+timedelta(minutes=1)).strftime('%H:%M')
        e="🟢" if s['direcao']=='CALL' else "🔴"
        return f"""⚛️ SINAL QUANTUM IA ⚛️

⏰ Horário: {he}
💰 Ativo: {s['ativo']}-OTC
📈 Direção: {s['direcao']} {e}
⌛️ Expiração: M1
📊 Confiança: {s['confianca']:.0f}%
🔬 Estratégia: 5-2-0

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
        try:
            self.iq.atualizar()
            await self.esperar(8);v=self.iq.velas[at]
            if len(v)<2:self.op=False;return
            pc=v[-1]['open'];hora=v[-1]['time'].strftime('%H:%M')
            print(f"\n  🔬 {at}-OTC {d} | 5-2-0 | OPEN:{pc:.5f} | Vela:{hora}")
            await self.esperar(5);v=self.iq.velas[at]
            if len(v)>0 and self.bateu(d,pc,v[-1]):
                r=self.p.win(0);print(f"  ✅ {r}");self.p.registrar(at,d,conf,"WIN")
                self.tg.send(self.fmt_corr(r,sinal))
                self.professor.registrar('win');self.professor.atualizar_stats(at,'win')
                self.m.catalogador.registrar(at,True)
                self.op=False;return
            print(f"  ❌ Principal")
            self.g=1;v=self.iq.velas[at];pg=v[-1]['open'] if len(v)>0 else pc
            print(f"  🔄 GALE 1 | OPEN:{pg:.5f}");await self.esperar(5);v=self.iq.velas[at]
            if len(v)>0 and self.bateu(d,pg,v[-1]):
                r=self.p.win(1);print(f"  ✅ {r}");self.p.registrar(at,d,conf,"WIN GALE 1",is_gale=True)
                self.tg.send(self.fmt_corr(r,sinal))
                self.professor.registrar('win');self.professor.atualizar_stats(at,'win')
                self.m.catalogador.registrar(at,True)
                self.op=False;return
            print(f"  ❌ GALE 1");r=self.p.loss();print(f"  🔴 {r}");self.p.registrar(at,d,conf,"LOSS")
            self.tg.send(self.fmt_corr(r,sinal))
            self.professor.registrar('loss');self.professor.atualizar_stats(at,'loss')
            self.m.catalogador.registrar(at,False)
            explicacao=self.professor.explicar_loss(sinal,self.iq.velas[at])
            self.tg.send(explicacao)
            print(f"  🧠 Loss explicado!")
            self.op=False
        except Exception as e:print(f"  ❌ {e}");self.op=False

    async def run(self):
        banner()
        print(f"\n  🔬 Iniciando Quantum IA - 5-2-0 + Catalogador de Pares...\n")
        print(f"  🕐 Horário Brasil: {datetime.now(FUSO_BR).strftime('%H:%M:%S')}\n")
        print(f"  🔬 Estratégia: 5-2-0 | 🎯 Melhor Par | 🛡️ Filtro Pavio | 🔒 7min/par | 4 Pares\n")
        if not self.iq.conectar():print(f"  ❌ Falha conexão!");return
        self.iq.atualizar()
        self.ultimo_dia=datetime.now(FUSO_BR).day
        print(f"\n  ✅ QUANTUM IA | 🔬 5-2-0 | 🎯 Catalogador de Pares | 4 Pares\n")
        self.tg.send(f"🔬 *QUANTUM IA - 5-2-0 + CATALOGADOR*\n👨‍🏫 Trader Professor\n📊 4 Pares OTC\n🔬 Estratégia: 5-2-0\n🎯 Melhor Par do Momento\n🔄 Troca Automática\n🛡️ Filtro de Pavio\n⚔️ Filosofia Samurai\n⏰ {datetime.now(FUSO_BR).strftime('%H:%M:%S')}")

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
                        sinal=self.m.obter_sinal(self.iq.velas,bloqueados)
                        if sinal and time.time()-self.ult>25:
                            self.op=True;self.sinais+=1;self.registrar_envio(sinal['ativo'])
                            he=(agora.replace(second=0,microsecond=0)+timedelta(minutes=1)).strftime('%H:%M')
                            print(f"\n🔬 #{self.sinais} {sinal['ativo']}-OTC {sinal['direcao']} | {sinal['confianca']:.0f}% | 5-2-0 | ⏰ {he}")
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
                        bloqueados=[a for a in ATIVOS_OTC if not self.pode_enviar(a)]
                        info_bloqueio=f" | 🔒 {','.join(bloqueados)}" if bloqueados else ""
                        par_foco=self.m.catalogador.par_atual
                        info_par=f" | 🎯 {par_foco}" if par_foco else ""
                        print(f"{C.GOLD}┌──────────────────────────────────────────────────────┐{C.E}")
                        print(f"{C.GOLD}│{C.E} ⏰ {agora.strftime('%H:%M:%S')} | 📨{self.sinais} | 🟢{w}W 🟡{g1}G1 🔴{l}L 🎯{tx}% | 💰+R${lucro} | 🛡️{self.m.sinais_bloqueados_pavio}{info_bloqueio}{info_par}")
                        print(f"{C.GOLD}│{C.E} 🔬 5-2-0 | ⚔️ {get_filosofia()}")
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
