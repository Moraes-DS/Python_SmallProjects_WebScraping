# --- CÓDIGO COM ANÁLISE DA DESCRIÇÃO PARA COR/OBJETIVO ---
# VERSÃO v31.full_scrape_loop - Loop para clicar e coletar TODOS os produtos

# (Imports e Configurações Iniciais Idênticos...)
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import pandas as pd
import os
import time
import random
import re
import traceback
import datetime

# --- Configurações ---
URL_ALVO = "https://www.artwalk.com.br/tenis"
CAMINHO_BASE = r"C:\Users\morae\desktop\scrapping" # Adapte se necessário
CAMINHO_CSV = os.path.join(CAMINHO_BASE, "produtos_artwalk_v31_full_scrape_loop.csv") # Novo nome
CAMINHO_SCREENSHOT_DIR = os.path.join(CAMINHO_BASE, "screenshots_debug")
os.makedirs(CAMINHO_SCREENSHOT_DIR, exist_ok=True)

# (Timeouts, Constantes, User Agent Idênticos...)
TEMPO_ESPERA_NAVEGACAO = 120000; TEMPO_ESPERA_PAGINA_PRODUTO = 90000
TIMEOUT_GERAL_PADRAO = 60000; TIMEOUT_ELEMENTO = 45000
TIMEOUT_ELEMENTO_PRODUTO = 50000 # Tempo para esperar seletor descrição (v26)
TIMEOUT_VISIBILIDADE_BOTAO_VER_MAIS = 35000; TIMEOUT_REDE_OCIOSA = 30000
TEMPO_ESPERA_CURTO = 5; NUM_SCROLL_ETAPAS_INICIAL = 10
SCROLL_PIXELS_POR_ETAPA = 500; TEMPO_ESPERA_ENTRE_ETAPAS_INICIAL = 1.0
TEMPO_ESPERA_POS_SCROLL_INICIAL = 25
# MAX_CLIQUES_VER_MAIS = 1 # REMOVIDO - Agora é um loop
SAFE_MAX_CLICKS = 60 # Limite de segurança para evitar loops infinitos
TEMPO_ESPERA_POS_CLIQUE_VER_MAIS = 20; TEMPO_ESPERA_POS_SCROLL_DENTRO_LOOP = 15
USER_AGENT = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
              'AppleWebKit/537.36 (KHTML, like Gecko) '
              'Chrome/119.0.0.0 Safari/537.36')

# --- Funções Auxiliares (Idênticas) ---
def limpar_preco(texto_preco):
    if not texto_preco: return None
    try:
        preco_limpo = re.sub(r'[^\d,.]', '', texto_preco)
        if ',' in preco_limpo and '.' in preco_limpo:
            if preco_limpo.rfind('.') < preco_limpo.rfind(','): preco_limpo = preco_limpo.replace('.', '').replace(',', '.')
        else: preco_limpo = preco_limpo.replace(',', '.')
        return float(preco_limpo)
    except Exception: return None
def determinar_genero(nome_produto):
    if not nome_produto: return "Unissex"
    nome_lower = nome_produto.lower()
    if ("infantil" in nome_lower or " gs " in nome_lower or nome_lower.endswith(" gs") or " kids " in nome_lower or " baby " in nome_lower): return "Infantil"
    elif ("feminino" in nome_lower or " wmns " in nome_lower or nome_lower.endswith(" w")): return "Feminino"
    elif "masculino" in nome_lower: return "Masculino"
    elif "unissex" in nome_lower: return "Unissex"
    else: return "Unissex"
def limpar_descricao(texto):
    if not texto: return ""
    return re.sub(r'\s+', ' ', texto).strip()
