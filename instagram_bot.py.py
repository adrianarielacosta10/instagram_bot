import os
import time
import random
import json
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

class InstagramFollowBot:
    def __init__(self, username, password):
        self.username = username
        self.password = password

        # Configuración del navegador
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-notifications')
        options.add_argument('--lang=es')
        #options.add_argument('--headless')  # Modo headless para evitar que abra la ventana (puedes quitarlo si necesitas ver)
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 15)
        
        # Estado y archivos
        self.followed_users = set()
        self.follows_today = 0
        self.state_file = 'bot_state.json'
        self.followed_users_file = 'followed_users.json'
        self.load_state()
        self.load_followed_users()

    def load_state(self):
        """Carga el estado del bot desde un archivo JSON."""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as file:
                self.state = json.load(file)
        else:
            self.state = {'last_follow_date': '', 'follows_today': 0}

    def load_followed_users(self):
        """Carga la lista de usuarios seguidos desde un archivo JSON."""
        if os.path.exists(self.followed_users_file):
            with open(self.followed_users_file, 'r') as file:
                self.followed_users = set(json.load(file))

    def save_state(self):
        """Guarda el estado del bot en un archivo JSON."""
        with open(self.state_file, 'w') as file:
            json.dump(self.state, file)

    def save_followed_users(self):
        """Guarda la lista de usuarios seguidos en un archivo JSON."""
        with open(self.followed_users_file, 'w') as file:
            json.dump(list(self.followed_users), file)

    def log_activity(self, message):
        """Registra las actividades del bot en un archivo de texto."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open('instagram_bot_log.txt', 'a') as file:
            file.write(f"[{timestamp}] {message}\n")
        print(f"[{timestamp}] {message}")

    def login(self):
        """Inicia sesión en Instagram."""
        try:
            self.log_activity("Iniciando sesión en Instagram...")
            self.driver.get('https://www.instagram.com/accounts/login/')
            username_input = self.wait.until(EC.presence_of_element_located((By.NAME, "username")))
            password_input = self.driver.find_element(By.NAME, "password")
            username_input.send_keys(self.username)
            password_input.send_keys(self.password)
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()

            # Esperar hasta que cargue la página principal
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "svg[aria-label='Inicio']")))
            self.log_activity("Login exitoso.")
        except TimeoutException:
            self.log_activity("Error: Login tomó demasiado tiempo.")
            raise
        except Exception as e:
            self.log_activity(f"Error durante el login: {str(e)}")
            raise

    def get_users_from_html(self, html_path):
        """Extraer usuarios del archivo HTML con validaciones y manejo robusto de errores."""
        try:
            # Verificar si el archivo existe
            if not os.path.exists(html_path):
                self.log_activity(f"Archivo HTML no encontrado: {html_path}")
                return []

            # Leer el contenido del archivo
            with open(html_path, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')

            # Buscar todos los enlaces en el HTML
            links = soup.find_all('a', href=True)
            users = []

            # Filtrar enlaces que son perfiles de Instagram
            for link in links:
                href = link['href']
                if href.startswith('https://www.instagram.com/') and '/p/' not in href:
                    users.append(href)

            # Eliminar duplicados y devolver los usuarios
            users = list(set(users))
            self.log_activity(f"Se encontraron {len(users)} usuarios en el archivo HTML.")
            return users

        except Exception as e:
            self.log_activity(f"Error al procesar el archivo HTML: {str(e)}")
            return []

    def follow_user(self, user_url):
        """Sigue a un usuario con selectores actualizados"""
        try:
            self.driver.get(user_url)
            # Esperar y verificar si el botón de seguir está presente
            follow_button = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Seguir') or contains(text(), 'Follow')]"))
                )
            if "seguir" not in follow_button.text.lower():  # Confirmar que es el botón correcto
                self.log_activity(f"Usuario ya seguido o botón no disponible: {user_url}")
                return
            follow_button.click()
            self.log_activity(f"Usuario seguido exitosamente: {user_url}")
            self.followed_users.add(user_url)
            self.follows_today += 1
            self.save_followed_users()
        except Exception as e:
            self.log_activity(f"Error al seguir al usuario {user_url}: {str(e)}")

    def start_following_process(self, html_path):
        """Inicia el proceso de seguir usuarios desde un archivo HTML."""
        users = self.get_users_from_html(html_path)
        if not users:
            self.log_activity("No se encontraron usuarios en el archivo HTML.")
            return

        for user_url in users:
            if user_url not in self.followed_users:
                self.follow_user(user_url)
                time.sleep(random.uniform(30, 60))  # Pausa aleatoria entre acciones

    def cleanup(self):
        """Limpieza y cierre del navegador."""
        try:
            self.driver.quit()
        except Exception as e:
            self.log_activity(f"Error al cerrar el navegador: {str(e)}")


def main():
    # Cargar variables de entorno
    load_dotenv()
    USERNAME = os.getenv('INSTAGRAM_USERNAME')
    PASSWORD = os.getenv('INSTAGRAM_PASSWORD')

    # Ruta del archivo HTML
    HTML_PATH = r"D:\Users\Usuario\Pictures\BENDITO\Marketing\instagram_users_with_links.html"


    bot = InstagramFollowBot(USERNAME, PASSWORD)
    try:
        bot.login()
        bot.start_following_process(HTML_PATH)
    except Exception as e:
        print(f"Error en el programa: {str(e)}")
    finally:
        bot.cleanup()


if __name__ == "__main__":
    main()
