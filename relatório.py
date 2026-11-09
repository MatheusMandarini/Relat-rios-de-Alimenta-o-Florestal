"""Automatiza a exportação mensal do relatório de alimentação florestal.

Eu deixei o processo dividido em pequenas funções para ficar mais fácil de
entender, ajustar e descobrir em qual etapa algo deu errado.
"""

import os
import time
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


load_dotenv()

LOGIN_URL = "https://spa.checklistfacil.com.br/login?lang=pt-br"
QUEUES_URL = "https://app.checklistfacil.com.br/settings/queues"
FILTER_NAME = "Alimentos"
POLL_INTERVAL = int(os.getenv("QUEUE_POLL_INTERVAL", "10"))
POLL_TIMEOUT = int(os.getenv("QUEUE_POLL_TIMEOUT", "600"))
DOWNLOAD_TIMEOUT = int(os.getenv("DOWNLOAD_TIMEOUT", "120"))
DOWNLOAD_DIR = Path(os.getenv("DOWNLOAD_DIR", "downloads")).resolve()
EXPORT_ROOT = Path(os.getenv("BASE_DIR", "exports")).resolve()
HEADLESS = os.getenv("HEADLESS", "1") == "1"

DOWNLOAD_BUTTON_CSS = "a.js-row-download-button"
EXPORT_BUTTON_XPATH = (
    "//button[.//span[contains(@class, 'mdc-button__label') "
    "and normalize-space()='Exportar']]"
)


def wait_for(driver, condition, timeout=15):
    """Espero um elemento ou condição ficar pronta antes de continuar."""
    return WebDriverWait(driver, timeout).until(condition)


def js_click(driver, element):
    """Clico pelo JavaScript quando o Selenium não consegue clicar normalmente."""
    driver.execute_script("arguments[0].click();", element)


def safe_quit(driver):
    """Tento fechar o navegador sem esconder o erro principal do processo."""
    try:
        driver.quit()
    except Exception as error:
        print(f"AVISO: falha ao fechar o Chrome: {error}")


def create_driver():
    """Configuro o Chrome e deixo os downloads irem para a pasta do projeto."""
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    options = webdriver.ChromeOptions()
    options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": str(DOWNLOAD_DIR),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        },
    )
    if HEADLESS:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
    return webdriver.Chrome(options=options)


def login(driver):
    """Faço o login usando as credenciais disponíveis no ambiente do sistema."""
    login_name = os.getenv("LOGIN_NAME")
    login_password = os.getenv("LOGIN_PASSWORD")
    if not login_name or not login_password:
        raise RuntimeError(
            "Defina LOGIN_NAME e LOGIN_PASSWORD nas variáveis de ambiente."
        )

    driver.get(LOGIN_URL)
    user_field = wait_for(
        driver, EC.visibility_of_element_located((By.NAME, "user-name"))
    )
    user_field.clear()
    user_field.send_keys(login_name)
    wait_for(
        driver,
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit'] .submit__label")),
    ).click()

    password_field = wait_for(
        driver, EC.visibility_of_element_located((By.NAME, "user-password"))
    )
    password_field.clear()
    password_field.send_keys(login_password)
    js_click(
        driver,
        wait_for(driver, EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))),
    )


def set_date_field(field, value):
    """Limpo um campo de data, preencho o novo valor e confiro se ele ficou certo."""
    field.click()
    field.send_keys(Keys.CONTROL, "a")
    field.send_keys(Keys.BACKSPACE)
    field.send_keys(value)
    field.send_keys(Keys.TAB)
    time.sleep(0.5)
    if field.get_attribute("value") != value:
        raise RuntimeError(
            f"Não consegui preencher a data {value}; "
            f"valor atual: {field.get_attribute('value')!r}"
        )


def _visible_date_fields(driver):
    """Retorno somente os campos de data que realmente estão visíveis na tela."""
    fields = []
    for field in driver.find_elements(
        By.CSS_SELECTOR, "input.mdc-text-field__input[maxlength='10']"
    ):
        if field.is_displayed():
            fields.append(field)
    return fields if len(fields) >= 2 else False