CORES_PALAVRAS_CHAVE = ["branco", "preto", "azul", "vermelho", "verde", "cinza", "rosa", "amarelo", "laranja", "marrom", "bege", "dourado", "prata", "roxo", "vinho", "creme", "turquesa", "grafite", "multicolor", "off-white", "bordo"]
OBJETIVOS_PALAVRAS_CHAVE = ["corrida", "caminhada", "treino", "academia", "fitness", "esportivo", "basquete", "skate", "volei", "tennis", "futebol", "casual", "dia a dia", "passeio", "urbano", "estilo", "moda", "performance", "aventura", "trilha", "lifestyle"]
def extrair_cor_da_descricao(descricao): return "Não informado"
def extrair_objetivo_da_descricao(descricao): return "Não informado"

# --- Função scrape_product_details (ESTILO v26 + FECHAMENTO DE POPUPS) ---
# (Permanece idêntica à versão v31.final_phase_fix)
def scrape_product_details(page, product_url):
    details = {"cor": "Não informado", "objetivo": "Não informado", "tamanhos_disponiveis": "Não informado", "descricao": "Não informado"}
    seletor_espera_descricao = "div.vtex-store-components-3-x-productDescriptionText"
    seletor_cor_especifico = "span.vtex-store-components-3-x-skuName"
    seletor_indicado_para_nome = "td.vtex-specification-tabs-0-x-specificationName:has-text('Indicado Para')"
    seletor_indicado_para_valor = f"{seletor_indicado_para_nome} + td.vtex-specification-tabs-0-x-specificationValue"
    seletor_tamanhos_disp = "div.vtex-sku-selector-container--product-size button.vtex-sku-selector__item:not(.--unavailable):not(:disabled) span.vtex-sku-selector__value"
    seletor_tamanhos_alt = "div.vtex-sku-selector-container--product-size button.vtex-sku-selector__item:not(.--unavailable):not(:disabled)"
    try:
        print(f"      -> Navegando para: {product_url}")
        page.goto(product_url, timeout=TEMPO_ESPERA_PAGINA_PRODUTO, wait_until='domcontentloaded')
        print(f"      -> Página carregada (domcontentloaded).")
        time.sleep(random.uniform(1.0, 2.0))
        print("      -> Tentando fechar popups...")
        try:
            cookie_button = page.locator("button:has-text('Aceitar')").first
            if cookie_button.is_visible(timeout=3000): cookie_button.click(timeout=5000); print("         -> Cookies fechado."); time.sleep(0.5)
        except Exception: pass
        try:
            close_selectors = ["div.vtex-modal-layout-0-x-container button.vtex-modal-layout-0-x-closeButton", "button[aria-label='Close']"]
            for selector in close_selectors:
                close_button = page.locator(selector).first
                if close_button.is_visible(timeout=4000): print(f"         -> Fechando modal ({selector})..."); close_button.click(timeout=8000); print("            ...modal fechado."); time.sleep(1.0); break
        except Exception as e_modal: print(f"         (Aviso) Erro fechar modal: {e_modal}")
        print("      -> Verificação popups concluída.")
        details["descricao"] = "Descrição não encontrada"
        try:
            print(f"      -> Esperando seletor descrição: '{seletor_espera_descricao}'...")
            page.wait_for_selector(seletor_espera_descricao, timeout=TIMEOUT_ELEMENTO_PRODUTO)
            print("         -> Seletor encontrado.")
            desc_element = page.query_selector(seletor_espera_descricao)
            if desc_element:
                texto_descricao_bruta = desc_element.inner_text()
                descricao_limpa = limpar_descricao(texto_descricao_bruta)
                if descricao_limpa: details["descricao"] = descricao_limpa; print(f"         -> SUCESSO! Descrição: {details['descricao'][:80]}...")
                else: print(f"         -> ALERTA: Seletor encontrado, mas inner_text vazio."); details["descricao"] = "Descrição encontrada, mas vazia"
            else: print(f"         -> ALERTA: Seletor esperado, mas query_selector retornou None.")
        except PlaywrightTimeoutError:
            print(f"    ⚠️ Timeout ({TIMEOUT_ELEMENTO_PRODUTO}ms) esperando pelo seletor '{seletor_espera_descricao}'.")
            desc_element = page.query_selector(seletor_espera_descricao)
            if desc_element:
                try:
                    texto_descricao_bruta = desc_element.inner_text(); descricao_limpa = limpar_descricao(texto_descricao_bruta)
                    if descricao_limpa: details["descricao"] = descricao_limpa; print("         -> Descrição pega no fallback pós-timeout.")
                    else: details["descricao"] = "Descrição vazia (fallback pós-timeout)"
                except Exception as e_inner: print(f"    ❌ Erro ao pegar inner_text no fallback: {e_inner}")
            else: print("         -> query_selector retornou None também no fallback.")
        except Exception as e_desc: print(f"    ❌ Erro inesperado ao obter descrição: {e_desc}"); traceback.print_exc()
        try:
            cor_locator = page.locator(seletor_cor_especifico).first; cor_locator.wait_for(timeout=20000); cor_texto = cor_locator.text_content().strip(); match = re.search(r'[\s\(-]([A-Za-zÀ-ÖØ-öø-ÿ/ -]+)$', cor_texto)
            if match:
                cor_extraida = match.group(1).strip()
                if cor_extraida.lower() not in ["masculino", "feminino", "unissex", "infantil"] and len(cor_extraida) > 2:
                    palavras = cor_extraida.lower().split('/'); cores_validas = [p.strip() for p in palavras if p.strip() in CORES_PALAVRAS_CHAVE or "multi" in p.strip() or "off" in p.strip()]
                    if cores_validas: details["cor"] = cor_extraida.capitalize()
            if details["cor"] == "Não informado":
                primeira_palavra = cor_texto.split(" ")[0].lower();
                if primeira_palavra in CORES_PALAVRAS_CHAVE: details["cor"] = primeira_palavra.capitalize()
        except Exception: pass
        try:
            page.locator(seletor_indicado_para_nome).first.wait_for(timeout=20000); objetivo_locator = page.locator(seletor_indicado_para_valor).first; obj_texto = objetivo_locator.text_content().strip()
            if obj_texto and len(obj_texto) < 50: details["objetivo"] = obj_texto.capitalize()
        except Exception: pass
        try:
            tamanho_locators = page.locator(seletor_tamanhos_disp).all(timeout=20000);
            if not tamanho_locators: tamanho_locators = page.locator(seletor_tamanhos_alt).all(timeout=10000)
            tamanhos = [loc.text_content().strip() for loc in tamanho_locators if loc.text_content() and loc.text_content().strip()]
            if tamanhos:
                try: tamanhos_ordenados = sorted(tamanhos, key=lambda x: float(x.replace(',', '.')) if re.match(r'^\d+([,.]\d+)?$', x) else float('inf'))
                except ValueError: tamanhos_ordenados = sorted(tamanhos)
                details["tamanhos_disponiveis"] = ", ".join(tamanhos_ordenados)
        except Exception: pass
    except PlaywrightTimeoutError as e_nav: print(f"    ⚠️ Timeout GERAL NAVEGAÇÃO: {product_url}. Erro: {e_nav}")
    except Exception as e: print(f"    ❌ Erro GERAL INESPERADO página produto: {product_url}. Erro: {e}"); traceback.print_exc()
    return details

