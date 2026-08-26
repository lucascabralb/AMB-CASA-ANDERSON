# Casa Anderson — Automação Residencial
## App + Backend Tuya (funcionando de verdade)

---

## O QUE MUDOU NESTA VERSÃO

- **App novo**: `casa-anderson-app.html` — visual Apple Minimalist Premium, login com Face ID + PIN de 4 dígitos, fotos reais dos ambientes, ícones sofisticados.
- **Backend corrigido**: encontrei e corrigi um `device_id` da Tuya com um espaço no meio (`cozinha_persiana`) que ia quebrar a persiana da cozinha.
- **3 cenas que só existiam no visual agora existem de verdade no backend**: Fechar Cinema, Zona 3, Boa Noite.
- **Credenciais Tuya movidas para variável de ambiente** (arquivo `.env`), em vez de ficarem escritas direto no código-fonte — essencial antes de publicar online.
- **O app agora fala com o backend de verdade**: cada botão, dimmer, persiana e cena manda o comando real via `fetch()`.
- **Modo demonstração automático**: se o backend estiver desligado ou fora do alcance, o app detecta sozinho e continua funcionando visualmente (com aviso "Demonstração" no lugar de "Online"), sem travar nem dar erro.

---

## COMO RODAR

### 1 — Configurar as credenciais
Dentro da pasta `amb-backend/`, copie `.env.example` para `.env` e confirme os valores (já vêm preenchidos com as credenciais que você me passou).

Se preferir sem instalar nada extra, exporte direto no terminal antes de rodar:
```bash
export TUYA_CLIENT_ID=mar833ptq3ja3fstcwdg
export TUYA_SECRET=27af5f3873a04fd191e1057615656d7a
```

### 2 — Instalar dependências
```bash
cd amb-backend
pip install -r requirements.txt
```

### 3 — Rodar o backend
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```
Você verá: `Uvicorn running on http://0.0.0.0:8000`

### 4 — Abrir o app
Abra `casa-anderson-app.html` no navegador (Chrome/Safari) ou no celular.
Entre com Face ID (toque no ícone) ou digite qualquer código de 4 dígitos.
Na Home, o texto "Online" no card "Sistema ativo" confirma que está conversando com o backend de verdade.

---

## MAPEAMENTO APP → DISPOSITIVOS REAIS

| Tela do app | device_id no backend |
|---|---|
| Sala — Led / Spot / Persiana 1 | `sala_led`, `sala_spot`, `sala_p1` |
| Sacada — TV / Cortina / Ração | `sacada_tv`, `sacada_cortina1`, `sacada_racao` |
| Quarto Casal — Luz Cabeceira / Persiana | `casal_luz`, `casal_persiana` |
| Quarto Meninas — Luz / Persiana | `meninas_luz`, `meninas_persiana` |
| Cozinha — Luz / Persiana | `cozinha_luz`, `cozinha_persiana` |
| Banheiro — Luz / Exaustor | `banheiro_luz`, `banheiro_exaustor` |
| Lavanderia — Luz / Tomada | `lavanderia_interruptor`, `lavanderia_rack` |
| Corredor — Luz | `corredor_luz` |
| Controles rápidos (Home) | `sala_led`, `sacada_luz_varanda`, `banheiro_exaustor`, `sacada_freezer` |

> Nota: no backend real só existe **um** device de luz para o Quarto Casal (`casal_luz`), mas o visual mostra 3 luzes (Cabeceira, TV, Cama) — hoje só a "Luz Cabeceira" está de fato conectada. Se você tiver os 3 Device IDs reais da Tuya para essas luzes, me passe que eu conecto as outras duas também.

---

## PRÓXIMO PASSO: PUBLICAR ONLINE

Para funcionar de qualquer lugar (celular fora de casa):
1. Suba o backend num servidor (Railway.app é gratuito para começar)
2. No painel do Railway, configure as variáveis `TUYA_CLIENT_ID` e `TUYA_SECRET` (nunca deixe no código)
3. Pegue a URL gerada, ex: `https://amb-casa-anderson.railway.app`
4. No `casa-anderson-app.html`, troque a linha:
   ```javascript
   const BACKEND = 'http://localhost:8000';
   ```
   pelo endereço do seu servidor.