def apply_filter(driver, anchor):
    """Encontro o botão de filtro ligado ao campo e aplico o período escolhido."""
    filter_button = wait_for(
        driver,
        lambda d: d.execute_script(
            """
            let node = arguments[0].parentElement;
            while (node) {
                const button = [...node.querySelectorAll('button')]
                    .find(item => (item.classList.contains('submit-filter-button') ||
                                   item.textContent.trim() === 'Filtrar') &&
                                  item.offsetParent !== null);
                if (button) return button;
                node = node.parentElement;
            }
            return null;
            """,
            anchor,
        ),
        20,
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", filter_button)
    try:
        ActionChains(driver).move_to_element(filter_button).click().perform()
    except Exception:
        js_click(driver, filter_button)
    time.sleep(5)


def select_filter_and_period(driver, start_date, end_date):
    """Seleciono o filtro salvo e informo o primeiro e o último dia do mês."""
    filters_button = wait_for(
        driver,
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[contains(@class, 'my-filters-button') "
                "and contains(normalize-space(.), 'Meus filtros')]",
            )
        ),
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", filters_button)
    js_click(driver, filters_button)
    filter_item = wait_for(
        driver,
        EC.element_to_be_clickable(
            (
                By.XPATH,
                f"//li[@role='radio'][.//label[normalize-space()='{FILTER_NAME}']]",
            )
        ),
    )
    js_click(driver, filter_item)
    wait_for(
        driver,
        EC.element_to_be_clickable((By.XPATH, "//button[.//span[normalize-space()='Carregar']]")),
    ).click()
    time.sleep(2)

    fields = wait_for(driver, _visible_date_fields)
    start_field, end_field = fields[:2]
    set_date_field(start_field, start_date.strftime("%d/%m/%Y"))
    set_date_field(end_field, end_date.strftime("%d/%m/%Y"))
    apply_filter(driver, end_field)


def open_filtered_listing(driver, start_date, end_date):
    """Abro a listagem de avaliações e preparo o filtro do relatório mensal."""
    wait_for(
        driver,
        EC.element_to_be_clickable((By.XPATH, "//a[@class='menu-link mdc-list-item']")),
    ).click()
    time.sleep(2)
    select_filter_and_period(driver, start_date, end_date)


def has_results(driver):
    """Confiro se a busca trouxe registros que podem ser exportados."""
    try:
        wait_for(
            driver,
            lambda d: bool(
                d.find_elements(By.CSS_SELECTOR, "input.js-check-all#checkbox-1")
            ),
            20,
        )
    except TimeoutException:
        return False
    return True


def set_page_size_200(driver):
    """Tento mostrar até 200 registros para exportar tudo de uma vez."""
    try:
        dropdown = wait_for(
            driver,
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "span[data-dropdown-target='#pagination-dropdown']")
            ),
            20,
        )
        js_click(driver, dropdown)
        option = wait_for(
            driver,
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//a[contains(@class, 'mdc-list-item__text') and normalize-space()='200']",
                )
            ),
            10,
        )
        js_click(driver, option)
        time.sleep(3)
    except TimeoutException:
        print("AVISO: paginação de 200 não encontrada; usando a paginação atual.")


def _visible_export_button(driver):
    """Encontro o botão Exportar que estiver visível e habilitado."""
    for button in driver.find_elements(By.XPATH, EXPORT_BUTTON_XPATH):
        try:
            if button.is_displayed() and button.is_enabled():
                return button
        except StaleElementReferenceException:
            continue
    return False


def select_xlsx_layout(driver):
    """Escolho o formato XLSX em que cada item fica separado em uma coluna."""
    def visible_select_box(d):
        """Localizo o seletor de layout que estiver aparecendo na tela."""
        for element in d.find_elements(By.CSS_SELECTOR, "div.js-select-full-field"):
            try:
                if element.is_displayed():
                    return element
            except StaleElementReferenceException:
                continue
        return False

    try:
        select_box = wait_for(driver, visible_select_box, 8)
    except TimeoutException:
        print(
            "AVISO: o seletor de layout XLSX não foi exibido; "
            "seguindo com o formato padrão do Checklist Fácil."
        )
        return

    toggle = select_box.find_element(By.CSS_SELECTOR, "button.options-toggle")
    js_click(driver, toggle)
    try:
        option = wait_for(
            driver,
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "li[data-value='evaluation_column_items']")
            ),
            10,
        )
    except TimeoutException as error:
        print(
            "AVISO: a opção 'Itens em colunas' não está disponível nesta exportação; "
            "seguindo com o formato exibido pelo Checklist Fácil."
        )
        return
    js_click(driver, option)
    time.sleep(0.5)
    selected = select_box.find_element(By.CSS_SELECTOR, "input.js-form-input")
    if selected.get_attribute("value") != "evaluation_column_items":
        raise RuntimeError("Não consegui selecionar o formato 'Itens em colunas'.")


def read_queue_rows(driver):
    """Leio as linhas da fila e devolvo o ID, o botão e o texto de cada uma."""
    rows = []
    for button in driver.find_elements(By.CSS_SELECTOR, DOWNLOAD_BUTTON_CSS):
        raw_id = button.get_attribute("data-row-id")
        if raw_id and raw_id.isdigit():
            row = button.find_element(By.XPATH, "./ancestor::tr[1]")
            rows.append((int(raw_id), button, row.text))
    return rows