# --- Função Auxiliar coletar_dados_base_lista (Idêntica) ---
# ... (código inteiro da função coletar_dados_base_lista permanece igual) ...
def coletar_dados_base_lista(page, seletor_produto):
    print(f"   🔍 Buscando produtos na lista com seletor: {seletor_produto}")
    lista_produtos_base = []
    try:
        page.locator(seletor_produto).first.wait_for(state="attached", timeout=15000); produtos_locators = page.locator(seletor_produto).all(); total_locators = len(produtos_locators); print(f"      -> {total_locators} locators encontrados.")
        if not produtos_locators: return []
        for i, produto_locator in enumerate(produtos_locators):
            dados_prod = {}; nome_completo = "NP"; link = None; preco_final = None; imagem = "Imagem não encontrada"
            try:
                seletor_marca="span.vtex-store-components-3-x-productBrandName"; seletor_nome_modelo=("span.vtex-product-summary-2-x-productBrand.vtex-product-summary-2-x-brandName"); seletor_link="a.vtex-product-summary-2-x-clearLink"; seletor_imagem="img.vtex-product-summary-2-x-imageNormal"; seletor_preco="span.vtex-product-price-1-x-sellingPriceValue"; seletor_preco_alt="span.vtex-product-price-1-x-sellingPrice"; T_OUT_LOC=1500
                try: marca = produto_locator.locator(seletor_marca).first.text_content(timeout=T_OUT_LOC).strip()
                except Exception: marca = ""
                try: nome_modelo = produto_locator.locator(seletor_nome_modelo).first.text_content(timeout=T_OUT_LOC).strip()
                except Exception: nome_modelo = ""
                try: link_rel = produto_locator.locator(seletor_link).first.get_attribute("href", timeout=T_OUT_LOC)
                except Exception: link_rel = None
                try: imagem = produto_locator.locator(seletor_imagem).first.get_attribute("src", timeout=T_OUT_LOC)
                except Exception: imagem = "Imagem não encontrada"
                preco_texto_bruto = ""
                try: preco_texto_bruto = produto_locator.locator(seletor_preco).first.text_content(timeout=T_OUT_LOC).strip()
                except Exception:
                    try: preco_texto_bruto = produto_locator.locator(seletor_preco_alt).first.text_content(timeout=T_OUT_LOC).strip()
                    except Exception: preco_texto_bruto = ""
                if marca and nome_modelo: nome_completo = f"{marca} {nome_modelo}"
                elif nome_modelo: nome_completo = nome_modelo
                elif marca: nome_completo = marca
                else: nome_completo = "Nome não encontrado"
                nome_completo = nome_completo.strip()
                if not nome_completo or len(nome_completo) < 3: nome_completo = "Nome não encontrado"
                link = None
                if link_rel:
                    try: base_url = "/".join(page.url.split("/")[:3])
                    except Exception: base_url = "/".join(URL_ALVO.split("/")[:3])
                    if link_rel.startswith("http"): link = link_rel
                    elif link_rel.startswith("/"): link = base_url + link_rel
                    else: link = base_url + "/" + link_rel
                preco_final = limpar_preco(preco_texto_bruto); genero_final = determinar_genero(nome_completo)
                if link and nome_completo != "Nome não encontrado" and preco_final is not None:
                    dados_prod = {"nome_produto": nome_completo, "preco_atual": preco_final, "url_site": link, "url_imagem": imagem, "genero_base": genero_final}
                    lista_produtos_base.append(dados_prod)
            except Exception as erro_lista_item: print(f"      ❌ Erro processar locator #{i+1}: {erro_lista_item}")
    except Exception as e_coleta_base: print(f"   ❌ Erro GERAL ao coletar dados básicos da lista: {e_coleta_base}")
    print(f"   ✅ Coleta básica retornou {len(lista_produtos_base)} produtos válidos.")
    return lista_produtos_base