def latest_queue_id(driver):
    """Guardo o último ID da fila antes de gerar um novo relatório."""
    original_window = driver.current_window_handle
    driver.switch_to.new_window("tab")
    try:
        driver.get(QUEUES_URL)
        try:
            wait_for(
                driver,
                EC.presence_of_element_located((By.CSS_SELECTOR, DOWNLOAD_BUTTON_CSS)),
                15,
            )
        except TimeoutException:
            return 0
        return max((row[0] for row in read_queue_rows(driver)), default=0)
    finally:
        driver.close()
        driver.switch_to.window(original_window)


def open_queue_history(driver):
    """Abro o histórico de exportações, que pode aparecer em uma nova aba."""
    windows_before = set(driver.window_handles)
    history_link = wait_for(
        driver,
        EC.presence_of_element_located((By.CSS_SELECTOR, "a[href$='/settings/queues']")),
    )
    js_click(driver, history_link)
    wait_for(
        driver,
        lambda d: len(d.window_handles) > len(windows_before)
        or "/settings/queues" in d.current_url,
        15,
    )
    new_windows = [window for window in driver.window_handles if window not in windows_before]
    if new_windows:
        driver.switch_to.window(new_windows[0])


def wait_for_new_export(driver, baseline_id):
    """Espero a nova exportação terminar e devolvo o botão do arquivo pronto."""
    deadline = time.monotonic() + POLL_TIMEOUT
    while time.monotonic() < deadline:
        rows = [row for row in read_queue_rows(driver) if row[0] > baseline_id]
        if rows:
            row_id, button, row_text = max(rows, key=lambda row: row[0])
            status = row_text.lower()
            if "sucesso" in status:
                print(f"Relatório pronto (linha {row_id}).")
                return button
            if "erro" in status or "falha" in status:
                raise RuntimeError(f"A exportação falhou no Checklist Fácil: {row_text!r}")
        time.sleep(POLL_INTERVAL)
        driver.refresh()
    raise TimeoutError(f"O relatório não ficou pronto em {POLL_TIMEOUT} segundos.")


def download_from_row(driver, button):
    """Baixo o arquivo e espero o Chrome terminar antes de devolvê-lo."""
    files_before = {path.name for path in DOWNLOAD_DIR.iterdir() if path.is_file()}
    js_click(driver, button)
    deadline = time.monotonic() + DOWNLOAD_TIMEOUT
    while time.monotonic() < deadline:
        in_progress = list(DOWNLOAD_DIR.glob("*.crdownload"))
        new_files = [
            path
            for path in DOWNLOAD_DIR.iterdir()
            if path.is_file()
            and path.name not in files_before
            and path.suffix.lower() not in {".crdownload", ".tmp"}
        ]
        if new_files and not in_progress:
            return max(new_files, key=lambda path: path.stat().st_mtime)
        time.sleep(1)
    raise TimeoutError(f"O download não terminou em {DOWNLOAD_TIMEOUT} segundos.")


def export_report(driver):
    """Seleciono os registros, gero o XLSX e faço o download do resultado."""
    set_page_size_200(driver)
    check_all = wait_for(
        driver,
        EC.presence_of_element_located((By.CSS_SELECTOR, "input.js-check-all#checkbox-1")),
    )
    js_click(driver, check_all)
    js_click(driver, wait_for(driver, EC.element_to_be_clickable((By.ID, "button-bulk-export"))))
    js_click(
        driver,
        wait_for(
            driver,
            EC.presence_of_element_located(
                (By.XPATH, "//label[normalize-space()='XLSX']")
            ),
        ),
    )
    select_xlsx_layout(driver)
    time.sleep(1)
    export_button = wait_for(driver, _visible_export_button, 15)
    baseline_id = latest_queue_id(driver)
    js_click(driver, export_button)
    open_queue_history(driver)
    return download_from_row(driver, wait_for_new_export(driver, baseline_id))


def monthly_destination(day):
    """Monto o nome do arquivo usando o mês e o ano do relatório."""
    return EXPORT_ROOT / f"{day:%m-%Y}.xlsx"


def save_monthly_report(downloaded_path, day):
    """Substituo o arquivo mensal antigo pelo relatório que acabou de baixar."""
    destination = monthly_destination(day)
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(downloaded_path, destination)
    print(f"Relatório atualizado: {destination}")
    return destination


def main():
    """Executo o processo completo para o mês atual."""
    today = date.today()
    start_date = today.replace(day=1)
    driver = create_driver()
    try:
        login(driver)
        open_filtered_listing(driver, start_date, today)
        if not has_results(driver):
            print(
                f"Nenhum registro de {start_date:%d/%m/%Y} a {today:%d/%m/%Y}; "
                "nenhum arquivo foi substituído."
            )
            return
        save_monthly_report(export_report(driver), today)
    finally:
        safe_quit(driver)


if __name__ == "__main__":
    main()