# --- Função Principal scraping_artwalk (LOOP COMPLETO) ---
def scraping_artwalk():
    print(f"--- Iniciando Scraping Artwalk v31.full_scrape_loop ---") # Nome da versão
    print(f"--- Salvando em: {CAMINHO_CSV} ---") # Nome do arquivo

    lista_dados_finais = []
    processed_urls = set()
    navegador = None; contexto = None; pagina_lista = None; pagina_produto = None
    FAZER_SCREENSHOT_DEBUG = True

    with sync_playwright() as p:
        try:
            navegador = p.chromium.launch(headless=False)
            contexto = navegador.new_context(user_agent=USER_AGENT, viewport={'width': 1920, 'height': 1080})
            contexto.set_default_navigation_timeout(TEMPO_ESPERA_NAVEGACAO); contexto.set_default_timeout(TIMEOUT_GERAL_PADRAO); pagina_lista = contexto.new_page(); pagina_produto = contexto.new_page(); pagina_produto.set_default_navigation_timeout(TEMPO_ESPERA_PAGINA_PRODUTO); pagina_produto.set_default_timeout(TIMEOUT_GERAL_PADRAO)

            # --- Carregamento Inicial e Preparação ---
            print("[FASE INICIAL] Carregando página de lista e tratando popups/scrolls...")
            print(f"   -> Navegando para {URL_ALVO}..."); pagina_lista.goto(URL_ALVO, wait_until='networkidle'); print("   -> Página carregada."); time.sleep(TEMPO_ESPERA_CURTO / 2)
            print("   -> Tratando popups da lista...");
            try: pagina_lista.locator("button:has-text('Aceitar')").first.click(timeout=15000); print("      -> Cookies OK."); time.sleep(0.5)
            except Exception: print("      (Info) Cookies não encontrados/aceitos.")
            try:
                 close_selectors = ["div.vtex-modal-layout-0-x-container button.vtex-modal-layout-0-x-closeButton", "button[aria-label='Close']", "button:has-text('FECHAR')"];
                 for selector in close_selectors:
                     close_button = pagina_lista.locator(selector).first;
                     if close_button.is_visible(timeout=5000): print(f"      -> Fechando modal ({selector})..."); close_button.click(timeout=10000); time.sleep(1.5); print("         ...Fechado."); break
            except Exception: print("      (Info) Modal não encontrado/fechado.")
            print(f"   -> Simulando {NUM_SCROLL_ETAPAS_INICIAL} scrolls iniciais na lista...")
            try:
                for i in range(NUM_SCROLL_ETAPAS_INICIAL): pagina_lista.mouse.wheel(0, SCROLL_PIXELS_POR_ETAPA); time.sleep(TEMPO_ESPERA_ENTRE_ETAPAS_INICIAL)
                print(f"      -> Scrolls da lista concluídos.")
            except Exception as e_scroll_init: print(f"      ⚠️ Erro scroll lista: {e_scroll_init}")
            print(f"   -> Aguardando {TEMPO_ESPERA_POS_SCROLL_INICIAL}s após scrolls da lista..."); time.sleep(TEMPO_ESPERA_POS_SCROLL_INICIAL);
            try: pagina_lista.wait_for_load_state('networkidle', timeout=TIMEOUT_REDE_OCIOSA); print("      -> Network Idle OK.")
            except Exception as e_ni1: print(f"      (Info) Network Idle não detectado ({e_ni1}).")
            print("   -> Preparação inicial concluída.")

            # --- LOOP PRINCIPAL: Coletar Novos -> Clicar Mais ---
            cliques_realizados = 0
            while cliques_realizados <= SAFE_MAX_CLICKS: # Loop com limite de segurança
                print(f"\n--- CICLO #{cliques_realizados + 1} ---")

                # 1. Coletar dados básicos atuais e identificar novos produtos
                print("   1. Coletando produtos visíveis na lista...")
                seletor_produto = "section.vtex-product-summary-2-x-container"
                produtos_atuais_base = coletar_dados_base_lista(pagina_lista, seletor_produto)
                produtos_novos_neste_ciclo = [
                    p for p in produtos_atuais_base if p["url_site"] not in processed_urls
                ]

                if not produtos_novos_neste_ciclo and cliques_realizados > 0:
                    print("   -> Nenhum produto NOVO encontrado neste ciclo após clique. Provavelmente fim.")
                    break # Sai do loop principal se não há novos produtos após um clique

                if not produtos_novos_neste_ciclo and cliques_realizados == 0 and not produtos_atuais_base:
                     print("   -> ERRO CRÍTICO: Nenhum produto encontrado na página inicial. Verifique seletores ou carregamento.")
                     break # Sai se nem na primeira vez achou algo

                # 2. Coletar detalhes dos novos produtos encontrados
                if produtos_novos_neste_ciclo:
                    print(f"   2. Coletando detalhes para {len(produtos_novos_neste_ciclo)} NOVOS produtos...")
                    log_interval = max(1, len(produtos_novos_neste_ciclo) // 4) # Log mais frequente
                    for i, dados_base in enumerate(produtos_novos_neste_ciclo):
                        url_atual = dados_base["url_site"]
                        item_num_global = len(lista_dados_finais) + 1 # Número sequencial geral
                        if (i + 1) % log_interval == 0 or i == 0 or i == len(produtos_novos_neste_ciclo) - 1:
                             print(f"--- Detalhes {item_num_global}/{len(produtos_atuais_base)} (Novo #{i+1}): {dados_base['nome_produto'][:60]}...")
                        try:
                            detalhes_extras = scrape_product_details(pagina_produto, url_atual)
                            dados_completos = {**dados_base, **detalhes_extras}; dados_completos["genero_destinado"] = dados_base.get("genero_base", "Unissex"); dados_completos.pop("genero_base", None); dados_completos["loja"] = "Artwalk"; dados_completos["categoria"] = "Tênis"
                            lista_dados_finais.append(dados_completos); processed_urls.add(url_atual)
                        except Exception as e_det_ciclo: print(f"    ❌ Erro detalhes ciclo {cliques_realizados+1}, item {i+1}: {e_det_ciclo}"); traceback.print_exc()
                        time.sleep(random.uniform(1.5, 2.5)) # Pausa entre produtos
                    print(f"   -> Detalhes dos {len(produtos_novos_neste_ciclo)} novos produtos coletados.")
                else:
                     # Isso só deve acontecer na primeira iteração se houver produtos
                     if cliques_realizados == 0 and produtos_atuais_base:
                         print("   2. (Primeira iteração, produtos já processados? Verificação...)")
                     # Ou se houve erro na coleta base anterior
                     elif not produtos_atuais_base:
                          print("   2. Nenhum produto base encontrado para coletar detalhes.")


                # 3. Tentar clicar em "Mostrar mais"
                print(f"\n   3. Tentando clicar 'Mostrar mais' (Clique #{cliques_realizados + 1})...")
                sel_btn_princ = 'a.vtex-button:has(div.vtex-button__label:has-text("Mostrar mais"))'
                sel_btn_fall = 'a:has-text("Mostrar mais")'
                botao_clicado_neste_ciclo = False
                try:
                    print("      -> Procurando botão..."); mostrar_mais_button = None; botao_encontrado = False;
                    try: mostrar_mais_button = pagina_lista.locator(sel_btn_princ); mostrar_mais_button.wait_for(state='visible', timeout=TIMEOUT_VISIBILIDADE_BOTAO_VER_MAIS); print("         -> Encontrado (principal)."); botao_encontrado = True
                    except Exception:
                        print("         -> Não encontrado (principal), tentando fallback...");
                        try: mostrar_mais_button = pagina_lista.locator(sel_btn_fall); mostrar_mais_button.wait_for(state='visible', timeout=TIMEOUT_VISIBILIDADE_BOTAO_VER_MAIS / 2); print("         -> Encontrado (fallback)."); botao_encontrado = True
                        except Exception: print("         -> Botão não encontrado.")

                    if botao_encontrado:
                        print("      -> Clicando..."); mostrar_mais_button.scroll_into_view_if_needed(timeout=10000); time.sleep(random.uniform(0.5, 1.5)); mostrar_mais_button.click(timeout=TIMEOUT_ELEMENTO, force=True); cliques_realizados += 1; botao_clicado_neste_ciclo = True; print(f"         -> Clique {cliques_realizados} OK.")
                        print(f"      -> Aguardando {TEMPO_ESPERA_POS_CLIQUE_VER_MAIS}s..."); time.sleep(TEMPO_ESPERA_POS_CLIQUE_VER_MAIS); print("         -> Espera pós-clique OK.")
                        print(f"      -> Scroll pós-clique...");
                        try: pagina_lista.evaluate("window.scrollTo(0, document.body.scrollHeight)"); time.sleep(1.5); print("         -> Scroll pós-clique OK.")
                        except Exception as e_scroll_loop: print(f"         ⚠️ Erro scroll: {e_scroll_loop}")
                        print(f"      -> Aguardando {TEMPO_ESPERA_POS_SCROLL_DENTRO_LOOP}s..."); time.sleep(TEMPO_ESPERA_POS_SCROLL_DENTRO_LOOP);
                        try: pagina_lista.wait_for_load_state('networkidle', timeout=TIMEOUT_REDE_OCIOSA / 1.5); print("         -> Network Idle pós-scroll OK.")
                        except Exception: pass
                        print("         -> Espera pós-scroll OK.")
                    else:
                        print("      -> Botão 'Mostrar mais' não encontrado. Fim do carregamento.")
                        break # Sai do loop principal

                except Exception as e_click:
                    print(f"   ❌ Erro crítico ao tentar clicar 'Mostrar mais': {e_click}")
                    traceback.print_exc()
                    break # Sai do loop principal em caso de erro no clique

                # Segurança extra: se o clique falhou por timeout ou erro, sai
                if not botao_clicado_neste_ciclo:
                    print("   -> Botão não foi clicado neste ciclo. Interrompendo.")
                    break

                if cliques_realizados >= SAFE_MAX_CLICKS:
                    print(f"   -> Atingido limite de segurança de {SAFE_MAX_CLICKS} cliques. Interrompendo.")
                    break

            # Fim do loop principal

            print(f"\n✅ Coleta finalizada após {cliques_realizados} cliques.")

        # --- Finally e Salvamento CSV (Idênticos) ---
        except PlaywrightTimeoutError as e_timeout: print(f"\n❌ Erro de TIMEOUT GERAL: {e_timeout}"); traceback.print_exc()
        except Exception as e: print(f"\n❌ Erro GERAL INESPERADO: {e}"); traceback.print_exc()
        finally:
            if pagina_produto and not pagina_produto.is_closed():
                try: pagina_produto.close(); print("\nℹ️ Página de produto fechada.")
                except Exception: pass
            if pagina_lista and not pagina_lista.is_closed():
                try: pagina_lista.close(); print("ℹ️ Página de listagem fechada.")
                except Exception: pass
            if contexto:
                try: contexto.close(); print("✅ Contexto fechado.")
                except Exception: pass
            if navegador:
                try: navegador.close(); print("✅ Navegador fechado.")
                except Exception: pass

    # Salvamento CSV Final (Idêntico)
    if lista_dados_finais:
        print(f"\n⏳ Salvando {len(lista_dados_finais)} produtos...")
        try:
            colunas_ordenadas = ["nome_produto", "preco_atual", "descricao", "cor", "tamanhos_disponiveis", "objetivo", "url_site", "url_imagem", "loja", "categoria", "genero_destinado"]; df = pd.DataFrame(lista_dados_finais)
            for col in colunas_ordenadas:
                if col not in df.columns: df[col] = "Não Coletado"
            df = df[colunas_ordenadas]; os.makedirs(os.path.dirname(CAMINHO_CSV), exist_ok=True); df.to_csv(CAMINHO_CSV, index=False, encoding='utf-8-sig'); print(f"✅ Dados salvos: {CAMINHO_CSV}")
        except Exception as e_csv:
            print(f"❌ Erro ao salvar CSV: {e_csv}"); traceback.print_exc()
            try: backup_path = CAMINHO_CSV.replace(".csv", "_backup_bruto.csv"); pd.DataFrame(lista_dados_finais).to_csv(backup_path, index=False, encoding='utf-8-sig'); print(f"ℹ️ Backup bruto salvo em: {backup_path}");
            except Exception as e_backup: print(f"❌ Falha ao salvar backup: {e_backup}")
    else: print("\n⚠️ Nenhum dado coletado para salvar.")
    print(f"\n--- Scraping Artwalk (v31.full_scrape_loop) Finalizado --- ({len(lista_dados_finais)} produtos)")

# --- Execução ---
if __name__ == "__main__":
    scraping_artwalk()